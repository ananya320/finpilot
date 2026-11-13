import json
from typing import Annotated, TypedDict, Optional
from datetime import date

from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from ..config import settings
from ..db import SessionLocal
from ..models import Transaction, Match
from . import vectorstore
from .reconcile import summary

SYSTEM = """You are FinPilot, a financial operations assistant.
RULES:
- Never calculate, estimate or recall numbers yourself. Always call a tool and quote its results exactly.
- If a tool returns nothing, say there is no matching data. Never guess or fill gaps.
- Explain reconciliation mismatches using the 'reason' field from the tools, then suggest a next step
  (e.g. contact vendor, check for a credit note, confirm a duplicate).
- Rows with needs_review=true were not verified against the source; mention that when relevant.
- Be concise. State amounts with their dates and references."""

def _j(obj):
    return json.dumps(obj, default=str)

@tool
def recon_summary() -> str:
    """Counts and total differences of reconciliation results grouped by status."""
    with SessionLocal() as db:
        return _j(summary(db))

@tool
def list_discrepancies(status: str = "") -> str:
    """List reconciliation items that are not fully matched. Optional status filter:
    probable, amount_mismatch, unpaid, unexplained, possible_duplicate, matched."""
    with SessionLocal() as db:
        q = db.query(Match)
        q = q.filter(Match.status == status) if status else q.filter(Match.status != "matched")
        return _j([dict(status=m.status, difference=m.difference, reason=m.reason) for m in q.limit(50)])

@tool
def search_transactions(text: str = "", source: str = "", min_amount: Optional[float] = None,
                        max_amount: Optional[float] = None, start_date: str = "", end_date: str = "") -> str:
    """Search transactions. text matches description/reference/counterparty. source: bank|invoice|payment.
    Amounts compare on absolute value. Dates are YYYY-MM-DD. Returns rows plus their exact total."""
    with SessionLocal() as db:
        q = db.query(Transaction)
        if text:
            like = f"%{text}%"
            q = q.filter(Transaction.description.ilike(like) | Transaction.reference.ilike(like)
                         | Transaction.counterparty.ilike(like))
        if source: q = q.filter(Transaction.source == source)
        if start_date: q = q.filter(Transaction.txn_date >= date.fromisoformat(start_date))
        if end_date: q = q.filter(Transaction.txn_date <= date.fromisoformat(end_date))
        rows = [t for t in q.order_by(Transaction.txn_date).limit(200)
                if (min_amount is None or abs(t.amount) >= min_amount)
                and (max_amount is None or abs(t.amount) <= max_amount)]
        total = sum(t.amount for t in rows)
        return _j({"count": len(rows), "total": total,
                   "rows": [dict(date=t.txn_date, source=t.source, description=t.description,
                                 reference=t.reference, amount=t.amount, needs_review=t.needs_review)
                            for t in rows[:30]]})

@tool
def explain_invoice(invoice_ref: str) -> str:
    """Get the reconciliation result and explanation for a specific invoice number."""
    with SessionLocal() as db:
        inv = db.query(Transaction).filter(Transaction.source == "invoice",
                                           Transaction.reference.ilike(invoice_ref)).first()
        if not inv:
            return _j({"error": f"No invoice {invoice_ref} found."})
        m = db.query(Match).filter(Match.invoice_id == inv.id).first()
        return _j({"invoice": dict(ref=inv.reference, amount=inv.amount, date=inv.txn_date,
                                   vendor=inv.counterparty),
                   "result": dict(status=m.status, difference=m.difference, reason=m.reason) if m
                             else "Reconciliation has not been run yet."})

@tool
def search_documents(query: str) -> str:
    """Semantic search over the raw text of uploaded documents (terms, notes, free text)."""
    try:
        return _j(vectorstore.search(query))
    except Exception as e:
        return _j({"error": str(e)})

TOOLS = [recon_summary, list_discrepancies, search_transactions, explain_invoice, search_documents]

class State(TypedDict):
    messages: Annotated[list, add_messages]

def build_graph():
    llm = ChatGoogleGenerativeAI(model=settings.gemini_model, google_api_key=settings.google_api_key,
                                 temperature=0).bind_tools(TOOLS)

    def agent(state: State):
        return {"messages": [llm.invoke([SystemMessage(content=SYSTEM)] + state["messages"])]}

    g = StateGraph(State)
    g.add_node("agent", agent)
    g.add_node("tools", ToolNode(TOOLS))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", tools_condition)   # tool call -> "tools", otherwise END
    g.add_edge("tools", "agent")
    return g.compile(checkpointer=MemorySaver())        # memory per session_id

graph = build_graph()

def ask(message: str, session_id: str) -> str:
    out = graph.invoke({"messages": [("user", message)]},
                       config={"configurable": {"thread_id": session_id}, "recursion_limit": 12})
    content = out["messages"][-1].content
    if isinstance(content, list):   # Gemini sometimes returns content parts
        content = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return content