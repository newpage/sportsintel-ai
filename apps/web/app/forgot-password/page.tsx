"use client";
import { FormEvent, useState } from "react";
import { apiFetch } from "../../lib/api";
export default function ForgotPasswordPage() {
  const [email,setEmail]=useState(""); const [message,setMessage]=useState("");
  async function submit(e:FormEvent){e.preventDefault(); await apiFetch("/v1/auth/password-reset/request",{method:"POST",body:JSON.stringify({email})}); setMessage("If the account exists, reset instructions have been created.");}
  return <main className="auth-shell"><form className="auth-card" onSubmit={submit}><div className="eyebrow">Account recovery</div><h1>Reset password</h1><label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required/></label>{message&&<div>{message}</div>}<button>Request reset</button></form></main>;
}
