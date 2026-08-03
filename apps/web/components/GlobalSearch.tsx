"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { apiFetch } from "../lib/api";

type SearchResult = {
  type: "TEAM" | "GAME";
  key: string;
  title: string;
  subtitle: string;
  href: string;
};

export function GlobalSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    if (query.trim().length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }
    timer.current = setTimeout(async () => {
      try {
        const data = await apiFetch(`/v1/search?q=${encodeURIComponent(query)}`);
        setResults(data.results || []);
        setOpen(true);
      } catch {
        setResults([]);
      }
    }, 180);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [query]);

  return (
    <div className="global-search">
      <span>⌕</span>
      <input
        aria-label="Search teams and games"
        onChange={(event) => setQuery(event.target.value)}
        onFocus={() => results.length && setOpen(true)}
        placeholder="Search teams or games"
        value={query}
      />
      {open && (
        <div className="search-results">
          {results.length ? results.map((result) => (
            <Link href={result.href} key={`${result.type}-${result.key}`} onClick={() => setOpen(false)}>
              <b>{result.type}</b>
              <span><strong>{result.title}</strong><small>{result.subtitle}</small></span>
            </Link>
          )) : <div className="search-empty">No matching teams or games.</div>}
        </div>
      )}
    </div>
  );
}
