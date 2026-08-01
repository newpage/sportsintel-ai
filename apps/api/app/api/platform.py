from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.sports import League, Team
from app.models.lms import SurvivorPool

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/readiness")
def readiness(db: Session = Depends(get_db)):
    league_count = db.scalar(select(func.count()).select_from(League)) or 0
    team_count = db.scalar(select(func.count()).select_from(Team)) or 0
    lms_pool_count = db.scalar(select(func.count()).select_from(SurvivorPool)) or 0

    return {
        "status": "ready",
        "environment": settings.app_env,
        "provider": settings.sports_data_provider,
        "checks": {
            "database": True,
            "nfl_league_loaded": league_count > 0,
            "all_32_teams_loaded": team_count == 32,
            "lms_domain_ready": True,
        },
        "counts": {
            "leagues": league_count,
            "teams": team_count,
            "lms_pools": lms_pool_count,
        },
    }
