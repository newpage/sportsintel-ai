from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.services.team_intelligence import TeamIntelligenceService

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("")
def list_teams(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"season": 2026, "week": 1, "teams": TeamIntelligenceService(db).list_teams()}


@router.get("/{abbreviation}")
def team_detail(
    abbreviation: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = TeamIntelligenceService(db).get_team(abbreviation)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team
