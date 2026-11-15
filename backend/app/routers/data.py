from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_business
from ..models import Transaction, Match, Business
from ..services.reconcile import run_reconciliation, summary

router = APIRouter()


def tx_dict(t):
    return dict(id=t.id, date=str(t.txn_date), source=t.source, description=t.description,
                reference=t.reference, counterparty=t.counterparty, amount=str(t.amount),
                needs_review=t.needs_review)


@router.get("/transactions")
def transactions(biz: Business = Depends(current_business), db: Session = Depends(get_db)):
    rows = (db.query(Transaction).filter(Transaction.business_id == biz.id)
              .order_by(Transaction.txn_date).all())
    return [tx_dict(t) for t in rows]


@router.post("/reconciliation/run")
def run(biz: Business = Depends(current_business), db: Session = Depends(get_db)):
    run_reconciliation(db, biz.id)
    return {"summary": summary(db, biz.id)}


@router.get("/reconciliation")
def get_recon(biz: Business = Depends(current_business), db: Session = Depends(get_db)):
    txs = {t.id: t for t in db.query(Transaction).filter(Transaction.business_id == biz.id)}

    def label(i):
        t = txs.get(i)
        return f"{t.reference or t.description} ({t.amount}, {t.txn_date})" if t else ""

    items = [dict(id=m.id, status=m.status, invoice=label(m.invoice_id), payment=label(m.payment_id),
                  difference=str(m.difference), reason=m.reason)
             for m in db.query(Match).filter(Match.business_id == biz.id).order_by(Match.status).all()]
    return {"summary": summary(db, biz.id), "items": items}