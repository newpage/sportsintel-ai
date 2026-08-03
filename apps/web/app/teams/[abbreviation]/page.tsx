"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "../../../components/AppShell";
import { ConfidenceBar } from "../../../components/ConfidenceBar";
import { WatchlistButton } from "../../../components/WatchlistButton";
import { Widget } from "../../../components/Widget";
import { apiFetch } from "../../../lib/api";

type TeamDetail = {
  abbreviation: string;
  name: string;
  conference: string;
  division: string;
  rating: number;
  trend: number;
  risk: string;
  headline: string;
  survivor?: {
    edge: number;
    confidence: number;
    future_value: number;
    win_probability: number;
    summary: string;
    evidence: string[];
    warnings: string[];
  };
  factors: { label: string; score: number; tone: string }[];
  upcoming_game?: {
    slug: string;
    opponent: string;
    location: string;
    kickoff_day: string;
    kickoff_time: string;
    venue: string;
    weather: string;
    spread: number;
    total: number;
  };
  assistant_questions: string[];
};

export default function TeamDetailPage() {
  const params = useParams<{ abbreviation: string }>();
  const [team, setTeam] = useState<TeamDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch(`/v1/teams/${params.abbreviation}`)
      .then(setTeam)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load team"));
  }, [params.abbreviation]);

  return (
    <AppShell>
      {error && <div className="error">{error}</div>}
      {!team && !error && <div className="loading-panel">Loading team intelligence…</div>}
      {team && <>
        <div className="team-detail-hero">
          <div><Link href="/teams">← All teams</Link><span className="page-kicker">{team.conference} {team.division}</span><h1>{team.abbreviation}</h1><h2>{team.name}</h2><p>{team.headline}</p></div>
          <div className="team-detail-score"><strong>{team.rating}</strong><span>SportsIntel rating</span><small className={team.trend >= 0 ? "trend-up" : "trend-down"}>{team.trend >= 0 ? "↑" : "↓"} {Math.abs(team.trend)} this week</small><WatchlistButton entityType="TEAM" entityKey={team.abbreviation} label={team.name} /></div>
        </div>

        <div className="metric-strip">
          <div className="metric"><span>Risk</span><strong>{team.risk}</strong></div>
          <div className="metric"><span>Survivor edge</span><strong>{team.survivor?.edge ?? "—"}</strong></div>
          <div className="metric"><span>Win probability</span><strong>{team.survivor ? `${team.survivor.win_probability}%` : "—"}</strong></div>
          <div className="metric"><span>Future value</span><strong>{team.survivor?.future_value ?? "—"}</strong></div>
        </div>

        <div className="team-detail-grid">
          <Widget title="Team profile" status="Current">
            <div className="team-factor-list">{team.factors.map((factor) => <div key={factor.label}><span>{factor.label}</span><strong>{factor.score}</strong><ConfidenceBar value={factor.score} /></div>)}</div>
          </Widget>
          <Widget title="Upcoming game" status="Week 1">
            {team.upcoming_game ? <div className="upcoming-team-game"><strong>{team.upcoming_game.location === "HOME" ? "vs" : "at"} {team.upcoming_game.opponent}</strong><span>{team.upcoming_game.kickoff_day} · {team.upcoming_game.kickoff_time}</span><p>{team.upcoming_game.venue}</p><div><b>Spread {team.upcoming_game.spread > 0 ? "+" : ""}{team.upcoming_game.spread}</b><b>Total {team.upcoming_game.total}</b></div><small>{team.upcoming_game.weather}</small><Link href={`/games/${team.upcoming_game.slug}`}>Open Game Intelligence →</Link></div> : <p>No upcoming game loaded.</p>}
          </Widget>
          <Widget title="Survivor evidence" status={team.survivor ? `${team.survivor.confidence}% confidence` : "Pending"}>
            {team.survivor ? <><p>{team.survivor.summary}</p><ul className="evidence-list">{team.survivor.evidence.map((item) => <li key={item}>{item}</li>)}</ul>{team.survivor.warnings.length > 0 && <div className="team-warning">Risks: {team.survivor.warnings.join(" · ")}</div>}</> : <p>No current Survivor recommendation.</p>}
          </Widget>
          <Widget title="Ask SportsIntel" status="Suggested">
            <div className="question-grid">{team.assistant_questions.map((question) => <Link href={`/assistant?q=${encodeURIComponent(question)}`} key={question}>{question}</Link>)}</div>
          </Widget>
        </div>
      </>}
    </AppShell>
  );
}
