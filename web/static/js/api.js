/**
 * api.js — Client API centralisé
 * Toutes les pages importent ce fichier.
 */

const API_BASE = "https://vacances-bot-web.onrender.com"; // ← à remplacer

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
    // Profil & Classement (Déjà existants)
    getProfile:      ()           => apiFetch("/api/profile"),
    getLeaderboard:  ()           => apiFetch("/api/leaderboard"),

    // Boutique (Déjà existant)
    getShop:         ()           => apiFetch("/api/shop"),
    buyItem:         (item, qty)  => apiFetch("/api/shop/buy", {
        method: "POST",
        body: JSON.stringify({ item, quantity: qty }),
    }),

    // ✨ NOUVEAU : Histoire / Lore / Tutoriel
    getStoryProgress: ()          => apiFetch("/api/story/tutorial/progress"),
    completeTutorial: ()          => apiFetch("/api/story/tutorial/progress", {
        method: "POST",
        body: JSON.stringify({ step: "DONE" }),
    }),

    // ✨ NOUVEAU : Système One Bloc
    getOneBlockState: ()          => apiFetch("/api/oneblock/state"),
    mineOneBlock:     ()          => apiFetch("/api/oneblock/mine", { method: "POST" }),

    // ✨ NOUVEAU : Marchand (Vente de matériaux)
    sellResources:    (resource, qty) => apiFetch("/api/merchant/sell", {
        method: "POST",
        body: JSON.stringify({ item: resource, quantity: qty })
    }),

    // ✨ NOUVEAU : Forge (Craft d'équipement)
    getForgeRecipes:  ()          => apiFetch("/api/forge/recipes"),
    craftEquipment:   (recipeKey)  => apiFetch("/api/forge/craft", {
        method: "POST",
        body: JSON.stringify({ recipe_key: recipeKey })
    }),

    // ✨ NOUVEAU : Inventaire & Équipement
    getInventory:     ()          => apiFetch("/api/inventory"),
    equipItem:        (itemKey)   => apiFetch("/api/inventory/equip", {
        method: "POST",
        body: JSON.stringify({ item_key: itemKey })
    }),

    // ✨ NOUVEAU : Système de Boss
    getBossState:     ()          => apiFetch("/api/boss/state"),
    attackBoss:       ()          => apiFetch("/api/boss/attack", { method: "POST" }),

    // ✨ NOUVEAU : Épreuves de l'Arbre Monde
    completeTrial:    (nodeId)    => apiFetch("/api/skilltree/trial/complete", {
        method: "POST",
        body: JSON.stringify({ node_id: nodeId })
    }),

    // Skill Tree & Pixel Map (Garder tes fonctions de base)
    getSkillTree:    ()           => apiFetch("/api/skilltree"),
    unlockNode:      (node)       => apiFetch("/api/skilltree/unlock", {
        method: "POST",
        body: JSON.stringify({ node }),
    }),
    getPixelMap:     (world)      => apiFetch(`/api/pixelmap/${world}`),
    placePixel:      (world, x, y, color) => apiFetch(`/api/pixelmap/${world}/place`, {
        method: "POST",
        body: JSON.stringify({ x, y, color }),
    }),

    // Classes (legacy — gardé pour compat, mais la classe vient maintenant du Gacha)
    getClasses:      ()           => apiFetch("/api/classes"),
    chooseClass:     (classe)     => apiFetch("/api/classes/choose", {
        method: "POST",
        body: JSON.stringify({ classe }),
    }),

    // Gacha
    getGachaPity:    ()           => apiFetch("/api/gacha/pity/status"),
    pullGacha:       (type)       => apiFetch("/api/gacha/pull", {
        method: "POST",
        body: JSON.stringify({ type }),
    }),

    // Codes promo
    redeemCode:      (code)       => apiFetch("/api/codes/redeem", {
        method: "POST",
        body: JSON.stringify({ code }),
    }),
    checkCode:       (code)       => apiFetch("/api/codes/check", {
        method: "POST",
        body: JSON.stringify({ code }),
    }),

    // One Bloc / Cliqueur
    getOneBlockState: ()          => apiFetch("/api/oneblock/state"),
    mineOneBlock:     ()          => apiFetch("/api/oneblock/mine", { method: "POST" }),
};

// ── Avatar Discord ────────────────────────────────────────────────────────

export function discordAvatar(userId, avatarHash, size = 128) {
    if (!avatarHash) {
        const def = parseInt(userId) % 5;
        return `https://cdn.discordapp.com/embed/avatars/${def}.png`;
    }
    return `https://cdn.discordapp.com/avatars/${userId}/${avatarHash}.png?size=${size}`;
}
