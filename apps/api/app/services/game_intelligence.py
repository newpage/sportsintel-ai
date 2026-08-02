from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sports import Team
from app.services.recommendations import RecommendationService


@dataclass(frozen=True)
class GameSeed:
    slug: str
    away: str
    home: str
    kickoff_day: str
    kickoff_time: str
    venue: str
    city: str
    spread: float
    total: float
    weather: str
    temperature: int
    wind_mph: int
    roof: str
    rest_away: int
    rest_home: int
    travel_miles: int
    injury_away: int
    injury_home: int
    headline: str


GAME_SEEDS: tuple[GameSeed, ...] = (
    GameSeed("nyj-at-buf", "NYJ", "BUF", "Sunday", "1:00 PM ET", "Highmark Stadium", "Orchard Park, NY", -6.5, 44.5, "Partly cloudy", 67, 8, "Open", 7, 7, 292, 4, 1, "Buffalo enters with the strongest combined quarterback, continuity, and home-field profile."),
    GameSeed("ari-at-sea", "ARI", "SEA", "Sunday", "4:25 PM ET", "Lumen Field", "Seattle, WA", -5.5, 46.0, "Light rain possible", 61, 10, "Open", 7, 7, 1113, 3, 2, "Seattle offers a strong home matchup without consuming a premium future survivor asset."),
    GameSeed("nyg-at-phi", "NYG", "PHI", "Sunday", "1:00 PM ET", "Lincoln Financial Field", "Philadelphia, PA", -5.5, 45.0, "Clear", 72, 6, "Open", 7, 7, 95, 4, 2, "Philadelphia owns the stronger roster and line-play profile, tempered by division familiarity."),
    GameSeed("chi-at-det", "CHI", "DET", "Sunday", "1:00 PM ET", "Ford Field", "Detroit, MI", -4.0, 47.5, "Indoor", 70, 0, "Dome", 7, 8, 281, 3, 1, "Detroit's pace, home efficiency, and rest edge support both spread and total interest."),
    GameSeed("cle-at-bal", "CLE", "BAL", "Sunday", "1:00 PM ET", "M&T Bank Stadium", "Baltimore, MD", -7.0, 44.5, "Clear", 74, 5, "Open", 7, 7, 372, 3, 1, "Baltimore's quarterback and defensive advantages are strong, but future survivor value is expensive."),
    GameSeed("lv-at-kc", "LV", "KC", "Sunday", "8:20 PM ET", "GEHA Field at Arrowhead Stadium", "Kansas City, MO", -8.0, 49.0, "Warm", 79, 9, "Open", 7, 7, 1346, 4, 1, "Kansas City has the week's highest raw win profile but also the largest future opportunity cost."),
    GameSeed("lar-at-sf", "LAR", "SF", "Monday", "8:15 PM ET", "Levi's Stadium", "Santa Clara, CA", -4.5, 48.0, "Clear", 70, 7, "Open", 7, 7, 350, 2, 2, "San Francisco's defensive profile is attractive, while divisional volatility limits confidence."),
    GameSeed("min-at-gb", "MIN", "GB", "Sunday", "4:25 PM ET", "Lambeau Field", "Green Bay, WI", -2.5, 46.5, "Breezy", 63, 14, "Open", 7, 7, 301, 2, 2, "Green Bay offers lower public usage, but weather and division variance create a wider outcome range."),
)


class GameIntelligenceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.teams = {
            team.abbreviation: team
            for team in db.scalars(select(Team)).all()
        }
        self.recommendations = RecommendationService(db)

    def list_games(self) -> list[dict]:
        survivor = {item["abbreviation"]: item for item in self.recommendations.survivor_rankings()}
        spread = {item["matchup"].replace(" vs ", "-"): item for item in self.recommendations.spread_rankings()}
        totals = {item["matchup"].replace(" vs ", "-"): item for item in self.recommendations.totals_rankings()}
        games = []
        for seed in GAME_SEEDS:
            home = self._team(seed.home)
            away = self._team(seed.away)
            matchup_key = f"{seed.home}-{seed.away}"
            survivor_item = survivor.get(seed.home)
            spread_item = spread.get(matchup_key)
            totals_item = totals.get(matchup_key)
            strategy_edges = [item["edge"] for item in (survivor_item, spread_item, totals_item) if item]
            games.append({
                "slug": seed.slug,
                "away": away,
                "home": home,
                "kickoff_day": seed.kickoff_day,
                "kickoff_time": seed.kickoff_time,
                "venue": seed.venue,
                "spread": seed.spread,
                "total": seed.total,
                "weather": seed.weather,
                "headline": seed.headline,
                "game_edge": round(sum(strategy_edges) / len(strategy_edges)) if strategy_edges else 72,
                "top_strategy": self._top_strategy(survivor_item, spread_item, totals_item),
                "survivor": survivor_item,
                "spread_signal": spread_item,
                "total_signal": totals_item,
            })
        return sorted(games, key=lambda game: game["game_edge"], reverse=True)

    def get_game(self, slug: str) -> dict | None:
        seed = next((item for item in GAME_SEEDS if item.slug == slug), None)
        if not seed:
            return None

        home = self._team(seed.home)
        away = self._team(seed.away)
        survivor = next((item for item in self.recommendations.survivor_rankings() if item["abbreviation"] == seed.home), None)
        spread = next((item for item in self.recommendations.spread_rankings() if item["matchup"] == f"{seed.home} vs {seed.away}"), None)
        total = next((item for item in self.recommendations.totals_rankings() if item["matchup"] == f"{seed.home} vs {seed.away}"), None)
        factors = self._factors(seed, home["name"], away["name"])
        confidence_values = [item["confidence"] for item in (survivor, spread, total) if item]
        game_confidence = round(sum(confidence_values) / len(confidence_values)) if confidence_values else 74
        game_edge_values = [item["edge"] for item in (survivor, spread, total) if item]
        game_edge = round(sum(game_edge_values) / len(game_edge_values)) if game_edge_values else 76

        return {
            "slug": seed.slug,
            "season": 2026,
            "week": 1,
            "status": "SCHEDULED",
            "last_updated": datetime.now(timezone.utc),
            "away": away,
            "home": home,
            "kickoff": {
                "day": seed.kickoff_day,
                "time": seed.kickoff_time,
                "venue": seed.venue,
                "city": seed.city,
            },
            "market": {
                "home_spread": seed.spread,
                "total": seed.total,
                "moneyline_home": self._moneyline(seed.spread),
                "movement": 1.0 if seed.home in {"BUF", "DET"} else -0.5 if seed.home in {"PHI", "SF"} else 0.0,
                "source": "Launch market input",
            },
            "weather": {
                "summary": seed.weather,
                "temperature_f": seed.temperature,
                "wind_mph": seed.wind_mph,
                "roof": seed.roof,
                "impact": self._weather_impact(seed),
            },
            "context": {
                "home_rest_days": seed.rest_home,
                "away_rest_days": seed.rest_away,
                "rest_edge": seed.rest_home - seed.rest_away,
                "away_travel_miles": seed.travel_miles,
                "home_injury_count": seed.injury_home,
                "away_injury_count": seed.injury_away,
                "injury_edge": seed.injury_away - seed.injury_home,
            },
            "game_edge": game_edge,
            "confidence": game_confidence,
            "risk": self._risk(seed, survivor),
            "headline": seed.headline,
            "strategies": {
                "survivor": survivor,
                "spread": spread,
                "total": total,
            },
            "factors": factors,
            "timeline": self._timeline(seed),
            "assistant_questions": [
                f"Why does {home['name']} rate well in this matchup?",
                f"What is the biggest risk for {away['name']} at {home['name']}?",
                "How do weather and injuries affect the total?",
                "Is this team worth using now in Survivor?",
            ],
        }

    def _team(self, abbreviation: str) -> dict:
        team = self.teams.get(abbreviation)
        return {
            "id": team.id if team else None,
            "abbreviation": abbreviation,
            "name": team.name if team else abbreviation,
            "city": team.city if team else abbreviation,
            "conference": team.conference if team else None,
            "division": team.division if team else None,
        }

    @staticmethod
    def _top_strategy(survivor: dict | None, spread: dict | None, total: dict | None) -> str:
        candidates = [("Survivor", survivor), ("Spread", spread), ("Total", total)]
        available = [(label, item["edge"]) for label, item in candidates if item]
        return max(available, key=lambda value: value[1])[0] if available else "Game Intelligence"

    @staticmethod
    def _moneyline(spread: float) -> int:
        return round(-110 - abs(spread) * 24)

    @staticmethod
    def _weather_impact(seed: GameSeed) -> str:
        if seed.roof == "Dome":
            return "NONE"
        if seed.wind_mph >= 14 or "rain" in seed.weather.lower():
            return "MODERATE"
        return "LOW"

    @staticmethod
    def _risk(seed: GameSeed, survivor: dict | None) -> str:
        if survivor:
            return survivor["risk"]
        if seed.wind_mph >= 14 or abs(seed.spread) < 3:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _factors(seed: GameSeed, home_name: str, away_name: str) -> list[dict]:
        return [
            {"code": "HOME_FIELD", "label": "Home field", "side": seed.home, "impact": 8, "tone": "POSITIVE", "detail": f"{home_name} receives the home-field advantage."},
            {"code": "QUARTERBACK", "label": "Quarterback stability", "side": seed.home, "impact": 11 if seed.home in {"BUF", "KC", "BAL", "PHI"} else 6, "tone": "POSITIVE", "detail": f"{home_name} has the more stable quarterback profile."},
            {"code": "INJURY", "label": "Injury availability", "side": seed.home if seed.injury_home <= seed.injury_away else seed.away, "impact": abs(seed.injury_away - seed.injury_home) * 3, "tone": "POSITIVE", "detail": f"Current availability favors {'the home team' if seed.injury_home <= seed.injury_away else away_name}."},
            {"code": "TRAVEL", "label": "Travel burden", "side": seed.away, "impact": -min(round(seed.travel_miles / 250), 7), "tone": "NEGATIVE", "detail": f"{away_name} travels approximately {seed.travel_miles:,} miles."},
            {"code": "WEATHER", "label": "Weather", "side": "TOTAL", "impact": -5 if seed.wind_mph >= 14 else -2 if "rain" in seed.weather.lower() else 1, "tone": "NEGATIVE" if seed.wind_mph >= 10 or "rain" in seed.weather.lower() else "NEUTRAL", "detail": f"{seed.weather}; wind {seed.wind_mph} mph."},
            {"code": "REST", "label": "Rest differential", "side": seed.home if seed.rest_home >= seed.rest_away else seed.away, "impact": (seed.rest_home - seed.rest_away) * 2, "tone": "POSITIVE" if seed.rest_home != seed.rest_away else "NEUTRAL", "detail": f"Rest profile is {seed.rest_home} days for the home team and {seed.rest_away} for the visitor."},
        ]

    @staticmethod
    def _timeline(seed: GameSeed) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [
            {"at": now - timedelta(hours=20), "type": "MARKET", "direction": "UP", "title": "Opening market reviewed", "detail": f"Home spread established at {seed.spread:+.1f}."},
            {"at": now - timedelta(hours=9), "type": "INJURY", "direction": "UP" if seed.injury_home < seed.injury_away else "FLAT", "title": "Availability profile updated", "detail": f"Current injury count: {seed.away} {seed.injury_away}, {seed.home} {seed.injury_home}."},
            {"at": now - timedelta(hours=3), "type": "WEATHER", "direction": "DOWN" if seed.wind_mph >= 14 or "rain" in seed.weather.lower() else "FLAT", "title": "Weather forecast refreshed", "detail": f"{seed.weather}, {seed.temperature}°F, wind {seed.wind_mph} mph."},
            {"at": now - timedelta(minutes=18), "type": "MODEL", "direction": "UP" if seed.home in {"BUF", "SEA", "DET"} else "FLAT", "title": "SportsIntel analysis recalculated", "detail": "Strategy signals and game confidence were refreshed."},
        ]
