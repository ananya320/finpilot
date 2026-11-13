import { useEffect, useState } from "react";
import { getRecon, runRecon } from "../api";

export default function Reconciliation() {
  const [data, setData] = useState({ summary: [], items: [] });
  const [busy, setBusy] = useState(false);
  const load = () => getRecon().then(setData);
  useEffect(() => { load(); }, []);

  async function run() { setBusy(true); await runRecon(); await load(); setBusy(false); }

  return (
    <div>
      <h2>Reconciliation <button onClick={run} disabled={busy}>{busy ? "Running…" : "Run reconciliation"}</button></h2>
      <div className="cards">
        {data.summary.map(s => (
          <div className="card" key={s.status}><span className={`badge ${s.status}`}>{s.status}</span> {s.count}</div>
        ))}
      </div>
      <table>
        <thead><tr><th>Status</th><th>Invoice</th><th>Payment</th><th>Difference</th><th>Explanation</th></tr></thead>
        <tbody>{data.items.map(m => (
          <tr key={m.id}>
            <td><span className={`badge ${m.status}`}>{m.status}</span></td>
            <td>{m.invoice}</td><td>{m.payment}</td><td>{m.difference}</td><td>{m.reason}</td>
          </tr>))}
        </tbody>
      </table>
    </div>
  );
}