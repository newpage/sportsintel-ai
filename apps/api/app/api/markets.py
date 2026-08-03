from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.services.market_intelligence import MarketIntelligenceService

router = APIRouter(tags=["market intelligence"])


@router.get("/spread")
def spread_center(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return MarketIntelligenceService(db).spread_center()


@router.get("/totals")
def totals_center(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return MarketIntelligenceService(db).totals_center()
