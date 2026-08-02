"use client";

import { useEffect, useMemo, useState } from "react";
import { AppShell } from "../../components/AppShell";
import { Recommendation, RecommendationCard } from "../../components/RecommendationCard";
import { apiFetch } from "../../lib/api";

type SurvivorItem = Recommendation & { win_probability: number; future_value: number; public_pick: number; warnings: string[]; abbreviation: string };

export default function SurvivorPage() {
  const [items, setItems] = useState<SurvivorItem[]>([]);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<string[]>(["BUF", "SEA"]);
  const [risk, setRisk] = useState("ALL");

  useEffect(() => { apiFetch("/v1/survivor/recommendations").then(result => setItems(result.recommendations)).catch(err => setError(err instanceof Error ? err.message : "Unable to load survivor recommendations")); }, []);
  const filtered = risk === "ALL" ? items : items.filter(item => item.risk === risk);
  const compared = useMemo(() => selected.map(code => items.find(item => item.abbreviation === code)).filter(Boolean) as SurvivorItem[], [items, selected]);

  function toggle(code: string) { setSelected(current => current.includes(code) ? current.filter(item => item !== code) : current.length < 2 ? [...current, code] : [current[1], code]); }

  return <AppShell>{error ? <div className="page-error"><h1>Unable to load Survivor</h1><p>{error}</p></div> : <>
    <div className="page-heading"><div><span className="page-kicker">Last Man Standing</span><h1>Survivor Center</h1><p>Balance immediate survival probability with the cost of using valuable teams too early.</p></div><div className="week-chip">NFL Week 1</div></div>
    <div className="toolbar"><div className="filter-group"><button className={risk === "ALL" ? "active" : ""} onClick={() => setRisk("ALL")}>All</button><button className={risk === "LOW" ? "active" : ""} onClick={() => setRisk("LOW")}>Low risk</button><button className={risk === "MEDIUM" ? "active" : ""} onClick={() => setRisk("MEDIUM")}>Medium risk</button></div><span>Select two teams to compare</span></div>
    <div className="survivor-layout"><section className="ranking-list">{filtered.map((item, index) => <div className={`ranked-card ${selected.includes(item.abbreviation) ? "selected" : ""}`} key={item.abbreviation}><button className="rank-select" onClick={() => toggle(item.abbreviation)}><span>#{index + 1}</span><span>{selected.includes(item.abbreviation) ? "Selected" : "Compare"}</span></button><RecommendationCard item={item} /><div className="survivor-factors"><Factor label="Win probability" value={`${item.win_probability}%`} /><Factor label="Future value" value={item.future_value} /><Factor label="Public pick" value={`${item.public_pick}%`} /></div>{item.warnings.length > 0 && <div className="warnings"><strong>Watch:</strong> {item.warnings.join(" · ")}</div>}</div>)}</section>
      <aside className="compare-panel" id="compare"><span className="page-kicker">Side-by-side</span><h2>Compare teams</h2>{compared.length < 2 ? <p>Select two teams from the rankings.</p> : <><div className="compare-head"><strong>{compared[0].abbreviation}</strong><span>vs</span><strong>{compared[1].abbreviation}</strong></div><CompareRow label="Edge" a={compared[0].edge} b={compared[1].edge}/><CompareRow label="Confidence" a={`${compared[0].confidence}%`} b={`${compared[1].confidence}%`}/><CompareRow label="Win probability" a={`${compared[0].win_probability}%`} b={`${compared[1].win_probability}%`}/><CompareRow label="Future value" a={compared[0].future_value} b={compared[1].future_value}/><CompareRow label="Projected public" a={`${compared[0].public_pick}%`} b={`${compared[1].public_pick}%`}/><div className="comparison-summary"><strong>SportsIntel view</strong><p>{compared[0].edge >= compared[1].edge ? compared[0].summary : compared[1].summary}</p></div></>}</aside>
    </div>
  </>}</AppShell>;
}
function Factor({ label, value }: { label: string; value: string | number }) { return <div><span>{label}</span><strong>{value}</strong></div>; }
function CompareRow({ label, a, b }: { label: string; a: string | number; b: string | number }) { return <div className="compare-row"><span>{a}</span><small>{label}</small><span>{b}</span></div>; }
