from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.services.game_intelligence import GameIntelligenceService
from app.services.team_intelligence import TeamIntelligenceService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(
    q: str = Query(min_length=1, max_length=80),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    needle = q.strip().lower()
    teams = [
        {
            "type": "TEAM",
            "key": item["abbreviation"],
            "title": item["name"],
            "subtitle": f"{item['conference']} {item['division']} · Rating {item['rating']}",
            "href": f"/teams/{item['abbreviation'].lower()}",
        }
        for item in TeamIntelligenceService(db).list_teams()
        if needle in item["name"].lower()
        or needle in item["abbreviation"].lower()
        or needle in item["city"].lower()
    ]
    games = [
        {
            "type": "GAME",
            "key": item["slug"],
            "title": f"{item['away']['abbreviation']} at {item['home']['abbreviation']}",
            "subtitle": f"{item['kickoff_day']} {item['kickoff_time']} · Edge {item['game_edge']}",
            "href": f"/games/{item['slug']}",
        }
        for item in GameIntelligenceService(db).list_games()
        if needle in item["slug"].replace("-", " ")
        or needle in item["away"]["name"].lower()
        or needle in item["home"]["name"].lower()
        or needle in item["away"]["abbreviation"].lower()
        or needle in item["home"]["abbreviation"].lower()
    ]
    return {"query": q, "results": (teams + games)[:12]}
