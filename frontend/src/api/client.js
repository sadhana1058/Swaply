// Thin fetch wrapper for the auth API.
// - always sends cookies (credentials: "include")
// - attaches the double-submit CSRF header from the csrf_token cookie
// - transparently refreshes the access token once on a 401, then retries

function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

async function rawRequest(path, { method = "GET", body, headers = {} } = {}) {
  const finalHeaders = { ...headers };
  const csrf = getCookie("csrf_token");
  if (csrf) finalHeaders["X-CSRF-Token"] = csrf;
  if (body !== undefined) finalHeaders["Content-Type"] = "application/json";

  return fetch(path, {
    method,
    credentials: "include",
    headers: finalHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

async function request(path, options = {}) {
  let res = await rawRequest(path, options);

  // Access token likely expired — try one refresh + retry.
  if (res.status === 401 && path !== "/auth/refresh" && path !== "/auth/login") {
    const refreshed = await rawRequest("/auth/refresh", { method: "POST" });
    if (refreshed.ok) {
      res = await rawRequest(path, options);
    }
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const message = (data && data.detail) || `Request failed (${res.status})`;
    throw new Error(message);
  }
  return data;
}

export const api = {
  signup: (payload) => request("/auth/signup", { method: "POST", body: payload }),
  login: (payload) => request("/auth/login", { method: "POST", body: payload }),
  logout: () => request("/auth/logout", { method: "POST" }),
  me: () => request("/auth/me"),
  // Full-page navigation so the browser follows Google's redirects.
  googleLoginUrl: "/auth/google/login",
};
