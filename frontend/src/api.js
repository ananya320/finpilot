const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function uploadFile(file, docType) {
  const form = new FormData();
  form.append("file", file);
  form.append("doc_type", docType);
  const res = await fetch(`${API}/upload`, { method: "POST", body: form });
  const body = await res.json();
  if (!res.ok) throw new Error(body.detail || "Upload failed");
  return body;
}
export const getTransactions = () => fetch(`${API}/transactions`).then(r => r.json());
export const getRecon = () => fetch(`${API}/reconciliation`).then(r => r.json());
export const runRecon = () => fetch(`${API}/reconciliation/run`, { method: "POST" }).then(r => r.json());
export async function sendChat(message, sessionId) {
  const res = await fetch(`${API}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  return res.json();
}