/**
 * Auth guard — include this script in any protected page.
 *
 * Checks for a valid JWT token in localStorage. If missing or expired,
 * redirects to /login. Exposes helper functions for token management.
 *
 * Usage: <script src="/static/auth-guard.js"></script>
 */

const AuthGuard = (() => {
    const API = '/api/v1';
    const TOKEN_KEY = 'daleel_access_token';
    const REFRESH_KEY = 'daleel_refresh_token';
    const USER_KEY = 'daleel_user';

    function getAccessToken() {
        return localStorage.getItem(TOKEN_KEY);
    }

    function getRefreshToken() {
        return localStorage.getItem(REFRESH_KEY);
    }

    function getUser() {
        try {
            return JSON.parse(localStorage.getItem(USER_KEY));
        } catch {
            return null;
        }
    }

    function setTokens(access, refresh) {
        localStorage.setItem(TOKEN_KEY, access);
        if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
    }

    function setUser(user) {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
    }

    function clearAuth() {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_KEY);
        localStorage.removeItem(USER_KEY);
    }

    function logout() {
        clearAuth();
        window.location.href = '/login';
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

    function isTokenExpired(token) {
        try {
            const payload = decodeJwtPayload(token);
            return payload.exp * 1000 < Date.now();
        } catch {
            return true;
        }
    }

    async function refreshAccessToken() {
        const refreshToken = getRefreshToken();
        if (!refreshToken || isTokenExpired(refreshToken)) {
            return false;
        }
        try {
            const res = await fetch(`${API}/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken }),
            });
            if (!res.ok) return false;
            const data = await res.json();
            setTokens(data.access_token, data.refresh_token);
            setUser(data.user);
            return true;
        } catch {
            return false;
        }
    }

    function authHeaders() {
        const token = getAccessToken();
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }

    async function authFetch(url, options = {}) {
        let token = getAccessToken();

        if (!token || isTokenExpired(token)) {
            const refreshed = await refreshAccessToken();
            if (!refreshed) {
                logout();
                throw new Error('Session expired');
            }
            token = getAccessToken();
        }

        const headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`,
        };

        let res = await fetch(url, { ...options, headers });

        if (res.status === 401) {
            const refreshed = await refreshAccessToken();
            if (!refreshed) {
                logout();
                throw new Error('Session expired');
            }
            headers['Authorization'] = `Bearer ${getAccessToken()}`;
            res = await fetch(url, { ...options, headers });
        }

        return res;
    }

    function requireAuth() {
        const token = getAccessToken();
        if (!token || isTokenExpired(token)) {
            const refreshToken = getRefreshToken();
            if (!refreshToken || isTokenExpired(refreshToken)) {
                window.location.href = '/login';
                return false;
            }
        }
        return true;
    }

    function requireRole(...roles) {
        const user = getUser();
        if (!user || !roles.includes(user.role)) {
            return false;
        }
        return true;
    }

    return {
        getAccessToken,
        getRefreshToken,
        getUser,
        setTokens,
        setUser,
        clearAuth,
        logout,
        decodeJwtPayload,
        isTokenExpired,
        refreshAccessToken,
        authHeaders,
        authFetch,
        requireAuth,
        requireRole,
    };
})();

document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    const publicPages = ['/login', '/register', '/invite'];
    if (!publicPages.includes(path)) {
        AuthGuard.requireAuth();
    }
});
