import { useEffect, useState } from "react";
import Coin3D from "./components/Coin3D";
import Upload from "./components/Upload";
import Transactions from "./components/Transactions";
import Reconciliation from "./components/Reconciliation";
import Chat from "./components/Chat";
import * as I from "./Icons";
import "./App.css";

const USER_NAME = "Ananya"; // display only, there is no login yet

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
};

function initialTheme() {
  try { return localStorage.getItem("fp-theme") || "dark"; } catch { return "dark"; }
}

export default function App() {
  const [tab, setTab] = useState("Upload");
  const [symbol, setSymbol] = useState("$");
  const [theme, setTheme] = useState(initialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("fp-theme", theme); } catch { /* storage unavailable */ }
  }, [theme]);

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
          <div>
            <I.Sparkle size={18} />
            <p>Smarter Finance.<br />Made Simple.</p>
          </div>
          <Coin3D size={84} />
        </div>

        <div className="bottom">
          <button className="item" disabled title="Coming soon"><I.Gear /><span>Settings</span></button>
          <button className="item" disabled title="Coming soon (no login yet)"><I.Logout /><span>Logout</span></button>
        </div>
      </aside>

      <div className="main">
        <header className="bar">
          <div className="sym" title="Display symbol only. No currency conversion.">
            {["$", "₹"].map((s) => (
              <button key={s} className={s === symbol ? "on" : ""} onClick={() => setSymbol(s)}>{s}</button>
            ))}
          </div>
          <div className="theme">
            <button className={theme === "light" ? "on" : ""} onClick={() => setTheme("light")} aria-label="Light mode"><I.Sun size={18} /></button>
            <button className={theme === "dark" ? "on" : ""} onClick={() => setTheme("dark")} aria-label="Dark mode"><I.Moon size={18} /></button>
          </div>
          <div className="user">
            <span className="avatar">{USER_NAME[0]}</span>
            <span>{USER_NAME}</span>
            <I.Chevron size={16} />
          </div>
        </header>

        <section className="hero">
          <div>
            <p className="welcome">Welcome back,</p>
            <h1>{l1}<br />{l2}<span className="grad">{accent}</span></h1>
            <p className="sub">{sub}</p>
            <div className="rule" />
          </div>
          <div className="slogan">Organize <i>•</i> Reconcile <i>•</i> Grow <I.Trend size={22} /></div>
        </section>

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

        <main className="panel">
          {tab === "Upload" && <Upload />}
          {tab === "Transactions" && <Transactions symbol={symbol} />}
          {tab === "Reconciliation" && <Reconciliation symbol={symbol} />}
          {tab === "Assistant" && <Chat />}
        </main>
      </div>
    </div>
  );
}
