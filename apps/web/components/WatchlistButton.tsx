"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

export function WatchlistButton({
  entityType,
  entityKey,
  label,
}: {
  entityType: "TEAM" | "GAME";
  entityKey: string;
  label: string;
}) {
  const [itemId, setItemId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    apiFetch("/v1/watchlist")
      .then((data) => {
        const item = (data.items || []).find(
          (entry: { entity_type: string; entity_key: string; id: number }) =>
            entry.entity_type === entityType && entry.entity_key === entityKey,
        );
        setItemId(item?.id || null);
      })
      .catch(() => undefined);
  }, [entityKey, entityType]);

  async function toggle() {
    setBusy(true);
    try {
      if (itemId) {
        await apiFetch(`/v1/watchlist/${itemId}`, { method: "DELETE" });
        setItemId(null);
      } else {
        const item = await apiFetch("/v1/watchlist", {
          method: "POST",
          body: JSON.stringify({
            entity_type: entityType,
            entity_key: entityKey,
            label,
          }),
        });
        setItemId(item.id);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <button className={`watch-button ${itemId ? "active" : ""}`} disabled={busy} onClick={toggle}>
      {itemId ? "★ Watching" : "☆ Watch"}
    </button>
  );
}
