from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine, SessionLocal
from .routers import auth, businesses, upload, data, chat
from .seed import ensure_default_user


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)   # use Alembic migrations in production
    with SessionLocal() as db:
        ensure_default_user(db)
    yield


app = FastAPI(title="FinPilot", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:3000"],
                   allow_methods=["*"], allow_headers=["*"])
for r in (auth, businesses, upload, data, chat):
    app.include_router(r.router)


@app.get("/health")
def health():
    return {"ok": True}