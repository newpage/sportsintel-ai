"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "../../components/AppShell";
import { ConfidenceBar } from "../../components/ConfidenceBar";
import { EdgeBadge } from "../../components/EdgeBadge";
import { apiFetch } from "../../lib/api";

type AssistantAction = {
  id: string;
  title: string;
  subtitle: string;
  prompt: string;
  category: string;
  tone: string;
  game_slug?: string;
};

type Workspace = {
  season: number;
  week: number;
  last_updated: string;
  mode: string;
  featured: {
    title: string;
    summary: string;
    edge: number;
    confidence: number;
    risk: string;
    trend: number;
    game_slug?: string;
    evidence: string[];
    warnings: string[];
  };
  actions: AssistantAction[];
  suggested_prompts: string[];
  capabilities: string[];
};

type AssistantAnswer = {
  prompt: string;
  answer: string;
  category: string;
  evidence: string[];
  related: { label: string; href: string }[];
  generated_at: string;
  grounding: string;
};

export default function AssistantPage() {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [answer, setAnswer] = useState<AssistantAnswer | null>(null);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch("/v1/assistant")
      .then(setWorkspace)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load the Assistant"));
  }, []);

  async function ask(question: string) {
    const cleaned = question.trim();
    if (!cleaned || loading) return;
    setLoading(true);
    setError("");
    setPrompt(cleaned);
    try {
      const response = await apiFetch("/v1/assistant/query", {
        method: "POST",
        body: JSON.stringify({ prompt: cleaned }),
      });
      setAnswer(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to generate analysis");
    } finally {
      setLoading(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void ask(prompt);
  }

  return (
    <AppShell>
      {error && !workspace ? (
        <div className="page-error">
          <h1>Assistant unavailable</h1>
          <p>{error}</p>
          <a href="/login?returnTo=/assistant">Sign in</a>
        </div>
      ) : !workspace ? (
        <div className="skeleton-shell"><div/><div/><div/><div/></div>
      ) : (
        <>
          <div className="page-heading assistant-heading">
            <div>
              <span className="page-kicker">Grounded decision support</span>
              <h1>SportsIntel Assistant</h1>
              <p>Ask focused questions about Survivor, spreads, totals, weather, injuries, and current Week 1 game intelligence.</p>
            </div>
            <div className="update-stamp">
              Week {workspace.week}<br />
              <strong>{new Date(workspace.last_updated).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</strong>
            </div>
          </div>

          <div className="assistant-workspace-grid">
            <section className="assistant-main-column">
              <div className="assistant-featured-card">
                <div className="assistant-featured-heading">
                  <div>
                    <span className="page-kicker">Featured decision</span>
                    <h2>{workspace.featured.title}</h2>
                  </div>
                  <EdgeBadge edge={workspace.featured.edge} />
                </div>
                <p>{workspace.featured.summary}</p>
                <ConfidenceBar value={workspace.featured.confidence} />
                <div className="assistant-meta-row">
                  <span className={`risk-badge ${workspace.featured.risk.toLowerCase()}`}>{workspace.featured.risk} risk</span>
                  <span className={workspace.featured.trend >= 0 ? "trend-up" : "trend-down"}>
                    {workspace.featured.trend >= 0 ? "↑" : "↓"} {Math.abs(workspace.featured.trend)} movement
                  </span>
                </div>
                <div className="assistant-evidence-chips">
                  {workspace.featured.evidence.map((item) => <span key={item}>{item}</span>)}
                </div>
                {workspace.featured.warnings.length > 0 && (
                  <div className="assistant-warning">Watch: {workspace.featured.warnings.join(" · ")}</div>
                )}
                {workspace.featured.game_slug && (
                  <Link className="inline-link" href={`/games/${workspace.featured.game_slug}`}>Open Game Intelligence →</Link>
                )}
              </div>

              <form className="assistant-composer" onSubmit={submit}>
                <label htmlFor="assistant-prompt">Ask SportsIntel</label>
                <div>
                  <input
                    id="assistant-prompt"
                    value={prompt}
                    onChange={(event) => setPrompt(event.target.value)}
                    placeholder="Why is Buffalo ranked first?"
                    maxLength={500}
                  />
                  <button type="submit" disabled={loading || prompt.trim().length < 2}>
                    {loading ? "Analyzing…" : "Analyze"}
                  </button>
                </div>
                <small>Responses are assembled from current SportsIntel recommendations and Game Intelligence—not generic football commentary.</small>
              </form>

              {error && <div className="assistant-error">{error}</div>}

              {answer ? (
                <section className="assistant-answer-card">
                  <div className="assistant-answer-top">
                    <span>{answer.category}</span>
                    <small>{new Date(answer.generated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</small>
                  </div>
                  <h2>{answer.prompt}</h2>
                  <p className="assistant-answer-copy">{answer.answer}</p>
                  <div className="assistant-answer-evidence">
                    <h3>Supporting evidence</h3>
                    {answer.evidence.map((item) => <div key={item}><span>✓</span>{item}</div>)}
                  </div>
                  {answer.related.length > 0 && (
                    <div className="assistant-related-links">
                      {answer.related.map((link) => <Link href={link.href} key={`${link.href}-${link.label}`}>{link.label} →</Link>)}
                    </div>
                  )}
                  <small className="assistant-grounding">Grounded in: {answer.grounding}</small>
                </section>
              ) : (
                <section className="assistant-empty-answer">
                  <span>✦</span>
                  <h2>Choose a decision or ask a question</h2>
                  <p>The Assistant will explain the current evidence, risks, market context, and applicable game intelligence.</p>
                </section>
              )}
            </section>

            <aside className="assistant-action-column">
              <div className="assistant-side-heading">
                <span className="page-kicker">One-click analysis</span>
                <h2>Decision shortcuts</h2>
              </div>
              <div className="assistant-action-list">
                {workspace.actions.map((action) => (
                  <button
                    className={`assistant-action-card ${action.tone.toLowerCase()}`}
                    onClick={() => void ask(action.prompt)}
                    disabled={loading}
                    key={action.id}
                  >
                    <span>{action.category}</span>
                    <strong>{action.title}</strong>
                    <small>{action.subtitle}</small>
                    <b>→</b>
                  </button>
                ))}
              </div>
              <div className="assistant-capabilities">
                <span className="page-kicker">Available now</span>
                {workspace.capabilities.map((capability) => <div key={capability}><span>✓</span>{capability}</div>)}
              </div>
            </aside>
          </div>
        </>
      )}
    </AppShell>
  );
}
