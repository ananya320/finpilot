const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

let token = null;
let businessId = null;
let unauthorizedHandler = () => {};

try {
  token = localStorage.getItem("fp-token");
  businessId = localStorage.getItem("fp-biz");
} catch { /* storage unavailable */ }

function store(key, value) {
  try {
    if (value === null || value === undefined) localStorage.removeItem(key);
    else localStorage.setItem(key, String(value));
  } catch { /* storage unavailable */ }
}

export const hasToken = () => Boolean(token);
export const storedBusinessId = () => businessId;
export const setToken = (t) => { token = t; store("fp-token", t); };
export const setBusinessId = (id) => { businessId = id; store("fp-biz", id); };
export const onUnauthorized = (fn) => { unauthorizedHandler = fn; };

function errorText(data) {
  const d = data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((x) => x.msg).join("; ");
  return "Request failed";
}

async function request(path, { method = "GET", json, form } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (businessId) headers["X-Business-Id"] = String(businessId);
  let body;
  if (json !== undefined) { headers["Content-Type"] = "application/json"; body = JSON.stringify(json); }
  if (form) body = form;

  let res;
  try { res = await fetch(`${API}${path}`, { method, headers, body }); }
  catch { throw new Error("Cannot reach the server. Is the backend running?"); }

  let data = null;
  try { data = await res.json(); } catch { /* empty body */ }

  const isAuthCall = path.startsWith("/auth/login") || path.startsWith("/auth/register");
  if (res.status === 401 && !isAuthCall) unauthorizedHandler();
  if (!res.ok) throw new Error(errorText(data));
  return data;
}

// auth
export const register = (name, email, password, business_name) =>
  request("/auth/register", { method: "POST", json: { name, email, password, business_name } });
export const login = (email, password) =>
  request("/auth/login", { method: "POST", json: { email, password } });
export const getMe = () => request("/auth/me");
export const updateProfile = (name) => request("/auth/me", { method: "PATCH", json: { name } });
export const changePassword = (current_password, new_password) =>
  request("/auth/password", { method: "POST", json: { current_password, new_password } });

// businesses
export const createBusiness = (name, currency) =>
  request("/businesses", { method: "POST", json: { name, currency } });
export const updateBusiness = (id, patch) =>
  request(`/businesses/${id}`, { method: "PATCH", json: patch });
export const deleteBusiness = (id) => request(`/businesses/${id}`, { method: "DELETE" });

// files and data
export function uploadFile(file, docType) {
  const form = new FormData();
  form.append("file", file);
  form.append("doc_type", docType);
  return request("/upload", { method: "POST", form });
}
export const getDocuments = () => request("/documents");
export const deleteDocument = (id) => request(`/documents/${id}`, { method: "DELETE" });
export const getTransactions = () => request("/transactions");
export const getRecon = () => request("/reconciliation");
export const runRecon = () => request("/reconciliation/run", { method: "POST" });
export const sendChat = (message, sessionId) =>
  request("/chat", { method: "POST", json: { message, session_id: sessionId } });