import { useState } from "react";
import { login, register } from "../api";
import Coin3D from "./Coin3D";
import { Logo } from "../Icons";

const SIGNUP_ENABLED = false; // set to true if you turn on allow_signup in config.py

export default function Login({ onAuth }) {
  const [mode, setMode] = useState("login");
  const [f, setF] = useState({ name: "", email: "", password: "", business: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF((s) => ({ ...s, [k]: e.target.value }));
  const isLogin = mode === "login";

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      const data = isLogin
        ? await login(f.email, f.password)
        : await register(f.name, f.email, f.password, f.business.trim() || "My Business");
      onAuth(data);
    } catch (err) { setError(err.message); }
    setBusy(false);
  }

  return (
    <div className="authwrap">
      <form className="authcard" onSubmit={submit}>
        <div className="coincenter"><Coin3D size={110} /></div>
        <div className="logo"><Logo /><span>Fin<b>Pilot</b></span></div>
        <h2>{isLogin ? "Welcome back" : "Create your account"}</h2>
        <p className="sub muted">{isLogin ? "Log in to your workspace." : "Start reconciling in minutes."}</p>

        <div className="form">
          {!isLogin && (
            <>
              <label>Your name<input className="field" value={f.name} onChange={set("name")} required maxLength={80} autoComplete="name" /></label>
              <label>Business name<input className="field" value={f.business} onChange={set("business")} placeholder="My Business" maxLength={80} /></label>
            </>
          )}
          <label>Email<input className="field" type="email" value={f.email} onChange={set("email")} required autoComplete="email" /></label>
          <label>Password{!isLogin && " (min 8 characters)"}
            <input className="field" type="password" value={f.password} onChange={set("password")} required minLength={isLogin ? 1 : 8} maxLength={72}
                   autoComplete={isLogin ? "current-password" : "new-password"} />
          </label>
          {error && <p className="err">⚠ {error}</p>}
          <button className="btn" disabled={busy}>{busy ? "Please wait…" : isLogin ? "Log in" : "Create account"}</button>
          {SIGNUP_ENABLED && (
            <button type="button" className="link" onClick={() => { setMode(isLogin ? "register" : "login"); setError(""); }}>
              {isLogin ? "New here? Create an account" : "Already have an account? Log in"}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}