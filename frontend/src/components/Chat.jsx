import { useEffect, useRef, useState } from "react";
import { sendChat } from "../api";

const IDEAS = ["Why is INV-1002 flagged?", "Which invoices are unpaid?", "Total of all bank transactions"];

export default function Chat() {
  const [msgs, setMsgs] = useState([{ role: "bot", text: "Ask about your transactions or reconciliation results." }]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const session = useRef(crypto.randomUUID());
  const end = useRef(null);

  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs, busy]);

  async function send(text) {
    const q = text.trim();
    if (!q || busy) return;
    setInput("");
    setMsgs((m) => [...m, { role: "user", text: q }]);
    setBusy(true);
    try {
      const r = await sendChat(q, session.current);
      setMsgs((m) => [...m, { role: "bot", text: r.answer || "No answer returned." }]);
    } catch (e) {
      setMsgs((m) => [...m, { role: "bot", text: e.message }]);
    }
    setBusy(false);
  }

  return (
    <div>
      <div className="path">~/finpilot/<b>assistant</b>.ts</div>
      <div className="ideas">{IDEAS.map((i) => <button key={i} className="idea" onClick={() => send(i)}>{i}</button>)}</div>
      <div className="chat">
        {msgs.map((m, i) => <div key={i} className={`msg ${m.role}`}>{m.text}</div>)}
        {busy && <div className="msg bot muted">thinking…</div>}
        <div ref={end} />
      </div>
      <form className="composer" onSubmit={(e) => { e.preventDefault(); send(input); }}>
        <span className="prompt">{">"}</span>
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask FinPilot…" />
        <button className="btn" disabled={busy}>Send</button>
      </form>
    </div>
  );
}