from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.lms import SurvivorPool

router = APIRouter(prefix="/lms", tags=["lms"])


@router.get("/pools")
def list_pools(db: Session = Depends(get_db)):
    pools = db.scalars(select(SurvivorPool).order_by(SurvivorPool.id)).all()
    return [
        {
            "id": pool.id,
            "name": pool.name,
            "season_id": pool.season_id,
            "tie_eliminates": pool.tie_eliminates,
            "allow_reuse": pool.allow_reuse,
            "buybacks_allowed": pool.buybacks_allowed,
            "picks_per_week": pool.picks_per_week,
        }
        for pool in pools
    ]
