from mcp.server.fastmcp import FastMCP

from .db import Base, engine
from .services import queries

Base.metadata.create_all(engine)
mcp = FastMCP("finpilot")


@mcp.tool()
def reconciliation_summary() -> str:
    """Counts and total differences of reconciliation results grouped by status."""
    return queries.recon_summary()


@mcp.tool()
def list_discrepancies(status: str = "") -> str:
    """List reconciliation items that are not fully matched. Optional status filter:
    probable, amount_mismatch, unpaid, unexplained, possible_duplicate, matched."""
    return queries.list_discrepancies(status)


@mcp.tool()
def explain_invoice(invoice_ref: str) -> str:
    """Reconciliation result and plain-English explanation for one invoice number, e.g. INV-1002."""
    return queries.explain_invoice(invoice_ref)


@mcp.tool()
def search_transactions(text: str = "", source: str = "", start_date: str = "", end_date: str = "") -> str:
    """Search transactions by text, source (bank|invoice|payment) and date range (YYYY-MM-DD).
    Returns matching rows and their exact total."""
    return queries.search_transactions(text=text, source=source, start_date=start_date, end_date=end_date)


if __name__ == "__main__":
    mcp.run()  # stdio transport