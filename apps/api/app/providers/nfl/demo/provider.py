from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sports import League, Season, Team
from app.providers.core.base import BaseProvider
from app.providers.core.types import (
    DatasetType,
    HealthStatus,
    ProviderCapability,
    ProviderHealth,
    ProviderMetadata,
    ProviderResult,
    ProviderStage,
)


NFL_TEAMS = [
    ("ARI", "Arizona Cardinals", "Arizona", "NFC", "West"),
    ("ATL", "Atlanta Falcons", "Atlanta", "NFC", "South"),
    ("BAL", "Baltimore Ravens", "Baltimore", "AFC", "North"),
    ("BUF", "Buffalo Bills", "Buffalo", "AFC", "East"),
    ("CAR", "Carolina Panthers", "Carolina", "NFC", "South"),
    ("CHI", "Chicago Bears", "Chicago", "NFC", "North"),
    ("CIN", "Cincinnati Bengals", "Cincinnati", "AFC", "North"),
    ("CLE", "Cleveland Browns", "Cleveland", "AFC", "North"),
    ("DAL", "Dallas Cowboys", "Dallas", "NFC", "East"),
    ("DEN", "Denver Broncos", "Denver", "AFC", "West"),
    ("DET", "Detroit Lions", "Detroit", "NFC", "North"),
    ("GB", "Green Bay Packers", "Green Bay", "NFC", "North"),
    ("HOU", "Houston Texans", "Houston", "AFC", "South"),
    ("IND", "Indianapolis Colts", "Indianapolis", "AFC", "South"),
    ("JAX", "Jacksonville Jaguars", "Jacksonville", "AFC", "South"),
    ("KC", "Kansas City Chiefs", "Kansas City", "AFC", "West"),
    ("LV", "Las Vegas Raiders", "Las Vegas", "AFC", "West"),
    ("LAC", "Los Angeles Chargers", "Los Angeles", "AFC", "West"),
    ("LAR", "Los Angeles Rams", "Los Angeles", "NFC", "West"),
    ("MIA", "Miami Dolphins", "Miami", "AFC", "East"),
    ("MIN", "Minnesota Vikings", "Minnesota", "NFC", "North"),
    ("NE", "New England Patriots", "New England", "AFC", "East"),
    ("NO", "New Orleans Saints", "New Orleans", "NFC", "South"),
    ("NYG", "New York Giants", "New York", "NFC", "East"),
    ("NYJ", "New York Jets", "New York", "AFC", "East"),
    ("PHI", "Philadelphia Eagles", "Philadelphia", "NFC", "East"),
    ("PIT", "Pittsburgh Steelers", "Pittsburgh", "AFC", "North"),
    ("SF", "San Francisco 49ers", "San Francisco", "NFC", "West"),
    ("SEA", "Seattle Seahawks", "Seattle", "NFC", "West"),
    ("TB", "Tampa Bay Buccaneers", "Tampa Bay", "NFC", "South"),
    ("TEN", "Tennessee Titans", "Tennessee", "AFC", "South"),
    ("WAS", "Washington Commanders", "Washington", "NFC", "East"),
]


class DemoNFLProvider(BaseProvider):
    metadata = ProviderMetadata(
        code="nfl.demo",
        name="NFL Demo Provider",
        version="1.0.0",
        stage=ProviderStage.EXPERIMENTAL,
        sports=("NFL",),
        capabilities=(
            ProviderCapability(
                dataset=DatasetType.TEAM,
                description="All 32 NFL teams for development.",
            ),
        ),
        access_type="Bundled sample data",
        license_name="Internal development data",
        attribution_required=False,
        attribution_text=None,
        commercial_use_allowed=True,
        redistribution_allowed=True,
        terms_url=None,
        requires_api_key=False,
        self_hostable=True,
        enabled_by_default=True,
        priority=1000,
    )

    def health(self) -> ProviderHealth:
        return ProviderHealth(
            status=HealthStatus.HEALTHY,
            message="Bundled development provider is available.",
            latency_ms=0,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    def fetch(self, dataset: DatasetType, **kwargs):
        if dataset != DatasetType.TEAM:
            raise ValueError(f"Unsupported dataset: {dataset}")
        return [
            {
                "abbreviation": abbreviation,
                "name": name,
                "city": city,
                "conference": conference,
                "division": division,
            }
            for abbreviation, name, city, conference, division in NFL_TEAMS
        ]

    def load(
        self,
        db: Session,
        dataset: DatasetType,
        records: list[dict],
    ) -> ProviderResult:
        league = db.scalar(select(League).where(League.code == "NFL"))
        inserted = 0
        updated = 0
        if not league:
            league = League(
                code="NFL",
                name="National Football League",
                sport="Football",
            )
            db.add(league)
            db.flush()

        season = db.scalar(
            select(Season).where(
                Season.league_id == league.id,
                Season.year == 2026,
                Season.phase == "REGULAR",
            )
        )
        if not season:
            db.add(
                Season(
                    league_id=league.id,
                    year=2026,
                    phase="REGULAR",
                )
            )

        for item in records:
            team = db.scalar(
                select(Team).where(
                    Team.abbreviation == item["abbreviation"]
                )
            )
            if team:
                team.name = item["name"]
                team.city = item["city"]
                team.conference = item["conference"]
                team.division = item["division"]
                updated += 1
            else:
                db.add(
                    Team(
                        league_id=league.id,
                        provider_key=item["abbreviation"],
                        abbreviation=item["abbreviation"],
                        name=item["name"],
                        city=item["city"],
                        conference=item["conference"],
                        division=item["division"],
                    )
                )
                inserted += 1

        db.flush()
        return ProviderResult(
            records_received=len(records),
            records_validated=len(records),
            records_inserted=inserted,
            records_updated=updated,
            records_rejected=0,
            confidence_score=100,
            confidence_reason=(
                "Bundled team catalog is deterministic and complete for "
                "development."
            ),
        )
