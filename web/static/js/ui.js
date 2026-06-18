/**
 * ui.js — Composants UI partagés (nav, toast, loader)
 */

import { isLoggedIn, logout, getToken, discordAvatar } from "./api.js";

// ── Nav ───────────────────────────────────────────────────────────────────

export function renderNav(activePage = "") {
    const nav = document.createElement("nav");
    nav.innerHTML = `
        <span class="logo">🏰 Serveur Vacances</span>
        <a href="profile.html" ${activePage === "profile" ? 'class="active"' : ""}>Profil</a>
        <a href="oneblock.html" ${activePage === "oneblock" ? 'class="active"' : ""}>⛏️ One Bloc</a>
        <a href="shop.html"    ${activePage === "shop"    ? 'class="active"' : ""}>Boutique</a>
        <a href="skilltree.html" ${activePage === "skilltree" ? 'class="active"' : ""}>Skill Tree</a>
        <a href="pixelmap.html"  ${activePage === "pixelmap"  ? 'class="active"' : ""}>Pixel Map</a>
        <a href="leaderboard.html" ${activePage === "leaderboard" ? 'class="active"' : ""}>Classement</a>
        <a href="gacha.html" ${activePage === "gacha" ? 'class="active"' : ""}>🎰 Gacha</a>
        <a href="codes.html" ${activePage === "codes" ? 'class="active"' : ""}>🎁 Codes</a>
        <div id="nav-user" style="display:flex;align-items:center;gap:.6rem;margin-left:.5rem"></div>
    `;
    document.body.prepend(nav);
}

export async function loadNavUser() {
    const el = document.getElementById("nav-user");
    if (!el || !isLoggedIn()) return;
    try {
        const { getProfile } = await import("./api.js");
        // On utilise le profil déjà chargé sur la page si dispo
        const profile = window.__profile;
        if (!profile) return;
        const avatarUrl = discordAvatar(profile.user_id, profile.avatar, 64);
        el.innerHTML = `
            <img id="nav-avatar" src="${avatarUrl}" alt="avatar" crossorigin="anonymous" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
            <span id="nav-username">${profile.global_name || profile.username || "Joueur"}</span>
            <button class="btn-outline" style="font-size:.8rem;padding:.3rem .8rem" onclick="import('./static/js/api.js').then(m=>m.logout())">Déco</button>
        `;
    } catch (_) {}
}

// ── Toast ─────────────────────────────────────────────────────────────────

let toastContainer;

function getToastContainer() {
    if (!toastContainer) {
        toastContainer = document.createElement("div");
        toastContainer.id = "toast-container";
        document.body.appendChild(toastContainer);
    }
    return toastContainer;
}

export function toast(message, type = "info", duration = 3500) {
    const c = getToastContainer();
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = message;
    c.appendChild(el);
    setTimeout(() => el.remove(), duration);
}

// ── Loader ────────────────────────────────────────────────────────────────

export function showLoader(container, message = "Chargement...") {
    container.innerHTML = `
        <div class="loader">
            <div class="spinner"></div>
            <span>${message}</span>
        </div>`;
}

// ── Guard : redirige si pas connecté ──────────────────────────────────────

export function requireAuth() {
    if (!isLoggedIn()) {
        window.location.href = "index.html";
        return false;
    }
    return true;
}

// ── Format nombre ──────────────────────────────────────────────────────────

export function fmt(n) {
    return Number(n || 0).toLocaleString("fr-FR");
}
