"use client";

import { useEffect, useState } from "react";
import { AppShell } from "../../components/AppShell";
import { Recommendation, RecommendationCard } from "../../components/RecommendationCard";
import { Widget } from "../../components/Widget";
import { apiFetch } from "../../lib/api";

type TodayData = {
  season: number;
  week: number;
  last_updated: string;
  data_mode: string;
  changes: { type: string; direction: string; entity: string; delta: number; message: string }[];
  metrics: Record<string, number>;
  survivor: Recommendation[];
  spread: Recommendation[];
  totals: Recommendation[];
  quick_questions: string[];
};

export default function TodayPage() {
  const [data, setData] = useState<TodayData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => { apiFetch("/v1/today").then(setData).catch(err => setError(err instanceof Error ? err.message : "Unable to load Today")); }, []);

  return <AppShell>{error ? <div className="page-error"><h1>Sign in required</h1><p>{error}</p><a href="/login?returnTo=/today">Sign in</a></div> : !data ? <DashboardSkeleton /> : <>
    <div className="page-heading"><div><span className="page-kicker">Morning briefing</span><h1>Today</h1><p>What changed, where the strongest edges are, and what deserves your attention.</p></div><div className="update-stamp">Updated<br/><strong>{new Date(data.last_updated).toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"})}</strong></div></div>
    <div className="metric-strip">
      <Metric label="Teams evaluated" value={data.metrics.teams_evaluated} />
      <Metric label="Active strategies" value={data.metrics.strategies_active} />
      <Metric label="Changes today" value={data.metrics.changes_today} />
      <Metric label="Avg confidence" value={`${data.metrics.average_confidence}%`} />
    </div>
    <div className="dashboard-grid">
      <Widget title="What changed" eyebrow="Intelligence feed" className="span-2"><div className="change-feed">{data.changes.map(change => <div className="change-row" key={`${change.type}-${change.entity}`}><span className={change.direction === "UP" ? "change-up" : "change-down"}>{change.direction === "UP" ? "↑" : "↓"}</span><div><strong>{change.entity}</strong><p>{change.message}</p></div><b>{change.delta > 0 ? "+" : ""}{change.delta}</b></div>)}</div></Widget>
      <Widget title="Top Survivor" eyebrow="Best current decision"><RecommendationCard item={data.survivor[0]} /></Widget>
      <Widget title="Survivor shortlist" eyebrow="Week 1"><div className="stack-list">{data.survivor.slice(1,4).map(item => <RecommendationCard compact item={item} key={item.abbreviation} />)}</div></Widget>
      <Widget title="Spread edges" eyebrow="Launch model"><div className="stack-list">{data.spread.map(item => <RecommendationCard compact item={item} key={item.selection} />)}</div></Widget>
      <Widget title="Totals edges" eyebrow="Launch model"><div className="stack-list">{data.totals.map(item => <RecommendationCard compact item={item} key={item.selection} />)}</div></Widget>
      <Widget title="SportsIntel Assistant" eyebrow="Quick analysis" className="span-2"><div className="question-grid">{data.quick_questions.map(question => <button key={question}>{question}<span>→</span></button>)}</div><p className="assistant-note">Answers are generated from current SportsIntel evidence—not generic football commentary.</p></Widget>
    </div>
  </>}</AppShell>;
}

function Metric({ label, value }: { label: string; value: string | number }) { return <div className="metric"><span>{label}</span><strong>{value}</strong></div>; }
function DashboardSkeleton() { return <div className="skeleton-shell"><div/><div/><div/><div/></div>; }
