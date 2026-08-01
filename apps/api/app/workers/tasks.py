from celery.utils.log import get_task_logger
from sqlalchemy import select

from app.db.session import Base, SessionLocal, engine
from app.models.audit import ProviderRun
from app.models.sports import League, Season, Team
from app.models.lms import SurvivorPool
from app.workers.celery_app import celery

logger = get_task_logger(__name__)

NFL_TEAMS = [('ARI', 'Arizona Cardinals', 'Arizona', 'NFC', 'West'), ('ATL', 'Atlanta Falcons', 'Atlanta', 'NFC', 'South'), ('BAL', 'Baltimore Ravens', 'Baltimore', 'AFC', 'North'), ('BUF', 'Buffalo Bills', 'Buffalo', 'AFC', 'East'), ('CAR', 'Carolina Panthers', 'Carolina', 'NFC', 'South'), ('CHI', 'Chicago Bears', 'Chicago', 'NFC', 'North'), ('CIN', 'Cincinnati Bengals', 'Cincinnati', 'AFC', 'North'), ('CLE', 'Cleveland Browns', 'Cleveland', 'AFC', 'North'), ('DAL', 'Dallas Cowboys', 'Dallas', 'NFC', 'East'), ('DEN', 'Denver Broncos', 'Denver', 'AFC', 'West'), ('DET', 'Detroit Lions', 'Detroit', 'NFC', 'North'), ('GB', 'Green Bay Packers', 'Green Bay', 'NFC', 'North'), ('HOU', 'Houston Texans', 'Houston', 'AFC', 'South'), ('IND', 'Indianapolis Colts', 'Indianapolis', 'AFC', 'South'), ('JAX', 'Jacksonville Jaguars', 'Jacksonville', 'AFC', 'South'), ('KC', 'Kansas City Chiefs', 'Kansas City', 'AFC', 'West'), ('LV', 'Las Vegas Raiders', 'Las Vegas', 'AFC', 'West'), ('LAC', 'Los Angeles Chargers', 'Los Angeles', 'AFC', 'West'), ('LAR', 'Los Angeles Rams', 'Los Angeles', 'NFC', 'West'), ('MIA', 'Miami Dolphins', 'Miami', 'AFC', 'East'), ('MIN', 'Minnesota Vikings', 'Minnesota', 'NFC', 'North'), ('NE', 'New England Patriots', 'New England', 'AFC', 'East'), ('NO', 'New Orleans Saints', 'New Orleans', 'NFC', 'South'), ('NYG', 'New York Giants', 'New York', 'NFC', 'East'), ('NYJ', 'New York Jets', 'New York', 'AFC', 'East'), ('PHI', 'Philadelphia Eagles', 'Philadelphia', 'NFC', 'East'), ('PIT', 'Pittsburgh Steelers', 'Pittsburgh', 'AFC', 'North'), ('SF', 'San Francisco 49ers', 'San Francisco', 'NFC', 'West'), ('SEA', 'Seattle Seahawks', 'Seattle', 'NFC', 'West'), ('TB', 'Tampa Bay Buccaneers', 'Tampa Bay', 'NFC', 'South'), ('TEN', 'Tennessee Titans', 'Tennessee', 'AFC', 'South'), ('WAS', 'Washington Commanders', 'Washington', 'NFC', 'East')]


@celery.task(name="app.workers.tasks.seed_foundation")
def seed_foundation():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    run = ProviderRun(
        provider="foundation",
        dataset="nfl_catalog",
        status="running",
        records_received=32,
        records_written=0,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    try:
        league = db.scalar(select(League).where(League.code == "NFL"))
        if not league:
            league = League(code="NFL", name="National Football League", sport="Football")
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
            season = Season(league_id=league.id, year=2026, phase="REGULAR")
            db.add(season)
            db.flush()

        for abbreviation, name, city, conference, division in NFL_TEAMS:
            team = db.scalar(select(Team).where(Team.abbreviation == abbreviation))
            if not team:
                db.add(
                    Team(
                        league_id=league.id,
                        provider_key=abbreviation,
                        abbreviation=abbreviation,
                        name=name,
                        city=city,
                        conference=conference,
                        division=division,
                    )
                )

        pool = db.scalar(select(SurvivorPool).where(SurvivorPool.name == "Demo LMS Pool"))
        if not pool:
            db.add(
                SurvivorPool(
                    name="Demo LMS Pool",
                    season_id=season.id,
                    tie_eliminates=True,
                    allow_reuse=False,
                    buybacks_allowed=False,
                    picks_per_week=1,
                )
            )

        run.status = "success"
        run.records_written = 32
        from datetime import datetime, timezone
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info("NFL and LMS foundation seeded")
        return {"status": "success", "teams": 32}
    finally:
        db.close()
