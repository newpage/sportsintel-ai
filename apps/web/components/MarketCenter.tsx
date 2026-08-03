"use client";

import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../lib/api";
import { AppShell } from "./AppShell";
import { MarketRecommendation, MarketRecommendationCard } from "./MarketRecommendationCard";

type CenterData = {
  strategy: "SPREAD" | "TOTAL";
  season: number;
  week: number;
  title: string;
  subtitle: string;
  last_updated: string;
  data_mode: string;
  summary: { opportunities: number; average_confidence: number; strong_signals: number; low_risk: number; biggest_mover?: string };
  filters: string[];
  recommendations: MarketRecommendation[];
};

export function MarketCenter({ endpoint }: { endpoint: "/v1/spread" | "/v1/totals" }) {
  const [data, setData] = useState<CenterData | null>(null);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("ALL");
  const [selected, setSelected] = useState<MarketRecommendation[]>([]);

  useEffect(() => { apiFetch(endpoint).then(setData).catch(err => setError(err instanceof Error ? err.message : "Unable to load market intelligence")); }, [endpoint]);

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.recommendations.filter(item => {
      if (filter === "ALL") return true;
      if (filter === "LOW_RISK") return item.risk === "LOW";
      if (filter === "MOVERS") return Math.abs(item.trend) >= 2;
      if (filter === "OVER" || filter === "UNDER") return item.direction === filter;
      if (filter === "HOME_FAVORITES") return item.strategy === "SPREAD" && item.line !== undefined && item.line < 0;
      return true;
    });
  }, [data, filter]);

  function toggle(item: MarketRecommendation) {
    setSelected(current => current.some(value => value.game_slug === item.game_slug) ? current.filter(value => value.game_slug !== item.game_slug) : current.length >= 2 ? [current[1], item] : [...current, item]);
  }

  return <AppShell>{error ? <div className="page-error"><h1>Unable to load recommendations</h1><p>{error}</p></div> : !data ? <div className="skeleton-shell"><div/><div/><div/></div> : <>
    <div className="page-heading"><div><span className="page-kicker">NFL Week {data.week} · {data.data_mode}</span><h1>{data.title}</h1><p>{data.subtitle}</p></div><div className="update-stamp">Updated<br/><strong>{new Date(data.last_updated).toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"})}</strong></div></div>
    <div className="metric-strip market-metric-strip"><Metric label="Opportunities" value={data.summary.opportunities}/><Metric label="Strong signals" value={data.summary.strong_signals}/><Metric label="Low risk" value={data.summary.low_risk}/><Metric label="Avg confidence" value={`${data.summary.average_confidence}%`}/></div>
    <div className="toolbar"><div className="filter-group">{data.filters.map(value => <button className={filter === value ? "active" : ""} key={value} onClick={() => setFilter(value)}>{value.replaceAll("_", " ")}</button>)}</div><span>{data.summary.biggest_mover ? `Biggest mover: ${data.summary.biggest_mover}` : "Launch-model rankings"}</span></div>
    <div className="market-center-layout"><section className="market-list">{filtered.map(item => <MarketRecommendationCard item={item} key={item.selection} selected={selected.some(value => value.game_slug === item.game_slug)} onSelect={() => toggle(item)}/>)}</section><aside className="market-compare"><span className="page-kicker">Comparison</span><h2>{selected.length === 2 ? "Side by side" : "Select two signals"}</h2>{selected.length === 2 ? <Comparison left={selected[0]} right={selected[1]}/> : <p>Use Compare on any two recommendations to inspect Edge, confidence, market value and risk.</p>}</aside></div>
  </>}</AppShell>;
}

function Metric({ label, value }: { label: string; value: string | number }) { return <div className="metric"><span>{label}</span><strong>{value}</strong></div>; }
function Comparison({ left, right }: { left: MarketRecommendation; right: MarketRecommendation }) { return <div className="market-comparison"><div className="compare-head"><strong>{left.selection}</strong><span>vs</span><strong>{right.selection}</strong></div><Row label="Edge" left={left.edge} right={right.edge}/><Row label="Confidence" left={`${left.confidence}%`} right={`${right.confidence}%`}/><Row label="Model edge" left={`${left.edge_points} pts`} right={`${right.edge_points} pts`}/><Row label="Risk" left={left.risk} right={right.risk}/><Row label="Trend" left={`${left.trend >= 0 ? "+" : ""}${left.trend}`} right={`${right.trend >= 0 ? "+" : ""}${right.trend}`}/><p className="comparison-summary">{left.edge === right.edge ? "The signals are evenly rated; use risk and market context as the tiebreaker." : `${left.edge > right.edge ? left.selection : right.selection} currently carries the stronger SportsIntel Edge.`}</p></div>; }
function Row({ label, left, right }: { label: string; left: string | number; right: string | number }) { return <div className="compare-row"><span>{left}</span><small>{label}</small><span>{right}</span></div>; }
