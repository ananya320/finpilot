import { useEffect, useState } from "react";
import { getTransactions } from "../api";

export default function Transactions() {
  const [rows, setRows] = useState([]);
  useEffect(() => { getTransactions().then(setRows); }, []);
  return (
    <div>
      <h2>Transactions ({rows.length})</h2>
      <table>
        <thead><tr><th>Date</th><th>Source</th><th>Description</th><th>Ref</th><th>Amount</th><th></th></tr></thead>
        <tbody>{rows.map(r => (
          <tr key={r.id}>
            <td>{r.date}</td><td>{r.source}</td><td>{r.description}</td>
            <td>{r.reference}</td><td>{r.amount}</td>
            <td>{r.needs_review && <span className="badge probable">review</span>}</td>
          </tr>))}
        </tbody>
      </table>
    </div>
  );
}