from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .db import get_db
from .models import User, Business
from .security import read_token


def business_dict(b: Business) -> dict:
    return {"id": b.id, "name": b.name, "currency": b.currency}


def current_user(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> User:
    scheme, _, token = authorization.partition(" ")
    uid = read_token(token) if scheme.lower() == "bearer" else None
    user = db.get(User, uid) if uid else None
    if not user:
        raise HTTPException(401, "Not authenticated")
    return user


def current_business(x_business_id: int = Header(...), user: User = Depends(current_user),
                     db: Session = Depends(get_db)) -> Business:
    biz = db.get(Business, x_business_id)
    if not biz or biz.user_id != user.id:
        raise HTTPException(404, "Business not found")
    return biz