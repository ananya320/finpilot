import { useState } from "react";
import { uploadFile } from "../api";

export default function Upload() {
  const [docType, setDocType] = useState("bank_statement");
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!file) return;
    setLoading(true); setError(""); setResult(null);
    try { setResult(await uploadFile(file, docType)); }
    catch (err) { setError(err.message); }
    setLoading(false);
  }

  return (
    <div>
      <h2>Upload documents</h2>
      <form onSubmit={submit}>
        <select value={docType} onChange={e => setDocType(e.target.value)}>
          <option value="bank_statement">Bank statement</option>
          <option value="invoice">Invoice</option>
          <option value="payment">Payment record</option>
        </select>{" "}
        <input type="file" accept=".pdf,.csv,.xlsx" onChange={e => setFile(e.target.files[0])} />{" "}
        <button disabled={!file || loading}>{loading ? "Processing…" : "Upload"}</button>
      </form>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      {result && (
        <div className="cards">
          <div className="card">Saved: <b>{result.saved}</b></div>
          <div className="card">Needs review: <b>{result.needs_review}</b></div>
          <div className="card">Rejected rows: <b>{result.rejected.length}</b></div>
          {result.rejected.length > 0 && (
            <ul>{result.rejected.map((r, i) => <li key={i}>{r}</li>)}</ul>
          )}
        </div>
      )}
    </div>
  );
}