from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sports import Team


@dataclass(frozen=True)
class TeamSeed:
    abbreviation: str
    opponent: str
    location: str
    win_probability: float
    future_value: float
    public_pick: float
    trend: int
    risk: str
    evidence: tuple[str, ...]
    warnings: tuple[str, ...]


LAUNCH_SEEDS: tuple[TeamSeed, ...] = (
    TeamSeed("BUF", "NYJ", "Home", 0.86, 78, 29, 3, "LOW", ("Strong home matchup", "Stable quarterback situation", "Opponent offensive uncertainty", "Favorable rest profile"), ("Division matchup",)),
    TeamSeed("SEA", "ARI", "Home", 0.82, 59, 11, 4, "LOW", ("Strong matchup profile", "Low future opportunity cost", "Home-field advantage", "Low projected public usage"), ("Opponent pace uncertainty",)),
    TeamSeed("PHI", "NYG", "Home", 0.84, 86, 23, 1, "MEDIUM", ("Roster advantage", "Home-field advantage", "Offensive line stability"), ("High future value", "Division matchup")),
    TeamSeed("DET", "CHI", "Home", 0.80, 66, 14, 2, "LOW", ("Home scoring profile", "Rest advantage", "Balanced roster"), ("Opponent volatility",)),
    TeamSeed("BAL", "CLE", "Home", 0.83, 90, 18, 0, "MEDIUM", ("Quarterback advantage", "Defensive matchup", "Home-field advantage"), ("Premium future matchups", "Division matchup")),
    TeamSeed("KC", "LV", "Home", 0.88, 96, 37, -1, "MEDIUM", ("Elite quarterback", "Strong win probability", "Coaching advantage"), ("Very high future value", "Heavy projected public usage")),
    TeamSeed("SF", "LAR", "Home", 0.79, 88, 17, -2, "MEDIUM", ("Defensive matchup", "Home-field advantage", "Roster depth"), ("Division matchup", "Future opportunity cost")),
    TeamSeed("GB", "MIN", "Home", 0.74, 61, 8, 2, "MEDIUM", ("Low projected usage", "Home-field advantage", "Favorable offensive matchup"), ("Division volatility",)),
)


