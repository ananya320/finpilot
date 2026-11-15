import { useCallback, useEffect, useState } from "react";
import Coin3D from "./components/Coin3D";
import Login from "./components/Login";
import Settings from "./components/Settings";
import Upload from "./components/Upload";
import Transactions from "./components/Transactions";
import Reconciliation from "./components/Reconciliation";
import Chat from "./components/Chat";
import * as I from "./Icons";
import { getMe, hasToken, setToken, setBusinessId, storedBusinessId, onUnauthorized, updateBusiness } from "./api";
import "./App.css";

const TABS = [
  { id: "Upload", icon: I.Home, step: I.Cloud },
  { id: "Transactions", icon: I.List, step: I.List },
  { id: "Reconciliation", icon: I.Sync, step: I.Check },
  { id: "Assistant", icon: I.Sparkle, step: I.Sparkle },
];

const HERO = {
  Upload: ["Let’s get your finances", "in sync with ", "FinPilot.", "Upload, analyze and reconcile — all in one place."],
  Transactions: ["Your transactions,", "extracted and ", "verified.", "Review every row pulled from your documents."],
  Reconciliation: ["Match invoices to payments,", "with ", "clear reasons.", "Every result comes with a plain-English explanation."],
  Assistant: ["Ask anything about", "your ", "finances.", "Answers come from your database, never guessed."],
  Settings: ["Manage your account", "and ", "businesses.", "Profile, password and a separate workspace for each business."],
};

function initialTheme() {
  try { return localStorage.getItem("fp-theme") || "dark"; } catch { return "dark"; }
}

export default function App() {
  const [booting, setBooting] = useState(hasToken());
  const [user, setUser] = useState(null);
  const [businesses, setBusinesses] = useState([]);
  const [bizId, setBizId] = useState(null);
  const [tab, setTab] = useState("Upload");
  const [theme, setTheme] = useState(initialTheme);

  const enter = useCallback((data) => {
    if (data.token) setToken(data.token);
    const saved = Number(storedBusinessId());
    const pick = data.businesses.find((b) => b.id === saved) || data.businesses[0];
    setBusinessId(pick.id);
    setUser(data.user); setBusinesses(data.businesses); setBizId(pick.id); setTab("Upload");
  }, []);

  const leave = useCallback(() => {
    setToken(null); setBusinessId(null);
    setUser(null); setBusinesses([]); setBizId(null);
  }, []);

  useEffect(() => { onUnauthorized(leave); }, [leave]);

  useEffect(() => {
    if (!hasToken()) return;
    getMe().then(enter).catch(leave).finally(() => setBooting(false));
  }, [enter, leave]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("fp-theme", theme); } catch { /* storage unavailable */ }
  }, [theme]);

  function switchBiz(id) { setBusinessId(id); setBizId(id); }

  function setCurrency(symbol) {
    updateBusiness(bizId, { currency: symbol })
      .then((u) => setBusinesses((list) => list.map((b) => (b.id === u.id ? u : b))))
      .catch(() => {});
  }

  if (booting) return <div className="boot">Loading…</div>;
  if (!user) return <Login onAuth={enter} />;

  const biz = businesses.find((b) => b.id === bizId) || businesses[0];
  const symbol = biz.currency;
  const active = TABS.findIndex((t) => t.id === tab);
  const [l1, l2, accent, sub] = HERO[tab];

  return (
    <div className="app">
      <aside className="side">
        <div className="logo"><I.Logo /><span>Fin<b>Pilot</b></span></div>

        <nav className="menu">
          {TABS.map((t) => (
            <button key={t.id} className={`item ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
              <t.icon /><span>{t.id}</span>
            </button>
          ))}
        </nav>

        <div className="promo">
          <div><I.Sparkle size={18} /><p>Smarter Finance.<br />Made Simple.</p></div>
          <Coin3D size={84} />
        </div>

        <div className="bottom">
          <button className={`item ${tab === "Settings" ? "active" : ""}`} onClick={() => setTab("Settings")}>
            <I.Gear /><span>Settings</span>
          </button>
          <button className="item" onClick={leave}><I.Logout /><span>Logout</span></button>
        </div>
      </aside>

      <div className="main">
        <header className="bar">
          <label className="bizsel" title="Switch business">
            <I.Bank size={18} />
            <select value={biz.id} onChange={(e) => switchBiz(Number(e.target.value))}>
              {businesses.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          </label>
          <div className="sym" title="Display symbol only. No currency conversion.">
            {["$", "₹"].map((s) => (
              <button key={s} className={s === symbol ? "on" : ""} onClick={() => setCurrency(s)}>{s}</button>
            ))}
          </div>
          <div className="theme">
            <button className={theme === "light" ? "on" : ""} onClick={() => setTheme("light")} aria-label="Light mode"><I.Sun size={18} /></button>
            <button className={theme === "dark" ? "on" : ""} onClick={() => setTheme("dark")} aria-label="Dark mode"><I.Moon size={18} /></button>
          </div>
          <button className="user" onClick={() => setTab("Settings")} title="Account settings">
            <span className="avatar">{user.name[0].toUpperCase()}</span>
            <span>{user.name}</span>
            <I.Chevron size={16} />
          </button>
        </header>

        <section className="hero">
          <div>
            <p className="welcome">Welcome back, {user.name}</p>
            <h1>{l1}<br />{l2}<span className="grad">{accent}</span></h1>
            <p className="sub">{sub}</p>
            <div className="rule" />
          </div>
          <div className="slogan">Organize <i>•</i> Reconcile <i>•</i> Grow <I.Trend size={22} /></div>
        </section>

        {tab !== "Settings" && (
          <div className="steps">
            {TABS.map((t, i) => (
              <div className="stepwrap" key={t.id}>
                <button className={`step ${i === active ? "now" : i < active ? "done" : ""}`} onClick={() => setTab(t.id)}>
                  <span className="dot"><t.step size={22} /></span>
                  <span className="lbl"><small>{i + 1}</small>{t.id}</span>
                </button>
                {i < TABS.length - 1 && <span className="line" />}
              </div>
            ))}
          </div>
        )}

        <main className="panel">
          {tab === "Upload" && <Upload key={bizId} />}
          {tab === "Transactions" && <Transactions key={bizId} symbol={symbol} />}
          {tab === "Reconciliation" && <Reconciliation key={bizId} symbol={symbol} />}
          {tab === "Assistant" && <Chat key={bizId} />}
          {tab === "Settings" && (
            <Settings user={user} setUser={setUser} businesses={businesses} setBusinesses={setBusinesses}
                      activeId={biz.id} onSwitch={switchBiz} />
          )}
        </main>
      </div>
    </div>
  );
}
