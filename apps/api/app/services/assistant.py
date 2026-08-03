from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.services.game_intelligence import GameIntelligenceService
from app.services.market_intelligence import MarketIntelligenceService
from app.services.recommendations import RecommendationService


@dataclass(frozen=True)
class AssistantAction:
    id: str
    title: str
    subtitle: str
    prompt: str
    category: str
    tone: str
    game_slug: str | None = None


class AssistantService:
    """Grounded launch assistant built on SportsIntel recommendation data.

    This deliberately avoids open-ended football generation. Every response is
    assembled from the same recommendation, market and game-intelligence
    objects used by the product pages, keeping answers fast and explainable.
    """

    def __init__(self, db: Session) -> None:
        self.recommendations = RecommendationService(db)
        self.markets = MarketIntelligenceService(db)
        self.games = GameIntelligenceService(db)

    def workspace(self) -> dict[str, Any]:
        survivor = self.recommendations.survivor_rankings()
        spread = self.recommendations.spread_rankings()
        totals = self.recommendations.totals_rankings()
        games = [
            detail
            for item in self.games.list_games()
            if (detail := self.games.get_game(item["slug"])) is not None
        ]

        leader = survivor[0]
        challenger = survivor[1]
        biggest_mover = max(
            [*survivor, *spread, *totals],
            key=lambda item: abs(int(item.get("trend", 0))),
        )
        weather_games = sorted(
            games,
            key=lambda game: (
                int(game.get("weather", {}).get("wind_mph", 0)),
                "rain" in game.get("weather", {}).get("summary", "").lower(),
            ),
            reverse=True,
        )
        injury_games = sorted(
            games,
            key=lambda game: abs(
                int(game.get("context", {}).get("injury_edge", 0))
            ),
            reverse=True,
        )

        actions = [
            AssistantAction(
                id="why-top-survivor",
                title=f"Why {leader['team']}?",
                subtitle="Explain the top Survivor recommendation",
                prompt=f"Why is {leader['team']} the top Survivor recommendation?",
                category="SURVIVOR",
                tone="POSITIVE",
                game_slug=leader.get("game_slug"),
            ),
            AssistantAction(
                id="compare-survivor",
                title=f"Compare {leader['abbreviation']} vs {challenger['abbreviation']}",
                subtitle="Current safety versus future value",
                prompt=(
                    f"Compare {leader['team']} and {challenger['team']} for Survivor."
                ),
                category="COMPARE",
                tone="NEUTRAL",
            ),
            AssistantAction(
                id="best-spread",
                title="Best spread edge",
                subtitle=spread[0]["selection"],
                prompt="What is the strongest spread opportunity and why?",
                category="SPREAD",
                tone="POSITIVE",
                game_slug=spread[0].get("game_slug"),
            ),
            AssistantAction(
                id="best-total",
                title="Best totals edge",
                subtitle=totals[0]["selection"],
                prompt="What is the strongest totals opportunity and why?",
                category="TOTAL",
                tone="POSITIVE",
                game_slug=totals[0].get("game_slug"),
            ),
            AssistantAction(
                id="biggest-mover",
                title="Biggest mover",
                subtitle=self._display_name(biggest_mover),
                prompt="Explain today's biggest recommendation movement.",
                category="MOVEMENT",
                tone="WARNING" if biggest_mover.get("trend", 0) < 0 else "POSITIVE",
                game_slug=biggest_mover.get("game_slug"),
            ),
            AssistantAction(
                id="weather-impact",
                title="Weather-sensitive game",
                subtitle=weather_games[0]["matchup"],
                prompt="Which game is most sensitive to weather and why?",
                category="WEATHER",
                tone="WARNING",
                game_slug=weather_games[0].get("slug"),
            ),
            AssistantAction(
                id="injury-impact",
                title="Largest injury edge",
                subtitle=injury_games[0]["matchup"],
                prompt="Which matchup has the largest injury impact?",
                category="INJURY",
                tone="WARNING",
                game_slug=injury_games[0].get("slug"),
            ),
        ]

        return {
            "season": 2026,
            "week": 1,
            "last_updated": datetime.now(timezone.utc),
            "mode": "grounded-decision-assistant",
            "featured": {
                "title": f"{leader['team']} leads Survivor",
                "summary": leader["summary"],
                "edge": leader["edge"],
                "confidence": leader["confidence"],
                "risk": leader["risk"],
                "trend": leader["trend"],
                "game_slug": leader.get("game_slug"),
                "evidence": leader["evidence"][:4],
                "warnings": leader["warnings"],
            },
            "actions": [action.__dict__ for action in actions],
            "suggested_prompts": [action.prompt for action in actions],
            "capabilities": [
                "Explain recommendations",
                "Compare Survivor candidates",
                "Identify spread and totals edges",
                "Summarize weather and injury risk",
                "Explain recommendation movement",
            ],
        }

    def answer(self, prompt: str) -> dict[str, Any]:
        normalized = " ".join(prompt.lower().strip().split())
        if not normalized:
            return self._response(
                prompt,
                "Ask about Survivor, spreads, totals, weather, injuries, or a matchup.",
                [],
                "GENERAL",
            )

        survivor = self.recommendations.survivor_rankings()
        spread = self.recommendations.spread_rankings()
        totals = self.recommendations.totals_rankings()

        if "compare" in normalized:
            matches = [item for item in survivor if self._mentions(item, normalized)]
            if len(matches) < 2:
                matches = survivor[:2]
            return self._compare_survivor(prompt, matches[0], matches[1])

        if any(token in normalized for token in ("spread", "point spread", "cover")):
            item = next((row for row in spread if self._mentions(row, normalized)), spread[0])
            return self._market_answer(prompt, item, "SPREAD")

        if any(token in normalized for token in ("total", "over", "under", "scoring")):
            item = next((row for row in totals if self._mentions(row, normalized)), totals[0])
            return self._market_answer(prompt, item, "TOTAL")

        if "weather" in normalized or "wind" in normalized or "rain" in normalized:
            games = sorted(
                [
                    detail
                    for item in self.games.list_games()
                    if (detail := self.games.get_game(item["slug"])) is not None
                ],
                key=lambda game: int(game.get("weather", {}).get("wind_mph", 0)),
                reverse=True,
            )
            game = games[0]
            weather = game["weather"]
            return self._response(
                prompt,
                (
                    f"{game['matchup']} has the strongest current weather sensitivity: "
                    f"{weather['summary']}, {weather['temperature_f']}°F and "
                    f"{weather['wind_mph']} mph wind. The impact is rated "
                    f"{weather['impact'].lower()}, with the totals market most exposed."
                ),
                [
                    f"Wind: {weather['wind_mph']} mph",
                    f"Conditions: {weather['summary']}",
                    f"Roof: {weather['roof']}",
                ],
                "WEATHER",
                game.get("slug"),
            )

        if "injur" in normalized or "availability" in normalized:
            games = sorted(
                [
                    detail
                    for item in self.games.list_games()
                    if (detail := self.games.get_game(item["slug"])) is not None
                ],
                key=lambda game: abs(int(game.get("context", {}).get("injury_edge", 0))),
                reverse=True,
            )
            game = games[0]
            context = game["context"]
            return self._response(
                prompt,
                (
                    f"{game['matchup']} currently shows the largest availability gap. "
                    f"The away side has {context['away_injury_count']} tracked injuries "
                    f"versus {context['home_injury_count']} for the home side, creating "
                    f"an injury edge of {context['injury_edge']:+d}."
                ),
                [
                    f"Away injuries: {context['away_injury_count']}",
                    f"Home injuries: {context['home_injury_count']}",
                    f"Injury edge: {context['injury_edge']:+d}",
                ],
                "INJURY",
                game.get("slug"),
            )

        if "mover" in normalized or "changed" in normalized or "movement" in normalized:
            items = [*survivor, *spread, *totals]
            item = max(items, key=lambda row: abs(int(row.get("trend", 0))))
            direction = "improved" if item["trend"] > 0 else "declined"
            return self._response(
                prompt,
                (
                    f"{self._display_name(item)} is the largest current mover. Its "
                    f"SportsIntel signal {direction} by {abs(item['trend'])} points, "
                    f"with an Edge of {item['edge']} and {item['confidence']}% confidence. "
                    f"{item['summary']}"
                ),
                [
                    f"Edge: {item['edge']}",
                    f"Confidence: {item['confidence']}%",
                    f"Movement: {item['trend']:+d}",
                ],
                "MOVEMENT",
                item.get("game_slug"),
            )

        candidate = next((item for item in survivor if self._mentions(item, normalized)), survivor[0])
        return self._survivor_answer(prompt, candidate)

    def _survivor_answer(self, prompt: str, item: dict[str, Any]) -> dict[str, Any]:
        evidence = list(item.get("evidence", []))
        warnings = list(item.get("warnings", []))
        answer = (
            f"{item['team']} carries a SportsIntel Survivor Edge of {item['edge']} "
            f"with {item['confidence']}% confidence and {item['risk'].lower()} risk. "
            f"{item['summary']}"
        )
        if warnings:
            answer += f" The main caution is {warnings[0].lower()}."
        return self._response(
            prompt,
            answer,
            evidence[:4] + [f"Win probability: {item['win_probability']}%", f"Future value: {item['future_value']}"],
            "SURVIVOR",
            item.get("game_slug"),
        )

    def _compare_survivor(
        self,
        prompt: str,
        left: dict[str, Any],
        right: dict[str, Any],
    ) -> dict[str, Any]:
        safer = left if left["win_probability"] >= right["win_probability"] else right
        lower_cost = left if left["future_value"] <= right["future_value"] else right
        answer = (
            f"{safer['team']} is the safer immediate Survivor choice at "
            f"{safer['win_probability']}% projected win probability. "
            f"{lower_cost['team']} has the lower future-value cost at "
            f"{lower_cost['future_value']}. "
        )
        if safer["abbreviation"] == lower_cost["abbreviation"]:
            answer += f"That makes {safer['team']} the stronger balanced decision."
        else:
            answer += (
                f"Choose {safer['team']} for maximum current-week safety; choose "
                f"{lower_cost['team']} to preserve more premium future options."
            )
        return self._response(
            prompt,
            answer,
            [
                f"{left['abbreviation']} Edge {left['edge']} · Win {left['win_probability']}% · Future {left['future_value']}",
                f"{right['abbreviation']} Edge {right['edge']} · Win {right['win_probability']}% · Future {right['future_value']}",
                f"Public usage: {left['abbreviation']} {left['public_pick']}% · {right['abbreviation']} {right['public_pick']}%",
            ],
            "COMPARE",
            safer.get("game_slug"),
            related=[
                {"label": left["team"], "href": f"/games/{left['game_slug']}"},
                {"label": right["team"], "href": f"/games/{right['game_slug']}"},
            ],
        )

    def _market_answer(
        self,
        prompt: str,
        item: dict[str, Any],
        category: str,
    ) -> dict[str, Any]:
        answer = (
            f"{item['selection']} is the top current {category.lower()} signal with a "
            f"SportsIntel Edge of {item['edge']} and {item['confidence']}% confidence. "
            f"{item['summary']}"
        )
        return self._response(
            prompt,
            answer,
            [
                f"Matchup: {item['matchup']}",
                f"Risk: {item['risk'].title()}",
                f"Movement: {item['trend']:+d}",
            ],
            category,
            item.get("game_slug"),
        )

    @staticmethod
    def _mentions(item: dict[str, Any], normalized: str) -> bool:
        values = [
            str(item.get("team", "")),
            str(item.get("abbreviation", "")),
            str(item.get("matchup", "")),
            str(item.get("selection", "")),
            str(item.get("opponent", "")),
        ]
        for value in values:
            lowered = value.lower().strip()
            if not lowered:
                continue
            if lowered in normalized:
                return True
            meaningful_tokens = [token for token in lowered.replace("vs", " ").split() if len(token) >= 3]
            if any(token in normalized for token in meaningful_tokens):
                return True
        return False

    @staticmethod
    def _display_name(item: dict[str, Any]) -> str:
        return str(item.get("team") or item.get("selection") or item.get("matchup") or "Recommendation")

    @staticmethod
    def _response(
        prompt: str,
        answer: str,
        evidence: list[str],
        category: str,
        game_slug: str | None = None,
        related: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        links = list(related or [])
        if game_slug and not any(link.get("href") == f"/games/{game_slug}" for link in links):
            links.append({"label": "Open Game Intelligence", "href": f"/games/{game_slug}"})
        return {
            "prompt": prompt,
            "answer": answer,
            "category": category,
            "evidence": evidence,
            "related": links,
            "generated_at": datetime.now(timezone.utc),
            "grounding": "SportsIntel launch-model recommendations and game intelligence",
        }
