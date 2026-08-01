"use client";

import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch } from "../../lib/api";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const result = await apiFetch("/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      const target = searchParams.get("returnTo") || (result.user.role === "ADMIN" ? "/admin" : "/");
      router.push(target);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in");
    }
  }

  return (
    <main className="auth-shell">
      <form className="auth-card" onSubmit={submit}>
        <div className="eyebrow">Secure access</div>
        <h1>Sign in</h1>
        <p>Access NFL strategies, LMS tools, and your SportsIntel account.</p>
        <label>Email<input type="email" value={email} onChange={e => setEmail(e.target.value)} required /></label>
        <label>Password<input type="password" value={password} onChange={e => setPassword(e.target.value)} required /></label>
        {error && <div className="error">{error}</div>}
        <a href="/forgot-password">Forgot password?</a>
        <button type="submit">Sign in</button>
      </form>
    </main>
  );
}
