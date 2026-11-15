from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import settings


def _secret() -> str:
    if not settings.secret_key:
        raise RuntimeError("SECRET_KEY is not set in .env")
    return settings.secret_key


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def make_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=settings.token_days)
    return jwt.encode({"sub": str(user_id), "exp": exp}, _secret(), algorithm="HS256")


def read_token(token: str):
    try:
        data = jwt.decode(token, _secret(), algorithms=["HS256"])
        return int(data["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None