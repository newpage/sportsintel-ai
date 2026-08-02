"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "../../components/AppShell";
import { apiFetch } from "../../lib/api";

type Team = { abbreviation: string; name: string };
type Game = {
  slug: string;
  away: Team;
  home: Team;
  kickoff_day: string;
  kickoff_time: string;
  venue: string;
  spread: number;
  total: number;
  weather: string;
  headline: string;
  game_edge: number;
  top_strategy: string;
  survivor?: { edge: number; confidence: number };
  spread_signal?: { selection: string; edge: number };
  total_signal?: { selection: string; edge: number };
};

export default function GamesPage() {
  const [games, setGames] = useState<Game[]>([]);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("ALL");

  useEffect(() => {
    apiFetch("/v1/games")
      .then(result => setGames(result.games))
      .catch(err => setError(err instanceof Error ? err.message : "Unable to load games"));
  }, []);

  const filtered = filter === "ALL" ? games : games.filter(game => game.top_strategy.toUpperCase() === filter);

  return (
    <AppShell>
      <div className="page-heading">
        <div><span className="page-kicker">NFL Week 1</span><h1>Game Intelligence</h1><p>Every matchup, market signal, weather condition, and strategy edge in one workspace.</p></div>
        <div className="week-chip">{games.length} matchups analyzed</div>
      </div>
      <div className="toolbar">
        <div className="filter-group">
          {["ALL", "SURVIVOR", "SPREAD", "TOTAL"].map(value => <button className={filter === value ? "active" : ""} key={value} onClick={() => setFilter(value)}>{value === "ALL" ? "All games" : value}</button>)}
        </div>
        <span>Sorted by combined SportsIntel Edge</span>
      </div>
      {error ? <div className="page-error"><h1>Unable to load games</h1><p>{error}</p></div> :
        <div className="game-board">{filtered.map(game => <Link className="game-board-card" href={`/games/${game.slug}`} key={game.slug}>
          <div className="game-board-top"><span>{game.kickoff_day} · {game.kickoff_time}</span><b>{game.game_edge} <small>Game Edge</small></b></div>
          <div className="matchup-line"><div><strong>{game.away.abbreviation}</strong><span>{game.away.name}</span></div><em>at</em><div><strong>{game.home.abbreviation}</strong><span>{game.home.name}</span></div></div>
          <p>{game.headline}</p>
          <div className="game-market"><span>Spread <strong>{game.home.abbreviation} {game.spread > 0 ? "+" : ""}{game.spread}</strong></span><span>Total <strong>{game.total}</strong></span><span>Weather <strong>{game.weather}</strong></span></div>
          <div className="game-signals">
            <span className="signal strong">Best: {game.top_strategy}</span>
            {game.survivor && <span>Survivor {game.survivor.edge}</span>}
            {game.spread_signal && <span>Spread {game.spread_signal.edge}</span>}
            {game.total_signal && <span>Total {game.total_signal.edge}</span>}
          </div>
        </Link>)}</div>}
    </AppShell>
  );
}
