"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AppShell } from "../../components/AppShell";
import { ConfidenceBar } from "../../components/ConfidenceBar";
import { WatchlistButton } from "../../components/WatchlistButton";
import { apiFetch } from "../../lib/api";

type Team = {
  abbreviation: string;
  name: string;
  city: string;
  conference: string;
  division: string;
  rating: number;
  trend: number;
  risk: string;
  survivor_edge?: number;
  spread_edge?: number;
  total_edge?: number;
  game_slug?: string;
  opponent?: string;
  location?: string;
};

export default function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [conference, setConference] = useState("ALL");
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch("/v1/teams")
      .then((data) => setTeams(data.teams || []))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load teams"));
  }, []);

  const filtered = useMemo(() => teams.filter((team) => {
    const matchesConference = conference === "ALL" || team.conference === conference;
    const needle = query.trim().toLowerCase();
    const matchesQuery = !needle || team.name.toLowerCase().includes(needle) || team.abbreviation.toLowerCase().includes(needle);
    return matchesConference && matchesQuery;
  }), [conference, query, teams]);

  return (
    <AppShell>
      <div className="page-heading">
        <div><span className="page-kicker">NFL intelligence</span><h1>Teams</h1><p>Compare current SportsIntel ratings, strategy edges, risk, and upcoming matchup context across the league.</p></div>
        <div className="week-chip"><strong>{teams.length}</strong><br />teams loaded</div>
      </div>

      <div className="team-toolbar">
        <input placeholder="Filter teams" value={query} onChange={(event) => setQuery(event.target.value)} />
        <div>
          {["ALL", "AFC", "NFC"].map((value) => <button className={conference === value ? "active" : ""} key={value} onClick={() => setConference(value)}>{value}</button>)}
        </div>
      </div>

      {error && <div className="error">{error}</div>}
      {!teams.length && !error && <div className="loading-panel">Loading team intelligence…</div>}

      <div className="team-grid">
        {filtered.map((team) => (
          <article className="team-card" key={team.abbreviation}>
            <div className="team-card-head">
              <div><span>{team.conference} {team.division}</span><h2>{team.abbreviation}</h2><p>{team.name}</p></div>
              <div className="team-rating"><strong>{team.rating}</strong><span>Rating</span></div>
            </div>
            <ConfidenceBar value={Math.min(97, Math.max(60, team.rating + 3))} />
            <div className="team-edge-grid">
              <div><span>Survivor</span><strong>{team.survivor_edge ?? "—"}</strong></div>
              <div><span>Spread</span><strong>{team.spread_edge ?? "—"}</strong></div>
              <div><span>Total</span><strong>{team.total_edge ?? "—"}</strong></div>
            </div>
            <div className="team-next-game">
              <span>Next matchup</span>
              <strong>{team.location === "HOME" ? "vs" : "at"} {team.opponent || "TBD"}</strong>
              <small className={team.trend >= 0 ? "trend-up" : "trend-down"}>{team.trend >= 0 ? "↑" : "↓"} {Math.abs(team.trend)} trend</small>
            </div>
            <div className="team-card-actions">
              <Link href={`/teams/${team.abbreviation.toLowerCase()}`}>Team intelligence</Link>
              {team.game_slug && <Link href={`/games/${team.game_slug}`}>Game</Link>}
              <WatchlistButton entityType="TEAM" entityKey={team.abbreviation} label={team.name} />
            </div>
          </article>
        ))}
      </div>
    </AppShell>
  );
}
