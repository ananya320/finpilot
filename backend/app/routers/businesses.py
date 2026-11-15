from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user, business_dict
from ..models import Business, Match, Transaction, Document
from ..services import vectorstore

router = APIRouter(prefix="/businesses", tags=["businesses"])
CURRENCIES = {"$", "₹"}
MAX_BUSINESSES = 20


class BizIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    currency: str = "$"


class BizPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    currency: str | None = None


def _own(db: Session, user, bid: int) -> Business:
    biz = db.get(Business, bid)
    if not biz or biz.user_id != user.id:
        raise HTTPException(404, "Business not found")
    return biz


@router.get("")
def list_businesses(user=Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Business).filter_by(user_id=user.id).order_by(Business.id).all()
    return [business_dict(b) for b in rows]


@router.post("")
def create_business(body: BizIn, user=Depends(current_user), db: Session = Depends(get_db)):
    if body.currency not in CURRENCIES:
        raise HTTPException(422, "Currency must be $ or ₹.")
    if db.query(Business).filter_by(user_id=user.id).count() >= MAX_BUSINESSES:
        raise HTTPException(400, f"You can have at most {MAX_BUSINESSES} businesses.")
    biz = Business(user_id=user.id, name=body.name.strip(), currency=body.currency)
    db.add(biz)
    db.commit()
    return business_dict(biz)


@router.patch("/{bid}")
def update_business(bid: int, body: BizPatch, user=Depends(current_user), db: Session = Depends(get_db)):
    biz = _own(db, user, bid)
    if body.name is not None:
        biz.name = body.name.strip()
    if body.currency is not None:
        if body.currency not in CURRENCIES:
            raise HTTPException(422, "Currency must be $ or ₹.")
        biz.currency = body.currency
    db.commit()
    return business_dict(biz)


@router.delete("/{bid}")
def delete_business(bid: int, user=Depends(current_user), db: Session = Depends(get_db)):
    biz = _own(db, user, bid)
    if db.query(Business).filter_by(user_id=user.id).count() <= 1:
        raise HTTPException(400, "You need at least one business.")
    for model in (Match, Transaction, Document):
        db.query(model).filter(model.business_id == bid).delete()
    db.delete(biz)
    db.commit()
    try:
        vectorstore.delete_business(bid)
    except Exception:
        pass  # search index cleanup is best effort
    return {"deleted": bid}