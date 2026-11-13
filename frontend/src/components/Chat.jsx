import { useState, useRef } from "react";
import { sendChat } from "../api";

export default function Chat() {
  const [msgs, setMsgs] = useState([{ role: "bot", text: "Ask me about your transactions or reconciliation results." }]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const session = useRef(crypto.randomUUID());

  async function send(e) {
    e.preventDefault();
    if (!input.trim()) return;
    const q = input; setInput("");
    setMsgs(m => [...m, { role: "user", text: q }]); setBusy(true);
    try {
      const r = await sendChat(q, session.current);
      setMsgs(m => [...m, { role: "bot", text: r.answer }]);
    } catch { setMsgs(m => [...m, { role: "bot", text: "Something went wrong." }]); }
    setBusy(false);
  }

  return (
    <div className="chat">
      {msgs.map((m, i) => <div key={i} className={`msg ${m.role}`}>{m.text}</div>)}
      <form onSubmit={send}>
        <input style={{ width: "75%" }} value={input} onChange={e => setInput(e.target.value)}
               placeholder="Why is INV-1002 mismatched?" />{" "}
        <button disabled={busy}>{busy ? "Thinking…" : "Send"}</button>
      </form>
    </div>
  );
}