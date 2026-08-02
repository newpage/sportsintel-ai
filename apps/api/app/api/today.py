from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.services.recommendations import RecommendationService

router = APIRouter(tags=["today"])


@router.get("/today")
def today(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RecommendationService(db).today()


@router.get("/survivor/recommendations")
def survivor_recommendations(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "season": 2026,
        "week": 1,
        "recommendations": RecommendationService(db).survivor_rankings(),
    }
