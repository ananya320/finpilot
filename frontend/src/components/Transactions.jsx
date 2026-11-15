import { useEffect, useState } from "react";
import { getTransactions } from "../api";
import { fmt } from "../money";

export default function Transactions({ symbol }) {
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => { getTransactions().then(setRows).finally(() => setLoading(false)); }, []);

  const shown = rows.filter((r) =>
    [r.description, r.reference, r.counterparty, r.source].join(" ").toLowerCase().includes(q.toLowerCase()));

  return (
    <div>
      <div className="path">~/finpilot/<b>ledger</b>.json</div>
      <div className="row">
        <h2>Transactions <span className="count">{shown.length}</span></h2>
        <input className="field" placeholder="filter…" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      {loading ? <p className="muted">Loading…</p> : (
        <div className="wrap">
          <table>
            <thead><tr><th>Date</th><th>Source</th><th>Description</th><th>Ref</th><th className="r">Amount</th><th></th></tr></thead>
            <tbody>
              {shown.map((r) => (
                <tr key={r.id}>
                  <td className="mono">{r.date}</td>
                  <td><span className="chip src">{r.source}</span></td>
                  <td>{r.description}</td>
                  <td className="mono">{r.reference}</td>
                  <td className={`r mono ${Number(r.amount) < 0 ? "neg" : "pos"}`}>{fmt(r.amount, symbol)}</td>
                  <td>{r.needs_review && <span className="chip s-probable">review</span>}</td>
                </tr>
              ))}
              {shown.length === 0 && <tr><td colSpan="6" className="muted">No transactions yet. Upload a file first.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}