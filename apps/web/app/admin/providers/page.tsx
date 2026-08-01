"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../../lib/api";

type Capability = {
  dataset: string;
  default_schedule_seconds?: number;
  description?: string;
};

type ProviderRow = {
  metadata: {
    code: string;
    name: string;
    version: string;
    stage: string;
    sports: string[];
    capabilities: Capability[];
    access_type: string;
    license_name?: string;
    attribution_required: boolean;
    commercial_use_allowed?: boolean;
    terms_url?: string;
    requires_api_key: boolean;
    self_hostable: boolean;
  };
  configuration: {
    enabled: boolean;
    priority: number;
  };
  health: {
    status: string;
    message: string;
    latency_ms?: number;
  };
  latest_execution?: {
    status: string;
    dataset: string;
    quality_score: number;
    confidence_score: number;
    records_received: number;
  };
};

export default function ProvidersPage() {
  const [providers, setProviders] = useState<ProviderRow[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      setProviders(await apiFetch("/v1/admin/providers"));
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load providers");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function toggle(code: string, enabled: boolean) {
    setMessage("");
    await apiFetch(`/v1/admin/providers/${code}/${enabled ? "disable" : "enable"}`, {
      method: "POST",
    });
    setMessage(`${code} ${enabled ? "disabled" : "enabled"}`);
    await load();
  }

  async function run(code: string, dataset: string) {
    setMessage(`Running ${code}:${dataset}…`);
    try {
      const result = await apiFetch(`/v1/admin/providers/${code}/run/${dataset}`, {
        method: "POST",
      });
      setMessage(
        `${code}:${dataset} ${result.status}; quality ${result.quality_score}%`
      );
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Provider run failed");
    }
  }

  if (error) {
    return (
      <main>
        <section className="hero compact">
          <h1>Provider access unavailable</h1>
          <p>{error}</p>
        </section>
      </main>
    );
  }

  return (
    <main>
      <section className="hero compact">
        <div className="eyebrow">Data operations</div>
        <h1>Provider Registry</h1>
        <p>
          Enable public providers, inspect licensing metadata, run supported
          datasets, and review quality and confidence.
        </p>
        {message && <div className="notice">{message}</div>}
      </section>

      <section className="provider-list">
        {providers.map((provider) => (
          <article className="provider-card" key={provider.metadata.code}>
            <div className="provider-heading">
              <div>
                <div className="eyebrow">
                  {provider.metadata.code} · {provider.metadata.stage}
                </div>
                <h2>{provider.metadata.name}</h2>
              </div>
              <div className={`status-pill ${provider.health.status.toLowerCase()}`}>
                {provider.health.status}
              </div>
            </div>

            <div className="provider-metrics">
              <div><span>Enabled</span><strong>{provider.configuration.enabled ? "Yes" : "No"}</strong></div>
              <div><span>Access</span><strong>{provider.metadata.access_type}</strong></div>
              <div><span>License</span><strong>{provider.metadata.license_name || "Unverified"}</strong></div>
              <div><span>Commercial</span><strong>{
                provider.metadata.commercial_use_allowed === true
                  ? "Allowed"
                  : provider.metadata.commercial_use_allowed === false
                    ? "Not allowed"
                    : "Unverified"
              }</strong></div>
            </div>

            <p className="muted">{provider.health.message}</p>

            <div className="capabilities">
              {provider.metadata.capabilities.map((capability) => (
                <button
                  key={capability.dataset}
                  disabled={!provider.configuration.enabled}
                  onClick={() => run(provider.metadata.code, capability.dataset)}
                >
                  Run {capability.dataset}
                </button>
              ))}
            </div>

            <div className="actions">
              <button
                className="secondary-button"
                onClick={() => toggle(
                  provider.metadata.code,
                  provider.configuration.enabled
                )}
              >
                {provider.configuration.enabled ? "Disable" : "Enable"}
              </button>
            </div>

            {provider.latest_execution && (
              <div className="latest-run">
                <strong>Latest:</strong> {provider.latest_execution.dataset} ·{" "}
                {provider.latest_execution.status} · quality{" "}
                {provider.latest_execution.quality_score}% · confidence{" "}
                {provider.latest_execution.confidence_score}%
              </div>
            )}
          </article>
        ))}
      </section>
    </main>
  );
}
