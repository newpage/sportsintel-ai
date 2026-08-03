"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "../../../components/AppShell";
import { RecommendationCard } from "../../../components/RecommendationCard";
import { Widget } from "../../../components/Widget";
import { WatchlistButton } from "../../../components/WatchlistButton";
import { apiFetch } from "../../../lib/api";

type GameDetail = any;

export default function GameDetailPage() {
  const params = useParams<{ slug: string }>();
  const [game, setGame] = useState<GameDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!params.slug) return;
    apiFetch(`/v1/games/${params.slug}`)
      .then(setGame)
      .catch(err => setError(err instanceof Error ? err.message : "Unable to load game"));
  }, [params.slug]);

  return <AppShell>{error ? <div className="page-error"><h1>Unable to load game</h1><p>{error}</p></div> : !game ? <div className="skeleton-shell"><div/><div/><div/></div> : <>
    <div className="game-hero">
      <div className="game-hero-nav"><Link href="/games">← All games</Link><div><WatchlistButton entityType="GAME" entityKey={game.slug} label={`${game.away.abbreviation} at ${game.home.abbreviation}`} /><span>NFL Week {game.week} · {game.status}</span></div></div>
      <div className="game-matchup-hero">
        <TeamBlock team={game.away} label="Away" />
        <div className="game-kickoff"><span>{game.kickoff.day}</span><strong>{game.kickoff.time}</strong><small>{game.kickoff.venue}<br/>{game.kickoff.city}</small></div>
        <TeamBlock team={game.home} label="Home" />
      </div>
      <div className="game-verdict"><div><span>SportsIntel Game Edge</span><strong>{game.game_edge}</strong></div><div><span>Confidence</span><strong>{game.confidence}%</strong></div><div><span>Risk</span><strong>{game.risk}</strong></div><p>{game.headline}</p></div>
    </div>

    <div className="metric-strip game-metrics">
      <Metric label="Home spread" value={`${game.home.abbreviation} ${game.market.home_spread > 0 ? "+" : ""}${game.market.home_spread}`} />
      <Metric label="Game total" value={game.market.total} />
      <Metric label="Weather" value={game.weather.summary} />
      <Metric label="Away travel" value={`${game.context.away_travel_miles.toLocaleString()} mi`} />
    </div>

    <div className="game-detail-grid">
      <Widget title="Strategy signals" eyebrow="Decision support" className="span-2">
        <div className="strategy-signal-grid">
          {game.strategies.survivor ? <RecommendationCard item={game.strategies.survivor} /> : <EmptySignal title="Survivor" />}
          {game.strategies.spread ? <RecommendationCard item={game.strategies.spread} /> : <EmptySignal title="Spread" />}
          {game.strategies.total ? <RecommendationCard item={game.strategies.total} /> : <EmptySignal title="Total" />}
        </div>
      </Widget>
      <Widget title="Matchup context" eyebrow="Current conditions">
        <div className="context-list"><Context label="Weather impact" value={game.weather.impact}/><Context label="Temperature" value={`${game.weather.temperature_f}°F`}/><Context label="Wind" value={`${game.weather.wind_mph} mph`}/><Context label="Roof" value={game.weather.roof}/><Context label="Rest edge" value={`${game.context.rest_edge > 0 ? "+" : ""}${game.context.rest_edge} days`}/><Context label="Injury edge" value={game.context.injury_edge}/></div>
      </Widget>
      <Widget title="Why the model moved" eyebrow="Evidence" className="span-2">
        <div className="factor-list">{game.factors.map((factor: any) => <div className={`factor-row ${factor.tone.toLowerCase()}`} key={factor.code}><div><strong>{factor.label}</strong><p>{factor.detail}</p></div><span>{factor.impact > 0 ? "+" : ""}{factor.impact}</span></div>)}</div>
      </Widget>
      <Widget title="Intelligence timeline" eyebrow="What changed">
        <div className="timeline">{game.timeline.map((event: any) => <div className="timeline-row" key={`${event.type}-${event.at}`}><span className={event.direction === "UP" ? "change-up" : event.direction === "DOWN" ? "change-down" : "change-flat"}>{event.direction === "UP" ? "↑" : event.direction === "DOWN" ? "↓" : "•"}</span><div><small>{new Date(event.at).toLocaleString([], {weekday:"short", hour:"numeric", minute:"2-digit"})} · {event.type}</small><strong>{event.title}</strong><p>{event.detail}</p></div></div>)}</div>
      </Widget>
      <Widget title="Ask SportsIntel" eyebrow="Quick questions" className="span-3"><div className="question-grid">{game.assistant_questions.map((question: string) => <button key={question}>{question}<span>→</span></button>)}</div></Widget>
    </div>
  </>}</AppShell>;
}

function TeamBlock({ team, label }: { team: any; label: string }) { return <div className="team-hero-block"><span>{label}</span><Link href={`/teams/${team.abbreviation.toLowerCase()}`}><strong>{team.abbreviation}</strong><h2>{team.name}</h2></Link><small>{team.conference} {team.division}</small></div>; }
function Metric({ label, value }: { label: string; value: string | number }) { return <div className="metric"><span>{label}</span><strong>{value}</strong></div>; }
function Context({ label, value }: { label: string; value: string | number }) { return <div><span>{label}</span><strong>{value}</strong></div>; }
function EmptySignal({ title }: { title: string }) { return <div className="empty-signal"><span>{title}</span><strong>Monitoring</strong><p>No launch-model edge is published for this strategy yet.</p></div>; }
