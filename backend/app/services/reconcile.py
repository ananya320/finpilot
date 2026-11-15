from difflib import SequenceMatcher
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..models import Transaction, Match

WINDOW_DAYS = 30


def _score(inv, pay):
    text = f"{pay.description} {pay.reference or ''}".lower()
    ref_hit = bool(inv.reference) and inv.reference.lower() in text
    exact = abs(pay.amount) == inv.amount
    days = (pay.txn_date - inv.txn_date).days
    in_window = -3 <= days <= WINDOW_DAYS
    v = (inv.counterparty or "").lower()
    vendor_sim = 0.0
    if v:
        vendor_sim = 1.0 if v in text else SequenceMatcher(None, v, pay.description.lower()).ratio()
    score = 0.40 * ref_hit + 0.35 * exact + 0.15 * in_window + 0.10 * vendor_sim
    return score, ref_hit, exact, days, in_window


def run_reconciliation(db: Session, business_id: int):
    db.query(Match).filter(Match.business_id == business_id).delete()
    invoices = (db.query(Transaction)
                  .filter(Transaction.business_id == business_id, Transaction.source == "invoice").all())
    payments = (db.query(Transaction)
                  .filter(Transaction.business_id == business_id,
                          Transaction.source.in_(["bank", "payment"]), Transaction.amount < 0)
                  .order_by(Transaction.id).all())

    pairs = []
    for inv in invoices:
        for pay in payments:
            score, ref_hit, exact, days, in_window = _score(inv, pay)
            if ref_hit or (exact and in_window):
                pairs.append((score, inv, pay, ref_hit, exact, days))
    pairs.sort(key=lambda p: -p[0])

    used_inv, used_pay = set(), set()
    for score, inv, pay, ref_hit, exact, days in pairs:
        if inv.id in used_inv or pay.id in used_pay:
            continue
        used_inv.add(inv.id)
        used_pay.add(pay.id)
        paid = abs(pay.amount)
        diff = inv.amount - paid
        label = inv.reference or f"#{inv.id}"
        if exact and ref_hit:
            status = "matched"
            reason = (f"Invoice {label} ({inv.amount}) matches the payment of {paid} on {pay.txn_date}: "
                      f"same amount and the invoice number appears in the payment description.")
        elif exact:
            status = "probable"
            reason = (f"Payment of {paid} on {pay.txn_date} equals invoice {label}, paid {days} days after the "
                      f"invoice date, but no invoice number was found in the payment. Please confirm.")
        else:
            status = "amount_mismatch"
            word = "underpaid" if diff > 0 else "overpaid"
            reason = (f"Payment on {pay.txn_date} references invoice {label}, but {paid} was paid against "
                      f"{inv.amount} invoiced: {word} by {abs(diff)}.")
        db.add(Match(business_id=business_id, invoice_id=inv.id, payment_id=pay.id, status=status,
                     score=score, difference=diff, reason=reason))

    for inv in invoices:
        if inv.id not in used_inv:
            db.add(Match(business_id=business_id, invoice_id=inv.id, status="unpaid",
                         difference=inv.amount,
                         reason=f"No payment found for invoice {inv.reference or inv.id} "
                                f"({inv.amount}) dated {inv.txn_date}."))

    seen = {}
    for pay in payments:
        key = (pay.txn_date, pay.amount, pay.description.strip().lower())
        first = seen.setdefault(key, pay)
        if pay.id in used_pay:
            continue
        if first.id != pay.id:
            db.add(Match(business_id=business_id, payment_id=pay.id, status="possible_duplicate",
                         difference=pay.amount,
                         reason=f"Same date, amount ({abs(pay.amount)}) and description as transaction "
                                f"#{first.id}. This may be a duplicate payment."))
        else:
            db.add(Match(business_id=business_id, payment_id=pay.id, status="unexplained",
                         difference=pay.amount,
                         reason=f"Payment of {abs(pay.amount)} on {pay.txn_date} "
                                f"({pay.description}) does not match any invoice."))
    db.commit()


def summary(db: Session, business_id: int):
    rows = (db.query(Match.status, func.count(Match.id), func.coalesce(func.sum(Match.difference), 0))
              .filter(Match.business_id == business_id)
              .group_by(Match.status).all())
    return [{"status": s, "count": c, "total_difference": str(t)} for s, c, t in rows]