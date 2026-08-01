from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class League(Base):
    __tablename__ = "leagues"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    sport: Mapped[str] = mapped_column(String(50))


class Season(Base):
    __tablename__ = "seasons"
    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    phase: Mapped[str] = mapped_column(String(30), default="REGULAR")
    __table_args__ = (UniqueConstraint("league_id", "year", "phase"),)


class Week(Base):
    __tablename__ = "weeks"
    id: Mapped[int] = mapped_column(primary_key=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(50))
    __table_args__ = (UniqueConstraint("season_id", "number"),)


class Venue(Base):
    __tablename__ = "venues"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider_key: Mapped[str | None] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(50))
    roof_type: Mapped[str | None] = mapped_column(String(30))
    surface: Mapped[str | None] = mapped_column(String(50))


class Team(Base):
    __tablename__ = "teams"
    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), index=True)
    provider_key: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    abbreviation: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(100))
    conference: Mapped[str] = mapped_column(String(10))
    division: Mapped[str] = mapped_column(String(20))


class Player(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider_key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), index=True)
    full_name: Mapped[str] = mapped_column(String(150))
    position: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str | None] = mapped_column(String(40))


class Game(Base):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider_key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("weeks.id"), index=True)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    venue_id: Mapped[int | None] = mapped_column(ForeignKey("venues.id"))
    kickoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(30), default="SCHEDULED")
    home_score: Mapped[int | None] = mapped_column(Integer)
    away_score: Mapped[int | None] = mapped_column(Integer)
