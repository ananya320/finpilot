from sqlalchemy.orm import Session

from .config import settings
from .models import User, Business
from .security import hash_password, verify_password


def ensure_default_user(db: Session):
    """Creates the fixed account if missing, and keeps its password in sync with config.py."""
    email = settings.default_email.strip().lower()
    user = db.query(User).filter_by(email=email).first()
    if not user:
        user = User(email=email, name=settings.default_name,
                    password_hash=hash_password(settings.default_password))
        db.add(user)
        db.flush()
        db.add(Business(user_id=user.id, name="My Business", currency="$"))
    elif not verify_password(settings.default_password, user.password_hash):
        user.password_hash = hash_password(settings.default_password)
    db.commit()