"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "../../components/AppShell";
import { apiFetch } from "../../lib/api";

type WatchItem = {
  id: number;
  entity_type: "TEAM" | "GAME";
  entity_key: string;
  label: string;
  created_at: string;
  detail?: any;
};

export default function WatchlistPage() {
  const [items, setItems] = useState<WatchItem[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const data = await apiFetch("/v1/watchlist");
      setItems(data.items || []);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function remove(id: number) {
    await apiFetch(`/v1/watchlist/${id}`, { method: "DELETE" });
    setItems((current) => current.filter((item) => item.id !== id));
  }

  return (
    <AppShell>
      <div className="page-heading"><div><span className="page-kicker">Personal intelligence</span><h1>Watchlist</h1><p>Keep your highest-priority teams and games in one decision workspace.</p></div><div className="week-chip"><strong>{items.length}</strong><br />watched items</div></div>
      {loading && <div className="loading-panel">Loading watchlist…</div>}
      {!loading && !items.length && <div className="empty-watchlist"><strong>Your watchlist is empty.</strong><p>Add teams from Team Intelligence or return to the game board.</p><div className="actions"><Link href="/teams">Browse teams</Link><Link className="secondary" href="/games">Browse games</Link></div></div>}
      <div className="watchlist-grid">
        {items.map((item) => {
          const href = item.entity_type === "TEAM" ? `/teams/${item.entity_key.toLowerCase()}` : `/games/${item.entity_key}`;
          return <article className="watchlist-card" key={item.id}><div><span>{item.entity_type}</span><h2>{item.label}</h2><p>{item.entity_type === "TEAM" ? `Current rating ${item.detail?.rating ?? "—"} · ${item.detail?.conference ?? "NFL"} ${item.detail?.division ?? ""}` : item.detail?.headline ?? "Game intelligence monitored."}</p></div><div className="watchlist-card-actions"><Link href={href}>Open intelligence</Link><button onClick={() => remove(item.id)}>Remove</button></div></article>;
        })}
      </div>
    </AppShell>
  );
}
