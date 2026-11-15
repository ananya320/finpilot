import { useEffect, useRef, useState } from "react";
import { uploadFile, getDocuments, deleteDocument } from "../api";
import { Bank, Doc, Card, Folder, Arrow, FileUp } from "../Icons";

const TYPES = [
  ["bank_statement", "Bank Statement", Bank],
  ["invoice", "Invoice", Doc],
  ["payment", "Payment Record", Card],
];
const LABEL = { bank_statement: "Bank statement", invoice: "Invoice", payment: "Payment" };
const STATUS_CLASS = { queued: "", uploading: "s-probable", done: "s-matched", error: "s-unpaid" };
const MAX = 10 * 1024 * 1024;
const kb = (n) => (n >= 1048576 ? `${(n / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`);

export default function Upload() {
  const [docType, setDocType] = useState("bank_statement");
  const [queue, setQueue] = useState([]);
  const [docs, setDocs] = useState([]);
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const input = useRef(null);
  const seq = useRef(0);

  const loadDocs = () => getDocuments().then(setDocs).catch(() => {});
  useEffect(() => { loadDocs(); }, []);

  const patch = (id, p) => setQueue((q) => q.map((i) => (i.id === id ? { ...i, ...p } : i)));

  function add(list) {
    const problems = [];
    const items = [];
    for (const f of Array.from(list)) {
      if (!/\.(pdf|csv|xlsx)$/i.test(f.name)) { problems.push(`${f.name}: unsupported type`); continue; }
      if (f.size > MAX) { problems.push(`${f.name}: larger than 10MB`); continue; }
      items.push({ id: ++seq.current, file: f, type: docType, status: "queued", message: "" });
    }
    setError(problems.join(" · "));
    setQueue((q) => [...q, ...items]);
  }

  async function uploadAll() {
    setBusy(true);
    const todo = queue.filter((i) => i.status === "queued" || i.status === "error");
    for (const item of todo) {
      patch(item.id, { status: "uploading", message: "" });
      try {
        const r = await uploadFile(item.file, item.type);
        patch(item.id, { status: "done", message: `${r.saved} saved · ${r.needs_review} to review · ${r.rejected.length} rejected` });
      } catch (e) { patch(item.id, { status: "error", message: e.message }); }
    }
    setBusy(false);
    loadDocs();
  }

  async function removeDoc(d) {
    if (!window.confirm(`Delete “${d.filename}” and its ${d.rows} transactions? Run reconciliation again afterwards.`)) return;
    try { await deleteDocument(d.id); loadDocs(); } catch (e) { setError(e.message); }
  }

  const waiting = queue.filter((i) => i.status === "queued" || i.status === "error").length;

  return (
    <div>
      <div className="seg">
        {TYPES.map(([v, label, Icon]) => (
          <button key={v} className={v === docType ? "on" : ""} onClick={() => setDocType(v)}>
            <Icon size={20} />{label}
          </button>
        ))}
      </div>

      <div className={`drop ${drag ? "drag" : ""}`}
           onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
           onDragLeave={() => setDrag(false)}
           onDrop={(e) => { e.preventDefault(); setDrag(false); add(e.dataTransfer.files); }}>
        <span className="fileicon"><FileUp size={56} /></span>
        <p className="big">Drag &amp; drop one or many files here</p>
        <p className="small">New files are added as <b>{LABEL[docType]}</b>. Switch the tab above to add another type.</p>
        <div className="or"><span>or</span></div>
        <input ref={input} type="file" multiple accept=".pdf,.csv,.xlsx" hidden
               onChange={(e) => { add(e.target.files); e.target.value = ""; }} />
        <button className="browse" onClick={() => input.current.click()}><Folder size={20} />Browse Files<Arrow size={18} /></button>
        <p className="small">Supported formats: PDF, CSV, XLSX &nbsp;•&nbsp; Max size: 10MB each</p>
      </div>

      {error && <p className="err">⚠ {error}</p>}

      {queue.length > 0 && (
        <div className="queue">
          {queue.map((i) => (
            <div className="qitem" key={i.id}>
              <span className="qname">{i.file.name} <span className="muted">({kb(i.file.size)})</span></span>
              <span className="chip src">{LABEL[i.type]}</span>
              <span className={`chip ${STATUS_CLASS[i.status]}`}>{i.status}</span>
              {i.message && <span className="qmsg">{i.message}</span>}
              {i.status !== "uploading" && i.status !== "done" &&
                <button className="mini" onClick={() => setQueue((q) => q.filter((x) => x.id !== i.id))}>Remove</button>}
            </div>
          ))}
          <div className="qactions">
            <button className="btn" disabled={busy || waiting === 0} onClick={uploadAll}>
              {busy ? "Uploading…" : `Upload ${waiting} file${waiting === 1 ? "" : "s"}`}
            </button>
            <button className="mini" disabled={busy} onClick={() => setQueue((q) => q.filter((i) => i.status !== "done"))}>Clear finished</button>
          </div>
        </div>
      )}

      <div className="section">
        <h3>Saved files <span className="count">{docs.length}</span></h3>
        <div className="wrap">
          <table>
            <thead><tr><th>File</th><th>Type</th><th className="r">Rows</th><th>Size</th><th>Uploaded</th><th></th></tr></thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id}>
                  <td>{d.filename}</td>
                  <td><span className="chip src">{LABEL[d.doc_type]}</span></td>
                  <td className="r mono">{d.rows}</td>
                  <td className="mono">{kb(d.size)}</td>
                  <td className="mono">{new Date(d.created).toLocaleDateString()}</td>
                  <td className="r"><button className="mini danger" onClick={() => removeDoc(d)}>Delete</button></td>
                </tr>
              ))}
              {docs.length === 0 && <tr><td colSpan="6" className="muted">No files saved for this business yet.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}