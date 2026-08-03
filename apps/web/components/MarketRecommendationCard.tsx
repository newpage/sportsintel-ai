import Link from "next/link";
import { ConfidenceBar } from "./ConfidenceBar";
import { EdgeBadge } from "./EdgeBadge";

export type MarketRecommendation = {
  rank: number;
  strategy: "SPREAD" | "TOTAL";
  game_slug: string;
  matchup: string;
  selection: string;
  edge: number;
  confidence: number;
  risk: string;
  trend: number;
  label: string;
  summary: string;
  evidence: string[];
  warnings: string[];
  market_movement: number;
  edge_points: number;
  line?: number;
  market_total: number;
  projected_total?: number;
  direction?: string;
  weather: string;
  wind_mph: number;
};

export function MarketRecommendationCard({ item, selected, onSelect }: { item: MarketRecommendation; selected?: boolean; onSelect?: () => void }) {
  return <article className={`market-recommendation-card ${selected ? "selected" : ""}`}>
    <button className="market-rank" onClick={onSelect} aria-pressed={selected}><span>#{item.rank}</span><small>{selected ? "Selected" : "Compare"}</small></button>
    <div className="market-card-main">
      <div className="market-card-heading"><div><span className="recommendation-kicker">{item.matchup}</span><h2>{item.selection}</h2><div className="market-badges"><span className={`signal ${item.edge >= 84 ? "strong" : "consider"}`}>{item.label}</span><span>Risk {item.risk}</span><span className={item.trend >= 0 ? "trend-up" : "trend-down"}>{item.trend >= 0 ? "↑" : "↓"} {Math.abs(item.trend)}</span></div></div><EdgeBadge edge={item.edge} /></div>
      <ConfidenceBar value={item.confidence} />
      <p className="market-summary">{item.summary}</p>
      <div className="market-facts"><div><span>Model edge</span><strong>{item.edge_points} pts</strong></div><div><span>Market</span><strong>{item.strategy === "SPREAD" ? item.line : item.market_total}</strong></div><div><span>{item.strategy === "TOTAL" ? "Projection" : "Movement"}</span><strong>{item.strategy === "TOTAL" ? item.projected_total : `${item.market_movement > 0 ? "+" : ""}${item.market_movement}`}</strong></div><div><span>Environment</span><strong>{item.weather}</strong></div></div>
      <div className="market-evidence"><div><h3>Why it rates</h3><ul>{item.evidence.map(value => <li key={value}>{value}</li>)}</ul></div><div><h3>Risks</h3>{item.warnings.length ? <ul className="warning-list">{item.warnings.map(value => <li key={value}>{value}</li>)}</ul> : <p>No major launch-model warnings.</p>}</div></div>
      <div className="card-actions"><Link href={`/games/${item.game_slug}`}>Game intelligence</Link><button onClick={onSelect}>{selected ? "Remove comparison" : "Compare"}</button></div>
    </div>
  </article>;
}
