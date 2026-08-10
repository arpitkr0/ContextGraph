from fastapi import APIRouter
from pydantic import BaseModel

from backend.agent import answer_question


router = APIRouter()


class AskRequest(BaseModel):
    question: str


@router.post("/ask")
def ask(request: AskRequest) -> dict:
    return answer_question(request.question)
