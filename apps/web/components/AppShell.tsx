"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

const navigation = [
  ["/today", "Today", "◉"],
  ["/survivor", "Survivor", "◆"],
  ["/spread", "Spread", "↔"],
  ["/totals", "Totals", "∑"],
  ["/teams", "Teams", "◫"],
  ["/games", "Games", "▦"],
  ["/assistant", "Assistant", "✦"],
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/today">
          <span className="brand-mark">SI</span>
          <span><strong>SportsIntel</strong><small>Smarter NFL decisions</small></span>
        </Link>
        <nav className="app-nav">
          {navigation.map(([href, label, icon]) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return <Link className={active ? "active" : ""} href={href} key={href}><span>{icon}</span>{label}</Link>;
          })}
        </nav>
        <div className="sidebar-footer">
          <Link href="/admin">Admin Console</Link>
          <Link href="/">Public site</Link>
        </div>
      </aside>
      <section className="app-stage">
        <header className="topbar">
          <div><span className="live-dot" /> NFL 2026 · Week 1</div>
          <div className="topbar-actions"><span>Launch model</span><a href="/login">Account</a></div>
        </header>
        <div className="app-content">{children}</div>
      </section>
    </div>
  );
}
