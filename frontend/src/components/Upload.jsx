import { useRef, useState } from "react";
import { uploadFile } from "../api";
import { Bank, Doc, Card, Folder, Arrow, FileUp } from "../Icons";

const TYPES = [
  ["bank_statement", "Bank Statement", Bank],
  ["invoice", "Invoice", Doc],
  ["payment", "Payment Record", Card],
];
const MAX = 10 * 1024 * 1024; // 10 MB

export default function Upload() {
  const [docType, setDocType] = useState("bank_statement");
  const [file, setFile] = useState(null);
  const [drag, setDrag] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const input = useRef(null);

  function pick(f) {
    if (!f) return;
    if (!/\.(pdf|csv|xlsx)$/i.test(f.name)) return setError("Unsupported file type. Use PDF, CSV or XLSX.");
    if (f.size > MAX) return setError("File is larger than 10MB.");
    setError(""); setResult(null); setFile(f);
  }

  async function submit() {
    if (!file) return;
    setLoading(true); setError(""); setResult(null);
    try { setResult(await uploadFile(file, docType)); setFile(null); }
    catch (e) { setError(e.message); }
    setLoading(false);
  }

  return (
    <div>
      <div className="seg">
        {TYPES.map(([v, label, Icon]) => (
          <button key={v} className={v === docType ? "on" : ""} onClick={() => setDocType(v)}>
            <Icon size={20} />{label}
          </button>
        ))}
      </div>

      <div
        className={`drop ${drag ? "drag" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files[0]); }}
      >
        <span className="fileicon"><FileUp size={56} /></span>
        <p className="big">{file ? file.name : "Drag & Drop your PDF, CSV or XLSX file here"}</p>
        {file && <p className="small">{(file.size / 1024).toFixed(0)} KB ready to upload</p>}
        <div className="or"><span>or</span></div>
        <input ref={input} type="file" accept=".pdf,.csv,.xlsx" hidden onChange={(e) => pick(e.target.files[0])} />
        <button className="browse" onClick={() => input.current.click()}><Folder size={20} />Browse Files<Arrow size={18} /></button>
        <p className="small">Supported formats: PDF, CSV, XLSX &nbsp;•&nbsp; Max size: 10MB</p>
      </div>

      {file && (
        <button className="btn go" disabled={loading} onClick={submit}>
          {loading ? "Processing…" : "Upload and extract"}
        </button>
      )}

      {error && <p className="err">⚠ {error}</p>}
      {result && (
        <>
          <div className="stats">
            <div className="stat s-matched"><small>saved</small><b>{result.saved}</b></div>
            <div className="stat s-probable"><small>needs review</small><b>{result.needs_review}</b></div>
            <div className="stat s-unpaid"><small>rejected rows</small><b>{result.rejected.length}</b></div>
          </div>
          {result.rejected.length > 0 && <ul className="mono">{result.rejected.map((r, i) => <li key={i}>{r}</li>)}</ul>}
        </>
      )}
    </div>
  );
}