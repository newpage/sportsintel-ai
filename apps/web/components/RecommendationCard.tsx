import Link from "next/link";

export type Recommendation = {
  team?: string;
  abbreviation?: string;
  opponent?: string;
  matchup?: string;
  selection?: string;
  edge: number;
  confidence: number;
  risk: string;
  label?: string;
  trend: number;
  summary: string;
  evidence?: string[];
};

function tone(edge: number) {
  if (edge >= 90) return "elite";
  if (edge >= 84) return "strong";
  if (edge >= 76) return "consider";
  return "risky";
}

export function RecommendationCard({ item, compact = false }: { item: Recommendation; compact?: boolean }) {
  const title = item.team || item.selection || item.matchup || "Recommendation";
  return (
    <article className={`recommendation-card ${tone(item.edge)} ${compact ? "compact-card" : ""}`}>
      <div className="recommendation-head">
        <div><span className="recommendation-kicker">{item.matchup || (item.opponent ? `${item.abbreviation} vs ${item.opponent}` : "SportsIntel analysis")}</span><h3>{title}</h3></div>
        <div className="edge-score"><strong>{item.edge}</strong><span>Edge</span></div>
      </div>
      <div className="recommendation-meta">
        <span className={`signal ${tone(item.edge)}`}>{item.label || (item.edge >= 84 ? "Strong" : "Consider")}</span>
        <span>Confidence {item.confidence}%</span>
        <span>Risk {item.risk}</span>
        <span className={item.trend >= 0 ? "trend-up" : "trend-down"}>{item.trend >= 0 ? "↑" : "↓"} {Math.abs(item.trend)}</span>
      </div>
      <div className="confidence-track"><span style={{ width: `${item.confidence}%` }} /></div>
      <p>{item.summary}</p>
      {!compact && item.evidence && <ul className="evidence-list">{item.evidence.slice(0, 3).map(value => <li key={value}>{value}</li>)}</ul>}
      <div className="card-actions"><Link href="/survivor">Why</Link><Link href="/survivor#compare">Compare</Link></div>
    </article>
  );
}
