from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, engine, SessionLocal
from .routers import auth, businesses, upload, data, chat
from .seed import ensure_default_user


@asynccontextmanager
async def lifespan(app):
    if settings.environment == "production" and len(settings.secret_key) < 32:
        raise RuntimeError("In production, SECRET_KEY must be at least 32 characters.")
    Base.metadata.create_all(engine)   # use Alembic migrations in production
    with SessionLocal() as db:
        ensure_default_user(db)
    yield


app = FastAPI(title="FinPilot", lifespan=lifespan)
origins = [o.strip().rstrip("/") for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])
for r in (auth, businesses, upload, data, chat):
    app.include_router(r.router)


@app.get("/health")
def health():
    return {"ok": True}