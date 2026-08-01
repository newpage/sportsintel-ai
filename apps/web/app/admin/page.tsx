"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";

type Overview = {
  status: string;
  environment: string;
  version: string;
  services: Record<string, boolean>;
  counts: Record<string, number>;
  latest_provider_run: null | Record<string, unknown>;
};

type User = {
  id: number;
  email: string;
  display_name?: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login_at?: string;
};

export default function AdminPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      apiFetch("/v1/admin/overview"),
      apiFetch("/v1/admin/users"),
    ])
      .then(([overviewData, userData]) => {
        setOverview(overviewData);
        setUsers(userData);
      })
      .catch(err => setError(err instanceof Error ? err.message : "Unable to load admin console"));
  }, []);

  if (error) {
    return <main><section className="hero compact"><h1>Admin access required</h1><p>{error}</p><a href="/login?returnTo=/admin">Sign in as administrator</a></section></main>;
  }

  if (!overview) {
    return <main><section className="hero compact"><h1>Loading Admin Console…</h1></section></main>;
  }

  return (
    <main>
      <section className="hero compact">
        <div className="eyebrow">Operations</div>
        <h1>Admin Console</h1>
        <p>Platform health, data ingestion, user access, and operational visibility.</p>
      </section>

      <section className="status-row">
        <div className={`status-pill ${overview.status}`}>{overview.status}</div>
        <div>Environment: <strong>{overview.environment}</strong></div>
        <div>Version: <strong>{overview.version}</strong></div>
      </section>

      <section className="grid">
        {Object.entries(overview.services).map(([name, healthy]) => (
          <article key={name}>
            <div className="eyebrow">{name}</div>
            <h2>{healthy ? "Healthy" : "Attention"}</h2>
          </article>
        ))}
      </section>

      <h2 className="section-title">Platform counts</h2>
      <section className="grid">
        {Object.entries(overview.counts).map(([name, count]) => (
          <article key={name}><div className="eyebrow">{name.replaceAll("_", " ")}</div><h2>{count}</h2></article>
        ))}
      </section>

      <h2 className="section-title">Users</h2>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Email</th><th>Name</th><th>Role</th><th>Status</th><th>Last login</th></tr></thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id}>
                <td>{user.email}</td>
                <td>{user.display_name || "—"}</td>
                <td>{user.role}</td>
                <td>{user.is_active ? "Active" : "Disabled"}</td>
                <td>{user.last_login_at ? new Date(user.last_login_at).toLocaleString() : "Never"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
