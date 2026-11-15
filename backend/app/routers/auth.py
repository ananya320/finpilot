import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..deps import current_user, business_dict
from ..models import User, Business
from ..security import hash_password, verify_password, make_token

router = APIRouter(prefix="/auth", tags=["auth"])
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DUMMY_HASH = hash_password("dummy-password")  # keeps login timing similar for unknown emails


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: str = Field(max_length=200)
    password: str = Field(min_length=8, max_length=72)
    business_name: str = Field(default="My Business", min_length=1, max_length=80)


class LoginIn(BaseModel):
    email: str = Field(max_length=200)
    password: str = Field(max_length=72)


class ProfileIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class PasswordIn(BaseModel):
    current_password: str = Field(max_length=72)
    new_password: str = Field(min_length=8, max_length=72)


def _user(u: User) -> dict:
    return {"id": u.id, "name": u.name, "email": u.email}


def _session(user: User, db: Session, with_token: bool = True) -> dict:
    rows = db.query(Business).filter_by(user_id=user.id).order_by(Business.id).all()
    out = {"user": _user(user), "businesses": [business_dict(b) for b in rows]}
    if with_token:
        out["token"] = make_token(user.id)
    return out


def _check_len(password: str):
    if len(password.encode()) > 72:
        raise HTTPException(422, "Password is too long (max 72 bytes).")


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if not settings.allow_signup:
        raise HTTPException(403, "Sign-up is disabled.")
    email = body.email.strip().lower()
    if not EMAIL.match(email):
        raise HTTPException(422, "Enter a valid email address.")
    _check_len(body.password)
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "An account with this email already exists.")
    user = User(email=email, name=body.name.strip(), password_hash=hash_password(body.password))
    db.add(user)
    db.flush()
    db.add(Business(user_id=user.id, name=body.business_name.strip(), currency="$"))
    db.commit()
    return _session(user, db)


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=body.email.strip().lower()).first()
    ok = verify_password(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not ok:
        raise HTTPException(401, "Invalid email or password.")
    return _session(user, db)


@router.get("/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return _session(user, db, with_token=False)


@router.patch("/me")
def update_me(body: ProfileIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.name = body.name.strip()
    db.commit()
    return _user(user)


@router.post("/password")
def change_password(body: PasswordIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect.")
    _check_len(body.new_password)
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"ok": True}