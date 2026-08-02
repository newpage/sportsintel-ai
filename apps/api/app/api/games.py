from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.services.game_intelligence import GameIntelligenceService

router = APIRouter(prefix="/games", tags=["games"])


@router.get("")
def list_games(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "season": 2026,
        "week": 1,
        "games": GameIntelligenceService(db).list_games(),
    }


@router.get("/{slug}")
def get_game(
    slug: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    game = GameIntelligenceService(db).get_game(slug)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game
