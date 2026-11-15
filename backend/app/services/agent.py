import re
from typing import Literal, Optional

from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel

from ..config import settings
from . import queries


def _llm():
    # max_retries lets short Google overloads (503) pass without breaking the chat
    return ChatGoogleGenerativeAI(model=settings.gemini_model, google_api_key=settings.google_api_key,
                                  temperature=0, max_retries=5, timeout=60)


def _text(content) -> str:
    if isinstance(content, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return content


# ---------- tools ----------
def _bid(config: RunnableConfig) -> int:
    """The business id is set by the server for the logged-in user, never by the model."""
    return int(config["configurable"]["business_id"])


@tool
def recon_summary(config: RunnableConfig) -> str:
    """Counts and total differences of reconciliation results grouped by status."""
    return queries.recon_summary(_bid(config))


@tool
def list_discrepancies(config: RunnableConfig, status: str = "") -> str:
    """List reconciliation items that are not fully matched. Optional status filter:
    probable, amount_mismatch, unpaid, unexplained, possible_duplicate, matched."""
    return queries.list_discrepancies(_bid(config), status)


@tool
def explain_invoice(invoice_ref: str, config: RunnableConfig) -> str:
    """Get the reconciliation result and explanation for a specific invoice number."""
    return queries.explain_invoice(_bid(config), invoice_ref)


@tool
def search_transactions(config: RunnableConfig, text: str = "", source: str = "",
                        min_amount: Optional[float] = None, max_amount: Optional[float] = None,
                        start_date: str = "", end_date: str = "") -> str:
    """Search transactions. text matches description/reference/counterparty. source: bank|invoice|payment.
    Amounts compare on absolute value. Dates are YYYY-MM-DD. Returns rows plus their exact total."""
    return queries.search_transactions(_bid(config), text, source, min_amount, max_amount,
                                       start_date, end_date)


@tool
def search_documents(query: str, config: RunnableConfig) -> str:
    """Semantic search over the raw text of uploaded documents (terms, notes, free text)."""
    return queries.search_documents(_bid(config), query)


# ---------- specialist agents ----------
COMMON = ("Never calculate, estimate or recall numbers yourself. Always call a tool and quote its results "
          "exactly. If a tool returns nothing, say there is no matching data. Be concise.")


def make_agent(tools, system: str):
    llm = _llm().bind_tools(tools)

    def call(state: MessagesState):
        return {"messages": [llm.invoke([SystemMessage(content=system)] + state["messages"])]}

    g = StateGraph(MessagesState)
    g.add_node("agent", call)
    g.add_node("tools", ToolNode(tools))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", tools_condition)
    g.add_edge("tools", "agent")
    return g.compile()


# ---------- supervisor ----------
class State(MessagesState):
    route: str


class Route(BaseModel):
    route: Literal["reconciliation", "transactions", "documents", "other"]


ROUTER_PROMPT = ("Classify the user's latest question.\n"
                 "reconciliation = invoice status, mismatches, unpaid, duplicates, explanations.\n"
                 "transactions = searching or totalling transactions by date, amount, vendor.\n"
                 "documents = questions about text inside uploaded files (terms, notes).\n"
                 "other = anything unrelated to the user's financial data.")


def router(state: State):
    r = _llm().with_structured_output(Route).invoke(
        [SystemMessage(content=ROUTER_PROMPT)] + state["messages"][-4:])
    return {"route": r.route}


def out_of_scope(state: State):
    return {"messages": [AIMessage(content="I can only help with your uploaded transactions, "
                                           "invoices and reconciliation results.")]}


NUM = re.compile(r"\d[\d,]*\.?\d*")


def verifier(state: State):
    """Plain Python check: every number in the answer must appear in a tool result."""
    answer = _text(state["messages"][-1].content)
    tool_text = " ".join(str(m.content) for m in state["messages"] if isinstance(m, ToolMessage))
    tool_text = tool_text.replace(",", "")
    bad = []
    for n in NUM.findall(answer.replace(",", "")):
        n = n.rstrip(".")
        if len(n) >= 3 and n not in tool_text:
            bad.append(n)
    if bad:
        warn = f"\n\n⚠ Could not verify these figures against the database: {', '.join(sorted(set(bad)))}"
        return {"messages": [AIMessage(content=answer + warn)]}
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("router", router)
    g.add_node("recon_agent", make_agent(
        [recon_summary, list_discrepancies, explain_invoice],
        "You are the reconciliation specialist. Explain mismatches using the 'reason' field from tools, "
        "then suggest a next step (contact vendor, check for a credit note, confirm a duplicate). " + COMMON))
    g.add_node("txn_agent", make_agent(
        [search_transactions],
        "You are the transaction search specialist. Rows with needs_review=true were not verified "
        "against the source; mention that when relevant. " + COMMON))
    g.add_node("docs_agent", make_agent(
        [search_documents],
        "You answer questions from uploaded document text. Cite the filename. " + COMMON))
    g.add_node("out_of_scope", out_of_scope)
    g.add_node("verifier", verifier)

    g.add_edge(START, "router")
    g.add_conditional_edges("router", lambda s: s["route"], {
        "reconciliation": "recon_agent", "transactions": "txn_agent",
        "documents": "docs_agent", "other": "out_of_scope"})
    for n in ["recon_agent", "txn_agent", "docs_agent", "out_of_scope"]:
        g.add_edge(n, "verifier")
    g.add_edge("verifier", END)
    return g.compile(checkpointer=MemorySaver())


graph = build_graph()


def ask(message: str, thread_id: str, business_id: int) -> str:
    out = graph.invoke({"messages": [("user", message)]},
                       config={"configurable": {"thread_id": thread_id, "business_id": business_id},
                               "recursion_limit": 25})
    return _text(out["messages"][-1].content)