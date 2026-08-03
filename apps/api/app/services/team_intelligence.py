from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sports import Team
from app.services.game_intelligence import GAME_SEEDS
from app.services.recommendations import RecommendationService


class TeamIntelligenceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.teams = {
            team.abbreviation: team
            for team in db.scalars(select(Team)).all()
        }
        self.recommendations = RecommendationService(db)

    def list_teams(self) -> list[dict]:
        survivor = {
            item["abbreviation"]: item
            for item in self.recommendations.survivor_rankings()
        }
        spread = self.recommendations.spread_rankings()
        totals = self.recommendations.totals_rankings()
        result: list[dict] = []

        for abbreviation, team in self.teams.items():
            upcoming = next(
                (
                    seed
                    for seed in GAME_SEEDS
                    if seed.home == abbreviation or seed.away == abbreviation
                ),
                None,
            )
            survivor_item = survivor.get(abbreviation)
            home_spread = next(
                (
                    item
                    for item in spread
                    if upcoming and item["game_slug"] == upcoming.slug
                ),
                None,
            )
            total_item = next(
                (
                    item
                    for item in totals
                    if upcoming and item["game_slug"] == upcoming.slug
                ),
                None,
            )
            edge_values = [
                item["edge"]
                for item in (survivor_item, home_spread, total_item)
                if item
            ]
            rating = round(sum(edge_values) / len(edge_values)) if edge_values else 70
            result.append(
                {
                    "id": team.id,
                    "abbreviation": abbreviation,
                    "name": team.name,
                    "city": team.city,
                    "conference": team.conference,
                    "division": team.division,
                    "rating": rating,
                    "trend": survivor_item["trend"] if survivor_item else 0,
                    "risk": survivor_item["risk"] if survivor_item else "MEDIUM",
                    "survivor_edge": survivor_item["edge"] if survivor_item else None,
                    "spread_edge": home_spread["edge"] if home_spread else None,
                    "total_edge": total_item["edge"] if total_item else None,
                    "game_slug": upcoming.slug if upcoming else None,
                    "opponent": (
                        upcoming.away if upcoming and upcoming.home == abbreviation
                        else upcoming.home if upcoming else None
                    ),
                    "location": (
                        "HOME" if upcoming and upcoming.home == abbreviation
                        else "AWAY" if upcoming else None
                    ),
                }
            )

        return sorted(result, key=lambda item: item["rating"], reverse=True)

    def get_team(self, abbreviation: str) -> dict | None:
        code = abbreviation.upper()
        team = self.teams.get(code)
        if not team:
            return None

        summary = next(
            item for item in self.list_teams() if item["abbreviation"] == code
        )
        survivor = next(
            (
                item
                for item in self.recommendations.survivor_rankings()
                if item["abbreviation"] == code
            ),
            None,
        )
        seed = next(
            (
                item
                for item in GAME_SEEDS
                if item.home == code or item.away == code
            ),
            None,
        )

        factors = [
            {
                "label": "Roster stability",
                "score": 92 if code in {"BUF", "PHI", "KC", "DET"} else 82,
                "tone": "POSITIVE",
            },
            {
                "label": "Quarterback confidence",
                "score": 95 if code in {"BUF", "KC", "BAL"} else 84,
                "tone": "POSITIVE",
            },
            {
                "label": "Current availability",
                "score": max(60, 96 - ((seed.injury_home if seed and seed.home == code else seed.injury_away if seed else 3) * 6)),
                "tone": "POSITIVE",
            },
            {
                "label": "Future survivor value",
                "score": survivor["future_value"] if survivor else 65,
                "tone": "NEUTRAL",
            },
        ]

        return {
            **summary,
            "survivor": survivor,
            "factors": factors,
            "headline": (
                survivor["summary"] if survivor
                else f"{team.name} is being monitored for future strategy opportunities."
            ),
            "upcoming_game": None if not seed else {
                "slug": seed.slug,
                "opponent": seed.away if seed.home == code else seed.home,
                "location": "HOME" if seed.home == code else "AWAY",
                "kickoff_day": seed.kickoff_day,
                "kickoff_time": seed.kickoff_time,
                "venue": seed.venue,
                "weather": seed.weather,
                "spread": seed.spread,
                "total": seed.total,
            },
            "assistant_questions": [
                f"Why is {team.name} rated {summary['rating']}?",
                f"Should I use {team.name} in Survivor this week?",
                f"What is the biggest risk for {team.name}?",
                f"Compare {team.name} with another top team.",
            ],
        }
