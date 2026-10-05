// Shared helpers: login session, API calls, navigation bar.

const Auth = {
  get token() {
    try { return localStorage.getItem("fb_token"); } catch { return null; }
  },
  get user() {
    try { return JSON.parse(localStorage.getItem("fb_user")); } catch { return null; }
  },
  save(token, user) {
    localStorage.setItem("fb_token", token);
    localStorage.setItem("fb_user", JSON.stringify(user));
  },
  clear() {
    try {
      localStorage.removeItem("fb_token");
      localStorage.removeItem("fb_user");
    } catch { /* storage unavailable */ }
  },
  dashboardFor(role) {
    return { donor: "/donor", ngo: "/ngo", admin: "/admin" }[role] || "/";
  },
  // Redirects away unless the logged-in user has one of the given roles.
  requireRole(...roles) {
    const user = this.user;
    if (!this.token || !user) {
      location.href = "/login";
      return null;
    }
    if (!roles.includes(user.role)) {
      location.href = this.dashboardFor(user.role);
      return null;
    }
    return user;
  },
};

function formatError(data) {
  const detail = data && data.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((e) => `${(e.loc || []).slice(-1)[0] || "field"}: ${e.msg}`).join("; ");
  }
  return "";
}

// fetch() wrapper: adds the auth header, sends JSON / FormData, throws readable errors.
async function api(path, { method = "GET", body } = {}) {
  const headers = {};
  if (Auth.token) headers.Authorization = `Bearer ${Auth.token}`;
  let payload = body;
  if (body && !(body instanceof FormData) && !(body instanceof URLSearchParams)) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  const res = await fetch(path, { method, headers, body: payload });
  if (res.status === 401 && Auth.token) {
    Auth.clear();
    location.href = "/login";
  }
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw new Error(formatError(data) || `Request failed (${res.status})`);
  return data;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function formatDateTime(iso) {
  return iso ? new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }) : "";
}

function showError(el, message) {
  el.textContent = message;
  el.hidden = !message;
}

// ---------- Shared listing display helpers ----------

const STATUS_LABELS = {
  listed: "Listed",
  matched: "Matched",
  picked_up: "Picked up",
  delivered: "Delivered",
  expired: "Expired",
  cancelled: "Cancelled",
  rejected: "Rejected (unsafe)",
};

const RISK_LABELS = { low: "Low", medium: "Medium", high: "High", critical: "Critical" };

function formatHours(h) {
  if (h < 1) return `${Math.round(h * 60)} min`;
  return `${h.toFixed(1)} h`;
}

// "in 2.5 h" / "in 40 min" / "overdue"
function timeLeft(iso) {
  const hours = (new Date(iso) - Date.now()) / 3600000;
  return hours <= 0 ? "overdue" : `in ${formatHours(hours)}`;
}

function riskBadge(freshness) {
  if (!freshness) return "";
  const level = freshness.risk_level;
  return `<span class="risk risk-${level}">${freshness.risk_score} · ${RISK_LABELS[level]}</span>`;
}

function renderNav() {
  const nav = document.getElementById("nav");
  if (!nav) return;
  const user = Auth.user;
  if (user && Auth.token) {
    nav.innerHTML = `
      <span class="small">${escapeHtml(user.name)} · ${escapeHtml(user.role)}</span>
      <a href="${Auth.dashboardFor(user.role)}">Dashboard</a>
      <a href="#" id="logout">Log out</a>`;
    document.getElementById("logout").addEventListener("click", (e) => {
      e.preventDefault();
      Auth.clear();
      location.href = "/";
    });
  } else {
    nav.innerHTML = `<a href="/login">Log in</a><a class="btn btn-small" href="/register">Register</a>`;
  }
}

document.addEventListener("DOMContentLoaded", renderNav);
