from fastapi import APIRouter
from pydantic import BaseModel
from ..services.agent import ask

router = APIRouter()

class ChatIn(BaseModel):
    message: str
    session_id: str = "default"

@router.post("/chat")
def chat(body: ChatIn):
    return {"answer": ask(body.message, body.session_id)}