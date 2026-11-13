import { useState } from "react";
import Upload from "./components/Upload";
import Transactions from "./components/Transactions";
import Reconciliation from "./components/Reconciliation";
import Chat from "./components/Chat";
import "./App.css";

const TABS = ["Upload", "Transactions", "Reconciliation", "Assistant"];

export default function App() {
  const [tab, setTab] = useState("Upload");
  return (
    <div className="app">
      <header><h1>FinPilot</h1>
        <nav>{TABS.map(t => (
          <button key={t} className={t === tab ? "active" : ""} onClick={() => setTab(t)}>{t}</button>
        ))}</nav>
      </header>
      <main>
        {tab === "Upload" && <Upload />}
        {tab === "Transactions" && <Transactions />}
        {tab === "Reconciliation" && <Reconciliation />}
        {tab === "Assistant" && <Chat />}
      </main>
    </div>
  );
}
