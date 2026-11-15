from sqlalchemy.orm import Session

from .config import settings
from .models import User, Business
from .security import hash_password, verify_password


def ensure_default_user(db: Session):
    """Creates the login account if missing and keeps its password in sync with the settings."""
    email = settings.default_email.strip().lower()
    password = settings.default_password
    if not email or not password:
        return
    if settings.environment == "production" and len(password) < 12:
        raise RuntimeError("In production, DEFAULT_PASSWORD must be at least 12 characters.")
    user = db.query(User).filter_by(email=email).first()
    if not user:
        user = User(email=email, name=settings.default_name, password_hash=hash_password(password))
        db.add(user)
        db.flush()
        db.add(Business(user_id=user.id, name="My Business", currency="$"))
    elif not verify_password(password, user.password_hash):
        user.password_hash = hash_password(password)
    db.commit()