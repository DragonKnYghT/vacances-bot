/**
 * api.js — Client API centralisé
 * Toutes les pages importent ce fichier.
 */

const API_BASE = (window.__API_BASE__ || "https://vacances-bot-web.onrender.com").replace(/\/$/, "");

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
        body: JSON.stringify({ recipe: recipeKey })
    }),

    // ✨ NOUVEAU : Inventaire & Équipement
    getInventory:     ()          => apiFetch("/api/inventory"),
    equipItem:        (itemId)    => apiFetch("/api/inventory/equip", {
        method: "POST",
        body: JSON.stringify({ id: itemId })
    }),

    // ✨ NOUVEAU : Système de Boss
    getBossState:     ()          => apiFetch("/api/boss/status"),
    attackBoss:       ()          => apiFetch("/api/boss/attack", { method: "POST" }),

    // ✨ NOUVEAU : Épreuves de l'Arbre Monde
    completeTrial:   (node, success) => apiFetch("/api/skilltree/trial/complete", {
        method: "POST",
        body: JSON.stringify({ node, success }),
    }),

    // Skill Tree (par monde, 2 arbres : base + player)
    getSkillTree:    (world)      => apiFetch(`/api/skilltree/${world}`),
    unlockNode:      (world, node, tree) => apiFetch(`/api/skilltree/${world}/unlock`, {
        method: "POST",
        body: JSON.stringify({ node, tree }),
    }),
    getPixelMap:     (world, playerId) => apiFetch(`/api/pixelmap/${world}${playerId ? `?player_id=${encodeURIComponent(playerId)}` : ""}`),
    getPixelMapGallery: (world)   => apiFetch(`/api/pixelmap/${world}/gallery`),
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
    getGachaInfo:    ()           => apiFetch("/api/gacha/info"),
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

    // Quêtes quotidiennes
    getDailyQuest:   ()           => apiFetch("/api/quests/daily"),
    claimQuest:      ()           => apiFetch("/api/quests/claim", { method: "POST" }),

    // Easter Eggs
    claimEasterEgg:  (eggId)      => apiFetch("/api/easter-egg/claim", {
        method: "POST",
        body: JSON.stringify({ egg_id: eggId }),
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
