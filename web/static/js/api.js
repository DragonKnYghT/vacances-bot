/**
 * api.js — Client API centralisé
 * Toutes les pages importent ce fichier.
 */

const API_BASE = "https://TON_BACKEND.onrender.com"; // ← à remplacer

// ── Auth ──────────────────────────────────────────────────────────────────

export function getToken() {
    return localStorage.getItem("jwt_token");
}

export function setToken(token) {
    localStorage.setItem("jwt_token", token);
}

export function clearToken() {
    localStorage.removeItem("jwt_token");
}

export function isLoggedIn() {
    return !!getToken();
}

export function logout() {
    clearToken();
    window.location.href = "index.html";
}

/** Redirige vers le login Discord */
export function loginWithDiscord() {
    window.location.href = `${API_BASE}/auth/login`;
}

// ── Fetch helper ──────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
    const token = getToken();
    const headers = {
        "Content-Type": "application/json",
        ...(token ? { "Authorization": `Bearer ${token}` } : {}),
        ...options.headers,
    };

    const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });

    if (resp.status === 401) {
        clearToken();
        window.location.href = "index.html";
        return;
    }

    if (!resp.ok) {
        const err = await resp.json().catch(() => ({ error: "Erreur réseau" }));
        throw new Error(err.error || `HTTP ${resp.status}`);
    }

    return resp.json();
}

// ── Endpoints ─────────────────────────────────────────────────────────────

export const api = {
    // Profil
    getProfile:      ()           => apiFetch("/api/profile"),
    getLeaderboard:  ()           => apiFetch("/api/leaderboard"),

    // Boutique
    getShop:         ()           => apiFetch("/api/shop"),
    buyItem:         (item, qty)  => apiFetch("/api/shop/buy", {
        method: "POST",
        body: JSON.stringify({ item, quantity: qty }),
    }),

    // Skill Tree
    getSkillTree:    ()           => apiFetch("/api/skilltree"),
    unlockNode:      (node)       => apiFetch("/api/skilltree/unlock", {
        method: "POST",
        body: JSON.stringify({ node }),
    }),

    // Pixel Map
    getPixelMap:     (world)      => apiFetch(`/api/pixelmap/${world}`),
    placePixel:      (world, x, y, color) => apiFetch(`/api/pixelmap/${world}/place`, {
        method: "POST",
        body: JSON.stringify({ x, y, color }),
    }),

    // Classes
    getClasses:      ()           => apiFetch("/api/classes"),
    chooseClass:     (classe)     => apiFetch("/api/classes/choose", {
        method: "POST",
        body: JSON.stringify({ classe }),
    }),
};

// ── Avatar Discord ────────────────────────────────────────────────────────

export function discordAvatar(userId, avatarHash, size = 128) {
    if (!avatarHash) {
        const def = parseInt(userId) % 5;
        return `https://cdn.discordapp.com/embed/avatars/${def}.png`;
    }
    return `https://cdn.discordapp.com/avatars/${userId}/${avatarHash}.png?size=${size}`;
}
