from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.models.watchlist import WatchlistItem
from app.services.game_intelligence import GameIntelligenceService
from app.services.team_intelligence import TeamIntelligenceService

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchlistRequest(BaseModel):
    entity_type: str = Field(pattern="^(TEAM|GAME)$")
    entity_key: str = Field(min_length=1, max_length=120)
    label: str = Field(min_length=1, max_length=180)


def serialize(item: WatchlistItem, db: Session) -> dict:
    detail = None
    if item.entity_type == "TEAM":
        detail = TeamIntelligenceService(db).get_team(item.entity_key)
    elif item.entity_type == "GAME":
        detail = GameIntelligenceService(db).get_game(item.entity_key)
    return {
        "id": item.id,
        "entity_type": item.entity_type,
        "entity_key": item.entity_key,
        "label": item.label,
        "created_at": item.created_at,
        "detail": detail,
    }


@router.get("")
def list_watchlist(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(WatchlistItem)
        .where(WatchlistItem.user_id == user.id)
        .order_by(WatchlistItem.created_at.desc())
    ).all()
    return {"items": [serialize(item, db) for item in rows]}


@router.post("", status_code=status.HTTP_201_CREATED)
def add_watchlist(
    body: WatchlistRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user.id,
            WatchlistItem.entity_type == body.entity_type,
            WatchlistItem.entity_key == body.entity_key,
        )
    )
    if existing:
        return serialize(existing, db)

    item = WatchlistItem(
        user_id=user.id,
        entity_type=body.entity_type,
        entity_key=body.entity_key,
        label=body.label,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return serialize(item, db)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_watchlist(
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.get(WatchlistItem, item_id)
    if not item or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    db.delete(item)
    db.commit()
