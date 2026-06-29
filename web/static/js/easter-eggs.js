/**
 * easter-eggs.js — 8 Easter Eggs cachés sur le site
 * Inclure ce script dans chaque page (déjà intégré via ui.js)
 * Chaque easter egg déclenche un toast + optionnellement appelle l'API pour récompenser.
 */

const EE_KEY = "ee_found"; // localStorage key

function getFoundEggs() {
    try { return JSON.parse(localStorage.getItem(EE_KEY) || "[]"); } catch { return []; }
}
function markEggFound(id) {
    const found = getFoundEggs();
    if (found.includes(id)) return false;
    found.push(id);
    localStorage.setItem(EE_KEY, JSON.stringify(found));
    return true;
}

function eeToast(msg, emoji = "🥚") {
    const el = document.createElement("div");
    el.style.cssText = `
        position:fixed;bottom:5rem;left:50%;transform:translateX(-50%) translateY(20px);
        background:#1e2035;border:2px solid #f5c542;border-radius:14px;
        padding:1rem 1.5rem;font-size:1rem;font-weight:700;color:#f5c542;
        box-shadow:0 8px 32px rgba(0,0,0,.6);z-index:9999;text-align:center;
        animation:eeIn .4s cubic-bezier(.34,1.56,.64,1) forwards;
        pointer-events:none;max-width:340px;
    `;
    el.innerHTML = `${emoji} <strong>Easter Egg découvert !</strong><br><span style="font-size:.85rem;color:#e2e4f0">${msg}</span>`;
    document.body.appendChild(el);
    setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity .5s"; setTimeout(() => el.remove(), 500); }, 4000);
}

const style = document.createElement("style");
style.textContent = `@keyframes eeIn { from{opacity:0;transform:translateX(-50%) translateY(30px) scale(.8)} to{opacity:1;transform:translateX(-50%) translateY(0) scale(1)} }`;
document.head.appendChild(style);

// ── EE #1 : Code Konami ──────────────────────────────────────────────────────
const KONAMI = ["ArrowUp","ArrowUp","ArrowDown","ArrowDown","ArrowLeft","ArrowRight","ArrowLeft","ArrowRight","b","a"];
let konamiPos = 0;
document.addEventListener("keydown", e => {
    if (e.key === KONAMI[konamiPos]) {
        konamiPos++;
        if (konamiPos === KONAMI.length) {
            konamiPos = 0;
            if (markEggFound("konami")) {
                eeToast("Code Konami ! +5 Bois offerts 🪵", "⬆️");
                rewardEgg("konami");
            }
        }
    } else { konamiPos = 0; }
});

// ── EE #2 : Cliquer 10× sur le logo nav ────────────────────────────────────
let logoClicks = 0;
let logoTimer = null;
document.addEventListener("click", e => {
    const logo = e.target.closest(".logo, [class*='logo']");
    if (!logo) { if (!e.target.closest("nav")) { logoClicks = 0; } return; }
    logoClicks++;
    clearTimeout(logoTimer);
    logoTimer = setTimeout(() => logoClicks = 0, 3000);
    if (logoClicks >= 10) {
        logoClicks = 0;
        if (markEggFound("logo10")) {
            eeToast("Obsédé du logo ? +3 Pierre offerts 🪨", "🔷");
            rewardEgg("logo10");
        }
    }
});

// ── EE #3 : Rester immobile 30 secondes sur une page ────────────────────────
let idleTimer = null;
function resetIdle() { clearTimeout(idleTimer); idleTimer = setTimeout(onIdle, 30000); }
function onIdle() {
    if (markEggFound("idle30")) {
        eeToast("Tu ne fais rien… Voilà quand même +2 Fer ⚙️", "😴");
        rewardEgg("idle30");
    }
}
["mousemove","keydown","click","scroll","touchstart"].forEach(ev => document.addEventListener(ev, resetIdle));
resetIdle();

// ── EE #4 : Taper "vacances" au clavier n'importe où ───────────────────────
let typedBuffer = "";
document.addEventListener("keydown", e => {
    if (e.ctrlKey || e.altKey || e.metaKey) return;
    if (e.key.length === 1) typedBuffer += e.key.toLowerCase();
    if (typedBuffer.length > 20) typedBuffer = typedBuffer.slice(-20);
    if (typedBuffer.includes("vacances")) {
        typedBuffer = "";
        if (markEggFound("vacances")) {
            eeToast("Tu as tapé 'vacances' ! Ambiance ☀️ — +5 Magie offerts ✨", "☀️");
            rewardEgg("vacances");
        }
    }
});

// ── EE #5 : Triple-clic rapide sur n'importe quelle image ───────────────────
let imgClickCount = 0;
let imgClickTimer = null;
document.addEventListener("click", e => {
    if (!e.target.matches("img")) return;
    imgClickCount++;
    clearTimeout(imgClickTimer);
    imgClickTimer = setTimeout(() => imgClickCount = 0, 600);
    if (imgClickCount >= 3) {
        imgClickCount = 0;
        if (markEggFound("tripleimg")) {
            eeToast("Triple-clic photo ! Paparazzi ? +4 Pierre 🪨", "📸");
            rewardEgg("tripleimg");
        }
    }
});

// ── EE #6 : Ouvrir la console DevTools (détection via resize) ───────────────
let devtoolsOpen = false;
setInterval(() => {
    const threshold = 160;
    const opened = window.outerWidth - window.innerWidth > threshold || window.outerHeight - window.innerHeight > threshold;
    if (opened && !devtoolsOpen) {
        devtoolsOpen = true;
        if (markEggFound("devtools")) {
            eeToast("Tu regardes dans les coulisses 👀 — +3 Cristal 💎", "🛠️");
            rewardEgg("devtools");
        }
    }
    if (!opened) devtoolsOpen = false;
}, 1000);

// ── EE #7 : Sélectionner exactement le texte "Serveur Vacances" ─────────────
document.addEventListener("selectionchange", () => {
    const sel = window.getSelection()?.toString().trim();
    if (sel === "Serveur Vacances") {
        if (markEggFound("selectname")) {
            eeToast("Tu as sélectionné notre nom 😏 — +2 Magie ✨", "✍️");
            rewardEgg("selectname");
        }
    }
});

// ── EE #8 : Scroller tout en bas d'une page (footer) ───────────────────────
window.addEventListener("scroll", () => {
    const atBottom = (window.innerHeight + window.scrollY) >= document.body.scrollHeight - 20;
    if (atBottom) {
        if (markEggFound("scrollbottom")) {
            eeToast("Explorateur du bas de page ! +3 Bois 🪵", "📜");
            rewardEgg("scrollbottom");
        }
    }
}, { passive: true });

// ── Récompense API ───────────────────────────────────────────────────────────
async function rewardEgg(eggId) {
    const token = localStorage.getItem("jwt_token");
    if (!token) return;
    try {
        await fetch("https://vacances-bot-web.onrender.com/api/easter-egg/claim", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify({ egg_id: eggId })
        });
    } catch(_) {} // Silencieux si offline
}

// ── Compteur affiché en console ─────────────────────────────────────────────
const found = getFoundEggs();
console.log(`%c🥚 Easter Eggs trouvés : ${found.length} / 8`, "color:#f5c542;font-size:14px;font-weight:bold");
if (found.length > 0) console.log("%cDéjà trouvés :", "color:#7a7f9a", found.join(", "));
