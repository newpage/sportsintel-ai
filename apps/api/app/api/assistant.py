from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.services.assistant import AssistantService

router = APIRouter(prefix="/assistant", tags=["assistant"])


class AssistantQuestion(BaseModel):
    prompt: str = Field(min_length=2, max_length=500)


@router.get("")
def assistant_workspace(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AssistantService(db).workspace()


@router.post("/query")
def assistant_query(
    body: AssistantQuestion,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AssistantService(db).answer(body.prompt)
