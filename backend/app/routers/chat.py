from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..deps import current_user, current_business
from ..services.agent import ask

router = APIRouter()


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(default="default", max_length=100)


@router.post("/chat")
def chat(body: ChatIn, user=Depends(current_user), biz=Depends(current_business)):
    thread = f"{user.id}:{biz.id}:{body.session_id}"
    return {"answer": ask(body.message, thread, biz.id)}