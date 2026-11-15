import json
from datetime import date
from typing import Optional

from ..db import SessionLocal
from ..models import Transaction, Match
from . import vectorstore
from .reconcile import summary


def _j(obj):
    return json.dumps(obj, default=str)


def recon_summary(business_id: int) -> str:
    with SessionLocal() as db:
        return _j(summary(db, business_id))


def list_discrepancies(business_id: int, status: str = "") -> str:
    with SessionLocal() as db:
        q = db.query(Match).filter(Match.business_id == business_id)
        q = q.filter(Match.status == status) if status else q.filter(Match.status != "matched")
        return _j([dict(status=m.status, difference=m.difference, reason=m.reason) for m in q.limit(50)])


def search_transactions(business_id: int, text: str = "", source: str = "",
                        min_amount: Optional[float] = None, max_amount: Optional[float] = None,
                        start_date: str = "", end_date: str = "") -> str:
    with SessionLocal() as db:
        q = db.query(Transaction).filter(Transaction.business_id == business_id)
        if text:
            like = f"%{text}%"
            q = q.filter(Transaction.description.ilike(like) | Transaction.reference.ilike(like)
                         | Transaction.counterparty.ilike(like))
        if source:
            q = q.filter(Transaction.source == source)
        if start_date:
            q = q.filter(Transaction.txn_date >= date.fromisoformat(start_date))
        if end_date:
            q = q.filter(Transaction.txn_date <= date.fromisoformat(end_date))
        rows = [t for t in q.order_by(Transaction.txn_date).limit(200)
                if (min_amount is None or abs(t.amount) >= min_amount)
                and (max_amount is None or abs(t.amount) <= max_amount)]
        total = sum(t.amount for t in rows)
        return _j({"count": len(rows), "total": total,
                   "rows": [dict(date=t.txn_date, source=t.source, description=t.description,
                                 reference=t.reference, amount=t.amount, needs_review=t.needs_review)
                            for t in rows[:30]]})


def explain_invoice(business_id: int, invoice_ref: str) -> str:
    with SessionLocal() as db:
        inv = (db.query(Transaction)
                 .filter(Transaction.business_id == business_id, Transaction.source == "invoice",
                         Transaction.reference.ilike(invoice_ref)).first())
        if not inv:
            return _j({"error": f"No invoice {invoice_ref} found."})
        m = (db.query(Match)
               .filter(Match.business_id == business_id, Match.invoice_id == inv.id).first())
        return _j({"invoice": dict(ref=inv.reference, amount=inv.amount, date=inv.txn_date,
                                   vendor=inv.counterparty),
                   "result": dict(status=m.status, difference=m.difference, reason=m.reason) if m
                             else "Reconciliation has not been run yet."})


def search_documents(business_id: int, query: str) -> str:
    try:
        return _j(vectorstore.search(query, business_id))
    except Exception as e:
        return _j({"error": str(e)})