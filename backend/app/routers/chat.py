import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..deps import current_user, current_business
from ..services.agent import ask

router = APIRouter()
log = logging.getLogger("finpilot.chat")


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(default="default", max_length=100)


@router.post("/chat")
def chat(body: ChatIn, user=Depends(current_user), biz=Depends(current_business)):
    thread = f"{user.id}:{biz.id}:{body.session_id}"
    try:
        return {"answer": ask(body.message, thread, biz.id)}
    except Exception as e:
        log.exception("assistant failed")
        text = str(e)
        if "503" in text or "UNAVAILABLE" in text or "429" in text:
            raise HTTPException(503, "The AI model is busy right now. Please try again in a minute.")
        if "NOT_FOUND" in text:
            raise HTTPException(502, "The AI model name was rejected. Update GEMINI_MODEL in .env.")
        raise HTTPException(502, "The assistant hit an error. Check the backend window for details.")