class RecommendationService:
    """Fast launch scoring service.

    The service is deterministic by design. Live odds, injuries, and weather can
    replace the launch inputs without changing the API or frontend contracts.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.teams = {
            team.abbreviation: team
            for team in db.scalars(select(Team)).all()
        }

    @staticmethod
    def _edge(seed: TeamSeed) -> int:
        survival = seed.win_probability * 100
        future_cost = max(seed.future_value - 65, 0) * 0.28
        ownership_cost = max(seed.public_pick - 18, 0) * 0.12
        risk_cost = {"LOW": 0, "MEDIUM": 4, "HIGH": 9}[seed.risk]
        score = survival + 11 - future_cost - ownership_cost - risk_cost
        return max(1, min(99, round(score)))

    @staticmethod
    def _label(edge: int) -> str:
        if edge >= 90:
            return "Elite"
        if edge >= 84:
            return "Strong"
        if edge >= 76:
            return "Consider"
        return "Risky"

    def survivor_rankings(self) -> list[dict]:
        recommendations: list[dict] = []
        for seed in LAUNCH_SEEDS:
            team = self.teams.get(seed.abbreviation)
            edge = self._edge(seed)
            confidence = max(55, min(97, round(seed.win_probability * 100 + 6 - (3 if seed.risk == "MEDIUM" else 0))))
            recommendations.append(
                {
                    "team_id": team.id if team else None,
                    "team": team.name if team else seed.abbreviation,
                    "abbreviation": seed.abbreviation,
                    "opponent": seed.opponent,
                    "location": seed.location,
                    "edge": edge,
                    "confidence": confidence,
                    "risk": seed.risk,
                    "label": self._label(edge),
                    "trend": seed.trend,
                    "win_probability": round(seed.win_probability * 100),
                    "future_value": seed.future_value,
                    "public_pick": seed.public_pick,
                    "summary": self._summary(seed, edge),
                    "evidence": list(seed.evidence),
                    "warnings": list(seed.warnings),
                }
            )
        return sorted(recommendations, key=lambda item: item["edge"], reverse=True)

    @staticmethod
    def _summary(seed: TeamSeed, edge: int) -> str:
        if seed.future_value >= 90:
            return f"Excellent current matchup, but preserving {seed.abbreviation} may create more value later."
        if seed.public_pick <= 12:
            return f"Strong survival profile with low projected duplication and limited future-value cost."
        if edge >= 90:
            return "One of the strongest current-week survival profiles with manageable season-long cost."
        return "A viable survivor option with a balanced current-week and future-value profile."

    def spread_rankings(self) -> list[dict]:
        return [
            {"matchup": "DET vs CHI", "selection": "Detroit -4.0", "edge": 88, "confidence": 82, "risk": "LOW", "trend": 2, "summary": "Detroit's home efficiency and matchup profile create the clearest early spread signal."},
            {"matchup": "BUF vs NYJ", "selection": "Buffalo -6.5", "edge": 86, "confidence": 80, "risk": "MEDIUM", "trend": 1, "summary": "Buffalo holds advantages at quarterback and offensive continuity, with division risk remaining."},
            {"matchup": "PHI vs NYG", "selection": "Philadelphia -5.5", "edge": 83, "confidence": 78, "risk": "MEDIUM", "trend": -1, "summary": "Philadelphia's line play supports the number, but divisional familiarity lowers confidence."},
        ]

    def totals_rankings(self) -> list[dict]:
        return [
            {"matchup": "DET vs CHI", "selection": "Over 47.5", "edge": 87, "confidence": 81, "risk": "LOW", "trend": 3, "summary": "Detroit pace and red-zone efficiency support an above-market scoring environment."},
            {"matchup": "KC vs LV", "selection": "Over 49.0", "edge": 84, "confidence": 77, "risk": "MEDIUM", "trend": 1, "summary": "Kansas City's offensive ceiling is strong, while the total already prices in substantial scoring."},
            {"matchup": "BAL vs CLE", "selection": "Under 44.5", "edge": 81, "confidence": 76, "risk": "MEDIUM", "trend": -1, "summary": "Defensive matchup strength and divisional familiarity favor a lower-scoring profile."},
        ]

    def today(self) -> dict:
        survivor = self.survivor_rankings()
        spread = self.spread_rankings()
        totals = self.totals_rankings()
        return {
            "season": 2026,
            "week": 1,
            "last_updated": datetime.now(timezone.utc),
            "data_mode": "launch-model",
            "changes": [
                {"type": "SURVIVOR", "direction": "UP", "entity": "Buffalo Bills", "delta": 3, "message": "Roster stability improved the survivor profile."},
                {"type": "TOTAL", "direction": "UP", "entity": "DET vs CHI", "delta": 3, "message": "Scoring environment strengthened."},
                {"type": "SURVIVOR", "direction": "DOWN", "entity": "San Francisco 49ers", "delta": -2, "message": "Future opportunity cost increased."},
                {"type": "SPREAD", "direction": "UP", "entity": "Detroit -4.0", "delta": 2, "message": "Matchup confidence improved."},
            ],
            "metrics": {
                "teams_evaluated": len(survivor),
                "strategies_active": 3,
                "changes_today": 4,
                "average_confidence": round(sum(item["confidence"] for item in survivor[:5]) / 5),
            },
            "survivor": survivor[:5],
            "spread": spread,
            "totals": totals,
            "watchlist": [],
            "quick_questions": [
                "Why is Buffalo ranked first?",
                "Compare Buffalo and Seattle",
                "Which elite team should I save?",
                "What are the biggest Week 1 risks?",
            ],
        }
