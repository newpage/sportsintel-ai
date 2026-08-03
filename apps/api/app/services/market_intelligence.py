from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.services.game_intelligence import GAME_SEEDS
from app.services.recommendations import RecommendationService


class MarketIntelligenceService:
    """Launch-ready spread and totals intelligence.

    The API contract is stable while the underlying launch inputs can later be
    replaced by live odds, weather, injury and statistical feeds.
    """

    def __init__(self, db: Session) -> None:
        self.recommendations = RecommendationService(db)
        self.games = {game.slug: game for game in GAME_SEEDS}

    def spread_center(self) -> dict:
        rankings = [self._enrich_spread(item, index + 1) for index, item in enumerate(self.recommendations.spread_rankings())]
        return self._center_payload(
            strategy="SPREAD",
            title="Spread Center",
            subtitle="Ranked point-spread opportunities with matchup evidence and market risk.",
            recommendations=rankings,
            filters=["ALL", "LOW_RISK", "HOME_FAVORITES", "MOVERS"],
        )

    def totals_center(self) -> dict:
        rankings = [self._enrich_total(item, index + 1) for index, item in enumerate(self.recommendations.totals_rankings())]
        return self._center_payload(
            strategy="TOTAL",
            title="Totals Center",
            subtitle="Over/under opportunities evaluated against pace, environment and matchup context.",
            recommendations=rankings,
            filters=["ALL", "OVER", "UNDER", "LOW_RISK", "MOVERS"],
        )

    def _center_payload(self, strategy: str, title: str, subtitle: str, recommendations: list[dict], filters: list[str]) -> dict:
        average_confidence = round(sum(item["confidence"] for item in recommendations) / len(recommendations)) if recommendations else 0
        biggest_mover = max(recommendations, key=lambda item: abs(item["trend"]), default=None)
        return {
            "strategy": strategy,
            "season": 2026,
            "week": 1,
            "title": title,
            "subtitle": subtitle,
            "last_updated": datetime.now(timezone.utc),
            "data_mode": "launch-model",
            "summary": {
                "opportunities": len(recommendations),
                "average_confidence": average_confidence,
                "strong_signals": sum(1 for item in recommendations if item["edge"] >= 84),
                "low_risk": sum(1 for item in recommendations if item["risk"] == "LOW"),
                "biggest_mover": biggest_mover["selection"] if biggest_mover else None,
            },
            "filters": filters,
            "recommendations": recommendations,
        }

    def _enrich_spread(self, item: dict, rank: int) -> dict:
        game = self.games[item["game_slug"]]
        home_side = game.home in item["selection"]
        evidence = [
            f"{game.home} home-field profile",
            "Quarterback and roster continuity advantage",
            f"Market line currently {game.spread:+.1f}",
        ]
        warnings = []
        if abs(game.spread) >= 6.5:
            warnings.append("Margin requirement increases late-game variance")
        if game.home in {"BUF", "PHI", "BAL", "SF"}:
            warnings.append("Division familiarity can compress expected margin")
        if game.wind_mph >= 14:
            warnings.append("Wind may reduce offensive consistency")
        return {
            **item,
            "rank": rank,
            "strategy": "SPREAD",
            "label": self._label(item["edge"]),
            "side": "HOME" if home_side else "AWAY",
            "line": game.spread,
            "market_total": game.total,
            "weather": game.weather,
            "wind_mph": game.wind_mph,
            "evidence": evidence,
            "warnings": warnings,
            "market_movement": item["trend"] * 0.5,
            "model_margin": round(abs(game.spread) + max((item["edge"] - 80) / 4, 0), 1),
            "edge_points": round(max((item["edge"] - 78) / 3.2, 0.5), 1),
        }

    def _enrich_total(self, item: dict, rank: int) -> dict:
        game = self.games[item["game_slug"]]
        is_over = item["selection"].upper().startswith("OVER")
        weather_evidence = "Indoor conditions remove weather variance" if game.roof == "Dome" else f"{game.weather}; wind {game.wind_mph} mph"
        evidence = [
            weather_evidence,
            "Matchup pace and scoring-efficiency profile",
            f"Current market total {game.total:.1f}",
        ]
        warnings = []
        if game.wind_mph >= 14:
            warnings.append("Wind creates passing and kicking volatility")
        if is_over and game.total >= 49:
            warnings.append("High market total leaves less margin for error")
        if not is_over and game.total <= 44.5:
            warnings.append("Low starting total limits additional under value")
        projection_delta = max((item["edge"] - 78) / 2.7, 1.0)
        projected_total = game.total + projection_delta if is_over else game.total - projection_delta
        return {
            **item,
            "rank": rank,
            "strategy": "TOTAL",
            "label": self._label(item["edge"]),
            "direction": "OVER" if is_over else "UNDER",
            "market_total": game.total,
            "projected_total": round(projected_total, 1),
            "edge_points": round(abs(projected_total - game.total), 1),
            "weather": game.weather,
            "temperature_f": game.temperature,
            "wind_mph": game.wind_mph,
            "roof": game.roof,
            "evidence": evidence,
            "warnings": warnings,
            "market_movement": item["trend"] * 0.5,
        }

    @staticmethod
    def _label(edge: int) -> str:
        if edge >= 90:
            return "Elite"
        if edge >= 84:
            return "Strong"
        if edge >= 78:
            return "Consider"
        return "Watch"
