const API = '/api/v1';
const TOKEN_KEY = 'daleel_access_token';
const USER_KEY = 'daleel_user';

// Note: the refresh token is now stored by the backend in an HttpOnly cookie
// (`daleel_refresh`, scoped to /api/v1/auth). The frontend never reads or
// writes it. `credentials: 'include'` on the /auth/refresh call is what
// carries it back to the server.

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY));
  } catch {
    return null;
  }
}

export function setTokens(access /* , refresh — ignored, cookie-based now */) {
  localStorage.setItem(TOKEN_KEY, access);
}

export function setUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  // Legacy key from earlier versions — clear it too on logout / session loss.
  localStorage.removeItem('daleel_refresh_token');
  window.dispatchEvent(new Event('auth:session-lost'));
}

function decodeJwtPayload(token) {
  const parts = token.split('.');
  if (parts.length < 2) throw new Error('Invalid token');
  let base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
  const padding = base64.length % 4;
  if (padding) base64 += '='.repeat(4 - padding);
  const binary = atob(base64);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return JSON.parse(new TextDecoder().decode(bytes));
}

export function isTokenExpired(token) {
  try {
    const payload = decodeJwtPayload(token);
    return payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}

export async function refreshAccessToken() {
  try {
    const res = await fetch(`${API}/auth/refresh`, {
      method: 'POST',
      credentials: 'include', // send HttpOnly refresh cookie
      headers: { 'Content-Type': 'application/json' },
      body: '{}',
    });
    if (!res.ok) return false;
    const data = await res.json();
    setTokens(data.access_token);
    setUser(data.user);
    return true;
  } catch {
    return false;
  }
}

export function authHeaders() {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function authFetch(url, options = {}) {
  let token = getAccessToken();
  if (!token) {
    const refreshed = await refreshAccessToken();
    if (!refreshed) {
      clearAuth();
      throw new Error('Session expired');
    }
    token = getAccessToken();
  }
  try {
    if (isTokenExpired(token)) {
      const refreshed = await refreshAccessToken();
      if (!refreshed) {
        throw new Error('Session expired');
      }
      token = getAccessToken();
    }
  } catch (err) {
    if (err.message === 'Session expired') {
      clearAuth();
      throw err;
    }
    // token decode failed — use token as-is
  }
  const headers = { ...options.headers, Authorization: `Bearer ${token}` };
  const res = await fetch(url, { ...options, headers });
  if (res.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      headers.Authorization = `Bearer ${getAccessToken()}`;
      return fetch(url, { ...options, headers });
    }
    clearAuth();
    throw new Error('Session expired');
  }
  return res;
}

export async function logout() {
  try {
    const token = getAccessToken();
    if (token) {
      await fetch(`${API}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: { Authorization: `Bearer ${token}` },
      });
    }
  } catch {
    // best-effort server-side logout
  }
  clearAuth();
  window.location.href = '/';
}

export function requireRole(...roles) {
  const user = getUser();
  return user && roles.includes(user.role);
}
