from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SurvivorPool(Base):
    __tablename__ = "survivor_pools"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), index=True)
    tie_eliminates: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_reuse: Mapped[bool] = mapped_column(Boolean, default=False)
    buybacks_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    picks_per_week: Mapped[int] = mapped_column(Integer, default=1)


class SurvivorEntry(Base):
    __tablename__ = "survivor_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("survivor_pools.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")


class SurvivorPick(Base):
    __tablename__ = "survivor_picks"
    id: Mapped[int] = mapped_column(primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("survivor_entries.id"), index=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("weeks.id"), index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    result: Mapped[str] = mapped_column(String(30), default="PENDING")
    __table_args__ = (UniqueConstraint("entry_id", "week_id"),)


class SurvivorRecommendation(Base):
    __tablename__ = "survivor_recommendations"
    id: Mapped[int] = mapped_column(primary_key=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("weeks.id"), index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    strategy_mode: Mapped[str] = mapped_column(String(30), default="BALANCED")
    win_probability: Mapped[float] = mapped_column(Float)
    future_value_score: Mapped[float] = mapped_column(Float)
    public_pick_estimate: Mapped[float | None] = mapped_column(Float)
    recommendation_score: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str | None] = mapped_column(String(1000))
