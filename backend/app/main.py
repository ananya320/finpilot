from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import Base, engine
from .routers import upload, data, chat

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)   # use Alembic migrations in production
    yield

app = FastAPI(title="FinPilot", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:3000"],
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(upload.router)
app.include_router(data.router)
app.include_router(chat.router)

@app.get("/health")
def health():
    return {"ok": True}