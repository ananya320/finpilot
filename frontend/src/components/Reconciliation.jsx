import { useEffect, useState } from "react";
import { getRecon, runRecon } from "../api";
import { fmt } from "../money";

export default function Reconciliation({ symbol }) {
  const [data, setData] = useState({ summary: [], items: [] });
  const [busy, setBusy] = useState(false);
  const load = () => getRecon().then(setData);
  useEffect(() => { load(); }, []);

  async function run() { setBusy(true); await runRecon(); await load(); setBusy(false); }

  return (
    <div>
      <div className="path">~/finpilot/<b>reconcile</b>.py</div>
      <div className="row">
        <h2>Reconciliation</h2>
        <button className="btn" onClick={run} disabled={busy}>{busy ? "Running…" : "Run reconciliation"}</button>
      </div>

      <div className="stats">
        {data.summary.map((s) => (
          <div className={`stat s-${s.status}`} key={s.status}>
            <small>{s.status.replace("_", " ")}</small>
            <b>{s.count}</b>
            <em className="mono">{fmt(s.total_difference, symbol)}</em>
          </div>
        ))}
      </div>

      <div className="wrap">
        <table>
          <thead><tr><th>Status</th><th>Invoice</th><th>Payment</th><th className="r">Difference</th><th>Explanation</th></tr></thead>
          <tbody>
            {data.items.map((m) => (
              <tr key={m.id}>
                <td><span className={`chip s-${m.status}`}>{m.status.replace("_", " ")}</span></td>
                <td className="mono">{m.invoice}</td>
                <td className="mono">{m.payment}</td>
                <td className="r mono">{fmt(m.difference, symbol)}</td>
                <td>{m.reason}</td>
              </tr>
            ))}
            {data.items.length === 0 && <tr><td colSpan="5" className="muted">No results yet. Click “Run reconciliation”.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}