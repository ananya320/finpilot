import { useState } from "react";
import { updateProfile, changePassword, createBusiness, updateBusiness, deleteBusiness } from "../api";

function Note({ n }) {
  return n ? <p className={n.ok ? "ok" : "err"}>{n.ok ? "✓ " : "⚠ "}{n.text}</p> : null;
}

function BizRow({ biz, active, canDelete, onSave, onDelete, onSwitch }) {
  const [name, setName] = useState(biz.name);
  const [currency, setCurrency] = useState(biz.currency);
  const dirty = name.trim() !== biz.name || currency !== biz.currency;
  return (
    <div className={`bizrow ${active ? "on" : ""}`}>
      <input className="field" value={name} maxLength={80} onChange={(e) => setName(e.target.value)} />
      <select className="field" value={currency} onChange={(e) => setCurrency(e.target.value)}>
        <option value="$">$ Dollar</option>
        <option value="₹">₹ Rupee</option>
      </select>
      <button className="mini" disabled={!dirty || !name.trim()} onClick={() => onSave({ name: name.trim(), currency })}>Save</button>
      {active ? <span className="chip s-matched">active</span> : <button className="mini" onClick={onSwitch}>Switch</button>}
      <button className="mini danger" disabled={!canDelete}
              title={canDelete ? "Delete this business and all its data" : "You need at least one business"}
              onClick={onDelete}>Delete</button>
    </div>
  );
}

export default function Settings({ user, setUser, businesses, setBusinesses, activeId, onSwitch }) {
  const [name, setName] = useState(user.name);
  const [pw, setPw] = useState({ current: "", next: "" });
  const [newBiz, setNewBiz] = useState("");
  const [notes, setNotes] = useState({});
  const say = (k, text, ok = true) => setNotes((n) => ({ ...n, [k]: { text, ok } }));

  async function saveProfile(e) {
    e.preventDefault();
    try { setUser(await updateProfile(name.trim())); say("profile", "Profile saved."); }
    catch (err) { say("profile", err.message, false); }
  }

  async function savePassword(e) {
    e.preventDefault();
    try { await changePassword(pw.current, pw.next); setPw({ current: "", next: "" }); say("pw", "Password changed."); }
    catch (err) { say("pw", err.message, false); }
  }

  async function addBiz(e) {
    e.preventDefault();
    if (!newBiz.trim()) return;
    try {
      const b = await createBusiness(newBiz.trim(), "$");
      setBusinesses([...businesses, b]); setNewBiz(""); onSwitch(b.id);
      say("biz", `Created “${b.name}” and switched to it.`);
    } catch (err) { say("biz", err.message, false); }
  }

  async function saveBiz(id, patch) {
    try {
      const b = await updateBusiness(id, patch);
      setBusinesses(businesses.map((x) => (x.id === id ? b : x)));
      say("biz", "Business saved.");
    } catch (err) { say("biz", err.message, false); }
  }

  async function removeBiz(b) {
    if (!window.confirm(`Delete “${b.name}” and ALL its files, transactions and results? This cannot be undone.`)) return;
    try {
      await deleteBusiness(b.id);
      const rest = businesses.filter((x) => x.id !== b.id);
      setBusinesses(rest);
      if (b.id === activeId) onSwitch(rest[0].id);
      say("biz", "Business deleted.");
    } catch (err) { say("biz", err.message, false); }
  }

  return (
    <div>
      <div className="path">~/finpilot/<b>settings</b>.json</div>

      <div className="card">
        <h3>Profile</h3>
        <form className="inline" onSubmit={saveProfile}>
          <input className="field" value={name} onChange={(e) => setName(e.target.value)} maxLength={80} required />
          <input className="field" value={user.email} disabled title="Email cannot be changed" />
          <button className="mini" disabled={!name.trim() || name.trim() === user.name}>Save</button>
        </form>
        <Note n={notes.profile} />
      </div>

      <div className="card">
        <h3>Password</h3>
        <form className="inline" onSubmit={savePassword}>
          <input className="field" type="password" placeholder="Current password" value={pw.current} autoComplete="current-password"
                 onChange={(e) => setPw({ ...pw, current: e.target.value })} required />
          <input className="field" type="password" placeholder="New password (min 8)" value={pw.next} autoComplete="new-password"
                 onChange={(e) => setPw({ ...pw, next: e.target.value })} minLength={8} maxLength={72} required />
          <button className="mini">Change</button>
        </form>
        <Note n={notes.pw} />
      </div>

      <div className="card">
        <h3>Businesses</h3>
        <p className="muted small">Each business keeps its own files, transactions, reconciliation and chat. Currency is a display symbol only.</p>
        {businesses.map((b) => (
          <BizRow key={`${b.id}-${b.name}-${b.currency}`} biz={b} active={b.id === activeId} canDelete={businesses.length > 1}
                  onSave={(patch) => saveBiz(b.id, patch)} onDelete={() => removeBiz(b)} onSwitch={() => onSwitch(b.id)} />
        ))}
        <form className="inline" style={{ marginTop: 14 }} onSubmit={addBiz}>
          <input className="field" placeholder="New business name" value={newBiz} maxLength={80} onChange={(e) => setNewBiz(e.target.value)} />
          <button className="mini" disabled={!newBiz.trim()}>+ Add business</button>
        </form>
        <Note n={notes.biz} />
      </div>
    </div>
  );
}