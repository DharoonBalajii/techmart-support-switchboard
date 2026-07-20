"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/lib/auth";
import "../auth.css";

export default function SignUpPage() {
  const router = useRouter();
  const { register, error, clearError } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await register(name, email, password);
      router.push("/chat");
    } catch {
      // error already surfaced via context
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <Link href="/" className="auth-brand">
          <div className="brand-mark" aria-hidden>
            <span /><span /><span />
            <div className="brand-core" />
          </div>
          <b>Support Switchboard</b>
        </Link>

        <>
          <h1>Create your account</h1>
          <p className="auth-sub">Sign up to open the multi-agent support console.</p>
        </>

        {error && <div className="auth-error"><span>⚠</span> {error}</div>}

          <form onSubmit={onSubmit}>
            <div className="auth-field">
              <label htmlFor="name">Full name</label>
              <input
                id="name"
                type="text"
                autoComplete="name"
                required
                value={name}
                onChange={(e) => { setName(e.target.value); clearError(); }}
                placeholder="Jane Doe"
              />
            </div>
            <div className="auth-field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => { setEmail(e.target.value); clearError(); }}
                placeholder="jane@example.com"
              />
            </div>
            <div className="auth-field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                autoComplete="new-password"
                required
                minLength={8}
                value={password}
                onChange={(e) => { setPassword(e.target.value); clearError(); }}
                placeholder="At least 8 characters"
              />
              <div className="hint">Use 8 or more characters.</div>
            </div>

            <button className="auth-submit" type="submit" disabled={submitting}>
              {submitting ? "Creating account…" : "Sign up"}
            </button>
          </form>

        <div className="auth-switch">
          Already have an account? <Link href="/sign-in">Sign in</Link>
        </div>
        <Link href="/" className="auth-back">← Back to home</Link>
      </div>
    </div>
  );
}
