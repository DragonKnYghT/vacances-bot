"""
Backend Flask pour le site web du bot Discord.
Hébergé sur Render dans le même repo, dossier /web/
"""

import os
import requests
from flask import Flask, redirect, request, jsonify, session, url_for
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
import jwt
from functools import wraps
import random as _random

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://dragonknyght.github.io",
            "https://DragonKnYghT.github.io",
            "http://localhost:3000",
            "http://127.0.0.1:5500",
            "http://127.0.0.1:5501"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": False
    }
})

# Fix CORS manuel pour les OPTIONS preflight (certaines routes Flask ratent le preflight)
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "")
    allowed = [
        "https://dragonknyght.github.io",
        "https://DragonKnYghT.github.io",
        "http://localhost:3000",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:5501",
    ]
    if origin.lower() in [a.lower() for a in allowed]:
        response.headers["Access-Control-Allow-Origin"]  = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.route("/api/<path:path>", methods=["OPTIONS"])
def handle_options(path):
    """Répond 200 à tous les preflight OPTIONS sur /api/*"""
    resp = app.make_default_options_response()
    return resp

# ── MongoDB ──────────────────────────────────────────────────────────────────
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["vacances_bot"]      # ← même DB que le bot

# ── Discord OAuth2 ───────────────────────────────────────────────────────────
DISCORD_CLIENT_ID     = os.environ.get("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI  = os.environ.get("DISCORD_REDIRECT_URI")   # ex: https://ton-backend.onrender.com/auth/callback
DISCORD_API_BASE      = "https://discord.com/api/v10"

JWT_SECRET  = os.environ.get("JWT_SECRET", "jwt-secret-change-me")
JWT_EXPIRES = 7  # jours

# ── Classes disponibles ──────────────────────────────────────────────────────
CLASSES = {
    "guerrier": {
        "name": "Guerrier ⚔️",
        "description": "Réductions sur les améliorations de défense",
        "bonuses": {"upgrade_discount": 0.15, "pixel_cost": 1.0, "shop_discount": 0.0}
    },
    "mage": {
        "name": "Mage 🔮",
        "description": "Bonus de points sur les quiz et activités",
        "bonuses": {"upgrade_discount": 0.0, "pixel_cost": 1.0, "shop_discount": 0.10}
    },
    "architecte": {
        "name": "Architecte 🏗️",
        "description": "Pose de pixels moins chère",
        "bonuses": {"upgrade_discount": 0.0, "pixel_cost": 0.5, "shop_discount": 0.0}
    },
    "marchand": {
        "name": "Marchand 💰",
        "description": "Réductions sur tous les achats en boutique",
        "bonuses": {"upgrade_discount": 0.0, "pixel_cost": 1.0, "shop_discount": 0.20}
    },
    "explorateur": {
        "name": "Explorateur 🗺️",
        "description": "Débloque les nouvelles maps plus vite",
        "bonuses": {"upgrade_discount": 0.0, "pixel_cost": 1.0, "shop_discount": 0.0, "map_discount": 0.25}
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# GACHA — Les Configurations de Rareté & Objets de collection
# ─────────────────────────────────────────────────────────────────────────────

RARITIES = {
    "commun":    {"label": "Commun",    "color": "#7a7f9a", "chance": 55},
    "rare":      {"label": "Rare",      "color": "#5ca8f0", "chance": 30},
    "epique":    {"label": "Épique",    "color": "#7c5cfc", "chance": 12},
    "legendaire":{"label": "Légendaire","color": "#f5c542", "chance": 3},
}

GACHA_CLASSES = [
    {"id":"soldat",      "name":"Soldat ⚔️",        "rarity":"commun",    "bonus":"Résistance +10% dégâts","upgrade_discount":0.05,"shop_discount":0.0,"pixel_cost":1.0},
    {"id":"paysan",      "name":"Paysan 🌾",         "rarity":"commun",    "bonus":"Matériaux +5% à la récolte","upgrade_discount":0.0,"shop_discount":0.05,"pixel_cost":1.0},
    {"id":"marchand",    "name":"Marchand 💰",       "rarity":"commun",    "bonus":"-20% en boutique","upgrade_discount":0.0,"shop_discount":0.20,"pixel_cost":1.0},
    {"id":"eclaireur",   "name":"Éclaireur 🗺️",     "rarity":"commun",    "bonus":"Maps débloquées +vite","upgrade_discount":0.0,"shop_discount":0.0,"pixel_cost":1.0,"map_discount":0.15},
    {"id":"guerrier",    "name":"Guerrier 🛡️",      "rarity":"rare",      "bonus":"-15% améliorations","upgrade_discount":0.15,"shop_discount":0.0,"pixel_cost":1.0},
    {"id":"architecte",  "name":"Architecte 🏗️",   "rarity":"rare",      "bonus":"Pixels à moitié prix","upgrade_discount":0.0,"shop_discount":0.0,"pixel_cost":0.5},
    {"id":"alchimiste",  "name":"Alchimiste ⚗️",    "rarity":"rare",      "bonus":"-20% matériaux spéciaux","upgrade_discount":0.0,"shop_discount":0.15,"pixel_cost":1.0},
    {"id":"barde",       "name":"Barde 🎵",          "rarity":"rare",      "bonus":"+2pts par activité","upgrade_discount":0.0,"shop_discount":0.0,"pixel_cost":1.0,"activity_bonus":2},
    {"id":"mage",        "name":"Mage 🔮",           "rarity":"epique",    "bonus":"-10% boutique + bonus quiz","upgrade_discount":0.0,"shop_discount":0.10,"pixel_cost":1.0,"activity_bonus":3},
    {"id":"paladin",     "name":"Paladin ✨",        "rarity":"epique",    "bonus":"-20% améliorations + résistance","upgrade_discount":0.20,"shop_discount":0.0,"pixel_cost":1.0},
    {"id":"ninja",       "name":"Ninja 🥷",          "rarity":"epique",    "bonus":"Pixels ×3 par achat","upgrade_discount":0.0,"shop_discount":0.0,"pixel_cost":0.33,"pixel_triple":True},
    {"id":"druide",      "name":"Druide 🌿",         "rarity":"epique",    "bonus":"Matériaux nature ×2","upgrade_discount":0.05,"shop_discount":0.10,"pixel_cost":0.8},
    {"id":"roi",         "name":"Roi 👑",            "rarity":"legendaire","bonus":"TOUT -25%","upgrade_discount":0.25,"shop_discount":0.25,"pixel_cost":0.75},
    {"id":"sorcier",     "name":"Sorcier Noir 🧙",   "rarity":"legendaire","bonus":"+5pts toutes activités + pixels gratuits","upgrade_discount":0.0,"shop_discount":0.0,"pixel_cost":0.0,"activity_bonus":5},
    {"id":"titan",       "name":"Titan ⚡",          "rarity":"legendaire","bonus":"Double points vocal/messages","upgrade_discount":0.10,"shop_discount":0.10,"pixel_cost":0.5},
]

GACHA_RACES = [
    {"id":"humain",      "name":"Humain 🧑",         "rarity":"commun",    "bonus":"+5% tous les points"},
    {"id":"gobelin",     "name":"Gobelin 👺",        "rarity":"commun",    "bonus":"Prix boutique -5%"},
    {"id":"orc",         "name":"Orc 💪",             "rarity":"commun",    "bonus":"Points vocal +10%"},
    {"id":"halfelin",    "name":"Halfelin 🍀",       "rarity":"commun",    "bonus":"Chance gacha +2%"},
    {"id":"elfe",        "name":"Elfe 🧝",           "rarity":"rare",      "bonus":"Points messages +15%"},
    {"id":"nain",        "name":"Nain ⛏️",           "rarity":"rare",      "bonus":"Matériaux -10%"},
    {"id":"demon",       "name":"Démon 😈",          "rarity":"rare",      "bonus":"Points activités +10%"},
    {"id":"beastman",    "name":"Homme-Bête 🐾",     "rarity":"rare",      "bonus":"Points vocal +20%"},
    {"id":"dragon",      "name":"Semi-Dragon 🐉",    "rarity":"epique",    "bonus":"Pixels +50% par achat"},
    {"id":"ange",        "name":"Ange 😇",           "rarity":"epique",    "bonus":"-20% toute la boutique"},
    {"id":"fantome",     "name":"Fantôme 👻",        "rarity":"epique",    "bonus":"Réapparaît 1×/sem si éliminé"},
    {"id":"necromant",   "name":"Nécromanien 💀",    "rarity":"epique",    "bonus":"Récupère 50% mat. dépensés"},
    {"id":"phenix",      "name":"Phénix 🔥",         "rarity":"legendaire","bonus":"Reroll gratuit 1×/semaine"},
    {"id":"celeste",     "name":"Être Céleste ⭐",   "rarity":"legendaire","bonus":"Tous les bonus ×1.5"},
    {"id":"ancien",      "name":"Ancien 🌌",         "rarity":"legendaire","bonus":"Incontournable"}
]

# ── Mondes / maps pixel ──────────────────────────────────────────────────────
WORLDS = {
    "monde_1": {"name": "La Forêt des Débuts", "required_nodes": [], "grid_size": 100},
    "monde_2": {"name": "Les Plaines de Feu",  "required_nodes": ["foret_complete"], "grid_size": 100},
    "monde_3": {"name": "L'Océan Profond",      "required_nodes": ["plaines_complete"], "grid_size": 100},
    "monde_4": {"name": "Le Sommet des Dieux", "required_nodes": ["ocean_complete"], "grid_size": 100},
}

# ── Boutique ─────────────────────────────────────────────────────────────────
SHOP_ITEMS = {
    "pierre":   {"name": "Pierre 🪨",    "price": 10,  "category": "materiau", "sell_price": 5},
    "bois":     {"name": "Bois 🪵",      "price": 8,   "category": "materiau", "sell_price": 4},
    "fer":      {"name": "Fer ⚙️",       "price": 25,  "category": "materiau", "sell_price": 12},
    "cristal":  {"name": "Cristal 💎",   "price": 60,  "category": "materiau", "sell_price": 30},
    "magie":    {"name": "Essence magique ✨", "price": 100, "category": "special", "sell_price": 50},
    "pixel_1":  {"name": "Pack Pixels ×10 🎨", "price": 50, "category": "pixel"},
    "ticket_classe": {"name": "Ticket Classe 🎫", "price": 80, "category": "gacha"},
    "ticket_race":   {"name": "Ticket Race 🎟️",  "price": 80, "category": "gacha"},
    "ticket_duo":    {"name": "Duo Classe+Race 🎰","price": 140,"category": "gacha"},
}

# ── Skill tree (L'Arbre Monde Réorganisé en 2 Arbres distincts) ─────────────────
# 1. L'Arbre Monde (Amélioration de la Base globale)
SKILL_TREE_BASE = {
    "salle_reunion": {
        "name": "Salle de réunion",
        "description": "Permet de lancer des votes serveur",
        "cost": {"pierre": 5, "bois": 3},
        "requires": [],
        "position": {"x": 400, "y": 50},
        "unlocks": "monde_vote",
        "trial": None
    },
    "forge": {
        "name": "La Forge",
        "description": "Débloque la forge d'équipement (Disponible au Monde 2)",
        "cost": {"pierre": 10, "fer": 5},
        "requires": ["salle_reunion"],
        "position": {"x": 200, "y": 200},
        "trial": "test_your_might" # Exige l'épreuve Test Your Might !
    },
    "bibliotheque": {
        "name": "Bibliothèque",
        "description": "Bonus de +2pts sur les quiz (Demande une épreuve de rythme)",
        "cost": {"bois": 15, "cristal": 2},
        "requires": ["salle_reunion"],
        "position": {"x": 600, "y": 200},
        "trial": "osu_rhythm" # Exige l'épreuve OSU !
    },
    "foret_complete": {
        "name": "Maîtrise de la Forêt",
        "description": "Débloque le Monde 2 - Plaines de Feu",
        "cost": {"pierre": 20, "bois": 20, "fer": 10},
        "requires": ["forge", "bibliotheque"],
        "position": {"x": 400, "y": 350},
        "unlocks": "monde_2",
        "trial": None
    },
    "plaines_complete": {
        "name": "Maîtrise des Plaines",
        "description": "Débloque le Monde 3 - Océan Profond",
        "cost": {"fer": 30, "cristal": 10, "magie": 2},
        "requires": ["foret_complete"],
        "position": {"x": 400, "y": 500},
        "unlocks": "monde_3",
        "trial": None
    },
    "ocean_complete": {
        "name": "Maîtrise de l'Océan",
        "description": "Débloque le Monde 4 - Sommet des Dieux",
        "cost": {"cristal": 30, "magie": 10},
        "requires": ["plaines_complete"],
        "position": {"x": 400, "y": 650},
        "unlocks": "monde_4",
        "trial": None
    },
}

# 2. L'Arbre du Joueur (Améliorations de Statistiques Personnelles)
SKILL_TREE_PLAYER = {
    "clics_efficaces": {
        "name": "Clics Efficaces",
        "description": "+1 bloc brisé supplémentaire par clic sur le One Bloc",
        "cost": {"bois": 10},
        "requires": [],
        "position": {"x": 950, "y": 50},
        "trial": None
    },
    "chance_accrue": {
        "name": "Chance Initiale",
        "description": "+2% de chance globale sur les tirages du Gacha",
        "cost": {"cristal": 5},
        "requires": ["clics_efficaces"],
        "position": {"x": 950, "y": 230},
        "trial": "osu_rhythm"
    },
    "fureur_du_gardien": {
        "name": "Fureur du Gardien",
        "description": "+15% de dégâts contre les boss du serveur",
        "cost": {"fer": 15, "magie": 1},
        "requires": ["chance_accrue"],
        "position": {"x": 950, "y": 410},
        "trial": "test_your_might"
    }
}

# Pour maintenir la rétrocompatibilité globale, on garde l'ancien pointeur combiné
SKILL_TREE = {**SKILL_TREE_BASE, **SKILL_TREE_PLAYER}

# ── Recettes de la Forge ─────────────────────────────────────────────────────
FORGE_RECIPES = {
    "wooden_pickaxe": {"name": "Pioche en Bois 🪵", "type": "tool", "cost": {"bois": 5}, "stat": 1, "desc": "Permet de casser le One Bloc."},
    "wooden_sword": {"name": "Épée en Bois 🪵", "type": "weapon", "cost": {"bois": 8}, "stat": 10, "desc": "Une épée simple reçue à la fin du tutoriel."},
    "iron_sword": {"name": "Épée en Fer ⚙️", "type": "weapon", "cost": {"fer": 12, "bois": 3}, "stat": 35, "desc": "Idéale pour entamer les combats de boss."},
    "crystal_staff": {"name": "Bâton de Cristal 💎", "type": "weapon", "cost": {"cristal": 10, "magie": 3}, "stat": 80, "desc": "Déchaîne l'énergie de l'Arbre Monde."}
}

# ── Les Gardiens / Boss des Mondes ───────────────────────────────────────────
BOSSES = {
    "monde_1": {"id": "boss_1", "name": "Le Tronc Corrompu 🌲", "max_hp": 500, "reward_points": 200},
    "monde_2": {"id": "boss_2", "name": "L'Esprit des Cendres 🔥", "max_hp": 2500, "reward_points": 500},
    "monde_3": {"id": "boss_3", "name": "Le Léviathan Saturé 🌊", "max_hp": 10000, "reward_points": 1200},
    "monde_4": {"id": "boss_4", "name": "Le Gardien Primordial ⛰️", "max_hp": 50000, "reward_points": 3000},
}

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_jwt(user_id: str, discord_token: str) -> str:
    payload = {
        "user_id": user_id,
        "discord_token": discord_token,
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Décorateur : vérifie le JWT dans le header Authorization: Bearer <token>"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Non authentifié"}), 401
        token = auth[7:]
        payload = decode_jwt(token)
        if not payload:
            return jsonify({"error": "Token invalide ou expiré"}), 401
        request.user_id = payload["user_id"]
        request.discord_token = payload["discord_token"]
        return f(*args, **kwargs)
    return decorated

def get_user_doc(user_id: str) -> dict:
    """Récupère ou crée le document utilisateur dans MongoDB avec toutes les structures RPG."""
    doc = db.users.find_one({"user_id": user_id})
    
    # Valeurs par défaut du système RPG à injecter si absentes
    default_rpg_fields = {
        "user_id": user_id,
        "points": 0,
        "vocal_points": 0,
        "message_points": 0,
        "activity_points": 0,
        "minigame_points": 0,
        "spent_points": 0,
        "classe": None,
        "race": None,
        "tickets_classe": 0,
        "tickets_race": 0,
        "classe_history": [],
        "race_history": [],
        "materials": {"bois": 0, "pierre": 0, "fer": 0, "cristal": 0, "magie": 0},
        "pixels_remaining": 0,
        "unlocked_worlds": ["monde_1"],
        "unlocked_nodes": [],
        "completed_trials": [],       # Épreuves de l'arbre réussies
        "tutorial_progress": "START",  # Suivi histoire : START, ONE_BLOC_INTRO, EQUIP_SWORD, DONE
        "one_block": {"phase": 1, "broken": 0, "next": "bois"},
        "inventory": [],               # Contient les dictionnaires d'équipements possédés
        "gacha_pity": {"total_pulls": 0, "current_step": 0, "bonus_chance": 0.0},
        "boss_progress": {"boss_1": 500, "boss_2": 2500, "boss_3": 10000, "boss_4": 50000}, # Vie restante
        "created_at": datetime.utcnow()
    }

    if not doc:
        doc = default_rpg_fields
        db.users.insert_one(doc)
    else:
        # Sécurité & initialisation des nouveaux champs RPG sur les comptes existants
        updates = {}
        for key, value in default_rpg_fields.items():
            if key not in doc:
                doc[key] = value
                updates[key] = value
        
        # Double sécurité pour les sous-dictionnaires
        if "materials" in doc and not isinstance(doc["materials"], dict):
            doc["materials"] = default_rpg_fields["materials"]
            updates["materials"] = default_rpg_fields["materials"]
        if "one_block" not in doc or not isinstance(doc["one_block"], dict):
            doc["one_block"] = default_rpg_fields["one_block"]
            updates["one_block"] = default_rpg_fields["one_block"]
        if "gacha_pity" not in doc or not isinstance(doc["gacha_pity"], dict):
            doc["gacha_pity"] = default_rpg_fields["gacha_pity"]
            updates["gacha_pity"] = default_rpg_fields["gacha_pity"]
        if "boss_progress" not in doc or not isinstance(doc["boss_progress"], dict):
            doc["boss_progress"] = default_rpg_fields["boss_progress"]
            updates["boss_progress"] = default_rpg_fields["boss_progress"]

        if updates:
            db.users.update_one({"user_id": user_id}, {"$set": updates})
            
    return doc

def apply_class_discount(user_doc: dict, item_key: str, base_price: int) -> int:
    user_classe = user_doc.get("classe")
    if not user_classe or user_classe == "Aucune":
        return base_price

    classe_meta = next((c for c in GACHA_CLASSES if c["id"] == user_classe), None)
    if not classe_meta:
        classe_meta = CLASSES.get(user_classe)

    if not classe_meta:
        return base_price

    item = SHOP_ITEMS.get(item_key, {})
    if item.get("category") == "pixel":
        pixel_cost_multiplier = classe_meta.get("pixel_cost", 1.0)
        return int(base_price * pixel_cost_multiplier)

    discount = classe_meta.get("shop_discount", 0.0)
    return int(base_price * (1 - discount))

# ─────────────────────────────────────────────────────────────────────────────
# Routes OAuth2
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/auth/login")
def auth_login():
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds.members.read",
    }
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return redirect(f"https://discord.com/api/oauth2/authorize?{qs}")

@app.route("/auth/callback")
def auth_callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Code manquant"}), 400

    token_resp = requests.post(
        f"{DISCORD_API_BASE}/oauth2/token",
        data={
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if not token_resp.ok:
        return jsonify({"error": "Échec échange token Discord"}), 400

    discord_token = token_resp.json()["access_token"]

    user_resp = requests.get(
        f"{DISCORD_API_BASE}/users/@me",
        headers={"Authorization": f"Bearer {discord_token}"},
    )
    if not user_resp.ok:
        return jsonify({"error": "Impossible de récupérer l'utilisateur"}), 400

    discord_user = user_resp.json()
    user_id = discord_user["id"]

    is_new_user = db.users.find_one({"user_id": user_id}) is None

    db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "username": discord_user.get("global_name") or discord_user["username"],
            "username_raw": discord_user["username"],
            "avatar": discord_user.get("avatar"),   # hash brut — l'URL est construite côté front avec discordAvatar()
            "global_name": discord_user.get("global_name"),
            "last_login": datetime.utcnow(),
        }},
        upsert=True
    )
    get_user_doc(user_id)

    token    = make_jwt(user_id, discord_token)
    site_url = os.environ.get("SITE_URL", "https://DragonKnYghT.github.io/vacances-bot")
    # Première connexion → intro, sinon callback normal
    dest = "intro.html" if is_new_user else "callback.html"
    return redirect(f"{site_url}/{dest}?token={token}")

@app.route("/auth/me")
@require_auth
def auth_me():
    resp = requests.get(
        f"{DISCORD_API_BASE}/users/@me",
        headers={"Authorization": f"Bearer {request.discord_token}"},
    )
    if not resp.ok:
        return jsonify({"error": "Token Discord expiré"}), 401
    return jsonify(resp.json())

@app.route("/auth/logout", methods=["POST"])
@require_auth
def auth_logout():
    return jsonify({"ok": True})

# ─────────────────────────────────────────────────────────────────────────────
# Routes Profil & Progression Histoire
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/profile")
@require_auth
def get_profile():
    doc = get_user_doc(request.user_id)
    doc.pop("_id", None)

    vocal = doc.get("vocal_points", 0)
    messages = doc.get("message_points", 0)
    # activity_points et minigame_points supprimés du total affiché (tâche #1)
    doc["total_points"] = vocal + messages

    # Résout l'id stocké (ex: "soldat") vers le nom affichable + bonus,
    # en cherchant dans les pools du Gacha (classe/race obtenues par tirage).
    classe_id = doc.get("classe")
    classe_obj = next((c for c in GACHA_CLASSES if c["id"] == classe_id), None)
    doc["classe"] = classe_obj["name"] if classe_obj else None
    doc["classe_id"] = classe_id
    doc["classe_bonus"] = classe_obj["bonus"] if classe_obj else None
    doc["classe_rarity"] = classe_obj["rarity"] if classe_obj else None

    race_id = doc.get("race")
    race_obj = next((r for r in GACHA_RACES if r["id"] == race_id), None)
    doc["race"] = race_obj["name"] if race_obj else None
    doc["race_id"] = race_id
    doc["race_bonus"] = race_obj["bonus"] if race_obj else None
    doc["race_rarity"] = race_obj["rarity"] if race_obj else None

    if "monde_1" not in doc.get("unlocked_worlds", []):
        doc["unlocked_worlds"] = ["monde_1"] + doc.get("unlocked_worlds", [])

    pipeline = [
        {"$addFields": {"total_cumule": {"$add": [
            {"$ifNull": ["$vocal_points_cumules", {"$ifNull": ["$vocal_points", 0]}]},
            {"$ifNull": ["$message_points_cumules", {"$ifNull": ["$message_points", 0]}]}
        ]}}},
        {"$sort": {"total_cumule": -1}},
        {"$group": {"_id": None, "ids": {"$push": "$user_id"}}},
    ]
    result = list(db.users.aggregate(pipeline))
    if result and request.user_id in result[0]["ids"]:
        doc["rank"] = result[0]["ids"].index(request.user_id) + 1
    else:
        doc["rank"] = None

    return jsonify(doc)

@app.route("/api/story/tutorial/progress", methods=["POST"])
@require_auth
def advance_tutorial():
    """Fait progresser l'état du tutoriel de l'histoire et offre les récompenses."""
    data = request.get_json()
    next_step = data.get("step") # 'ONE_BLOC_INTRO', 'EQUIP_SWORD', 'DONE'
    
    doc = get_user_doc(request.user_id)
    
    if next_step == "DONE" and doc.get("tutorial_progress") != "DONE":
        # Fin de tuto, on offre l'Épée en bois 🪵 demandée dans le lore
        wooden_sword = {
            "id": "wooden_sword_" + str(int(datetime.utcnow().timestamp())),
            "item_id": "wooden_sword",
            "name": "Épée en Bois 🪵",
            "type": "weapon",
            "stat": 10,
            "equipped": False
        }
        db.users.update_one(
            {"user_id": request.user_id},
            {
                "$set": {"tutorial_progress": "DONE"},
                "$push": {"inventory": wooden_sword}
            }
        )
        return jsonify({"ok": True, "step": "DONE", "reward": "wooden_sword"})

    db.users.update_one({"user_id": request.user_id}, {"$set": {"tutorial_progress": next_step}})
    return jsonify({"ok": True, "step": next_step})

# ─────────────────────────────────────────────────────────────────────────────
# Routes One Bloc / Cliqueur (Système de phases et farm)
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/oneblock/state")
@require_auth
def get_one_block_state():
    """Retourne l'état actuel du Cliqueur pour affichage initial."""
    doc = get_user_doc(request.user_id)
    one_block_data = doc.get("one_block", {"phase": 1, "broken": 0, "next": "bois"})
    has_pickaxe = any(
        item for item in doc.get("inventory", [])
        if item.get("item_id") == "wooden_pickaxe" and item.get("equipped") is True
    )
    return jsonify({
        "phase":        one_block_data.get("phase", 1),
        "broken":       one_block_data.get("broken", 0),
        "next_block":   one_block_data.get("next", "bois"),
        "phase_needed": one_block_data.get("phase", 1) * 100,
        "has_pickaxe":  has_pickaxe,
        "tutorial_progress": doc.get("tutorial_progress"),
    })

@app.route("/api/oneblock/mine", methods=["POST"])
@require_auth
def mine_one_block():
    """Gère le clic de cassage de bloc, requiert la pioche en bois équipée au début."""
    doc = get_user_doc(request.user_id)
    
    # Vérification de l'outil équipé (Tuto force à équiper la pioche en bois)
    has_pickaxe = any(item for item in doc.get("inventory", []) if item.get("item_id") == "wooden_pickaxe" and item.get("equipped") is True)
    
    # Bypass de sécurité uniquement si le joueur est en plein tutoriel
    if not has_pickaxe and doc.get("tutorial_progress") == "DONE":
        return jsonify({"error": "Tu dois forger et équiper une Pioche en Bois pour miner le One Bloc !"}), 400

    one_block_data = doc.get("one_block", {"phase": 1, "broken": 0, "next": "bois"})
    
    # Calcul des bonus de clic via l'arbre du joueur
    click_power = 1
    if "clics_efficaces" in doc.get("unlocked_nodes", []):
        click_power += 1

    current_broken = one_block_data.get("broken", 0) + click_power
    current_phase = one_block_data.get("phase", 1)
    
    # Détermination du matériau gagné selon la phase
    materials_pool = ["bois"]
    if current_phase >= 2: materials_pool.append("pierre")
    if current_phase >= 3: materials_pool.append("fer")
    if current_phase >= 4: materials_pool.extend(["cristal", "magie"])
    
    gained_mat = _random.choice(materials_pool)
    
    # Changement de phase tous les 100 blocs cassés
    next_phase = current_phase
    if current_broken >= current_phase * 100:
        next_phase += 1
        current_broken = 0

    # Prochain bloc à afficher visuellement
    next_mat_visual = _random.choice(materials_pool)

    # Mise à jour MongoDB
    db.users.update_one(
        {"user_id": request.user_id},
        {
            "$set": {
                "one_block.broken": current_broken,
                "one_block.phase": next_phase,
                "one_block.next": next_mat_visual
            },
            "$inc": {f"materials.{gained_mat}": 1}
        }
    )

    return jsonify({
        "ok": True,
        "gained": gained_mat,
        "broken": current_broken,
        "phase": next_phase,
        "next_block": next_mat_visual,
        "phase_needed": next_phase * 100
    })

# ─────────────────────────────────────────────────────────────────────────────
# Routes Boutique & Marchand (Achat + Vente de ressources)
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/shop")
@require_auth
def get_shop():
    doc = get_user_doc(request.user_id)
    total_points = (
        doc.get("vocal_points", 0) +
        doc.get("message_points", 0)
    )
    available = max(0, total_points - doc.get("spent_points", 0))
    items = []   # ← fix : manquait dans app_v2
    for key, item in SHOP_ITEMS.items():
        discounted = apply_class_discount(doc, key, item["price"])
        items.append({
            "id": key,
            "name": item["name"],
            "base_price": item["price"],
            "price": discounted,
            "category": item["category"],
            "sell_price": item.get("sell_price", 0), # Ajout pour l'interface de vente du Marchand
            "discounted": discounted < item["price"],
        })
    return jsonify({"items": items, "user_points": available, "materials": doc.get("materials", {})})

@app.route("/api/shop/buy", methods=["POST"])
@require_auth
def buy_item():
    data = request.get_json()
    item_key = data.get("item")
    qty = int(data.get("quantity", 1))

    if item_key not in SHOP_ITEMS:
        return jsonify({"error": "Article inconnu"}), 404

    doc = get_user_doc(request.user_id)
    price = apply_class_discount(doc, item_key, SHOP_ITEMS[item_key]["price"]) * qty
    total_points = (
        doc.get("vocal_points", 0) +
        doc.get("message_points", 0)
    )
    available = max(0, total_points - doc.get("spent_points", 0))

    if available < price:
        return jsonify({"error": "Pas assez de points"}), 400

    mat_field = f"materials.{item_key}"
    update = {"$inc": {"spent_points": price}}

    if item_key not in ("pixel_1", "ticket_classe", "ticket_race", "ticket_duo"):
        update["$inc"][mat_field] = qty

    if item_key == "pixel_1":
        update["$inc"]["pixels_remaining"] = 10 * qty
    elif item_key == "ticket_classe":
        update["$inc"]["tickets_classe"] = qty
    elif item_key == "ticket_race":
        update["$inc"]["tickets_race"] = qty
    elif item_key == "ticket_duo":
        update["$inc"]["tickets_classe"] = qty
        update["$inc"]["tickets_race"] = qty
        update["$inc"]["pixels_remaining"] = 10 * qty

    db.users.update_one({"user_id": request.user_id}, update)
    return jsonify({"ok": True, "spent": price, "remaining_points": available - price})

@app.route("/api/merchant/sell", methods=["POST"])
@require_auth
def sell_item():
    """Le Marchand : Deuxième page de la boutique pour vendre ses ressources contre des Coins."""
    data = request.get_json()
    item_key = data.get("item")
    qty = int(data.get("quantity", 1))

    if item_key not in SHOP_ITEMS or "sell_price" not in SHOP_ITEMS[item_key]:
        return jsonify({"error": "Cet article ne peut pas être vendu."}), 400

    doc = get_user_doc(request.user_id)
    user_mats = doc.get("materials", {})
    
    if user_mats.get(item_key, 0) < qty:
        return jsonify({"error": f"Tu n'as pas assez de {item_key} à vendre."}), 400

    earnings = SHOP_ITEMS[item_key]["sell_price"] * qty

    # Vendre déduit les matériaux et réduit le "spent_points" pour regagner du solde disponible
    db.users.update_one(
        {"user_id": request.user_id},
        {
            "$inc": {
                f"materials.{item_key}": -qty,
                "spent_points": -earnings # Réduire les dépenses revient à donner du budget !
            }
        }
    )
    return jsonify({"ok": True, "earned": earnings})

# ─────────────────────────────────────────────────────────────────────────────
# Routes Inventaire & La Forge (Déblocable monde 2 via l'arbre)
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/inventory")
@require_auth
def get_inventory():
    doc = get_user_doc(request.user_id)
    return jsonify({
        "inventory": doc.get("inventory", []),
        "forge_unlocked": "forge" in doc.get("unlocked_nodes", []),
        "current_world": doc.get("unlocked_worlds", ["monde_1"])[-1]
    })

@app.route("/api/forge/craft", methods=["POST"])
@require_auth
def forge_craft():
    """Permet de fabriquer des outils/armes. Disponible uniquement si validé dans l'arbre au Monde 2."""
    doc = get_user_doc(request.user_id)
    data = request.get_json()
    recipe_key = data.get("recipe")

    if "forge" not in doc.get("unlocked_nodes", []):
        return jsonify({"error": "🔒 Tu dois d'abord débloquer La Forge dans l'Arbre Monde !"}), 403
    
    if "monde_2" not in doc.get("unlocked_worlds", []):
        return jsonify({"error": "🔒 La Forge n'est accessible qu'à partir du Monde 2 (Plaines de Feu)."}), 403

    if recipe_key not in FORGE_RECIPES:
        return jsonify({"error": "Recette introuvable."}), 404

    recipe = FORGE_RECIPES[recipe_key]
    user_mats = doc.get("materials", {})

    # Vérification des ressources
    for mat, qty in recipe["cost"].items():
        if user_mats.get(mat, 0) < qty:
            return jsonify({"error": f"Matériaux insuffisants pour forger cet équipement ({mat} manquant)."}), 400

    # Retrait des ressources et ajout de l'item généré
    inc_costs = {f"materials.{mat}": -qty for mat, qty in recipe["cost"].items()}
    new_item = {
        "id": f"{recipe_key}_{int(datetime.utcnow().timestamp())}",
        "item_id": recipe_key,
        "name": recipe["name"],
        "type": recipe["type"],
        "stat": recipe["stat"],
        "equipped": False
    }

    db.users.update_one(
        {"user_id": request.user_id},
        {
            "$inc": inc_costs,
            "$push": {"inventory": new_item}
        }
    )
    return jsonify({"ok": True, "item": new_item})

@app.route("/api/inventory/equip", methods=["POST"])
@require_auth
def equip_item():
    """Équipe un objet et déséquipe automatiquement l'ancien du même type."""
    data = request.get_json()
    unique_id = data.get("id")
    
    doc = get_user_doc(request.user_id)
    inventory = doc.get("inventory", [])
    
    item_to_equip = next((item for item in inventory if item["id"] == unique_id), None)
    if not item_to_equip:
        return jsonify({"error": "Objet introuvable dans ton inventaire."}), 404

    # Déséquiper tous les objets du même type (ex: autres armes)
    for item in inventory:
        if item["type"] == item_to_equip["type"]:
            item["equipped"] = False
            
    # Équiper le nouvel objet
    item_to_equip["equipped"] = True

    db.users.update_one({"user_id": request.user_id}, {"$set": {"inventory": inventory}})
    return jsonify({"ok": True, "inventory": inventory})

# ─────────────────────────────────────────────────────────────────────────────
# Routes Skill Tree (Avec système d'épreuves Rythme OSU & Test Your Might)
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/skilltree/<world_id>")
@require_auth
def get_skilltree_world(world_id):
    """Route multi-mondes : renvoie base_tree + player_tree pour un monde donné."""
    doc = get_user_doc(request.user_id)
    unlocked       = doc.get("unlocked_nodes", [])
    materials      = doc.get("materials", {})
    completed_trials = doc.get("completed_trials", [])
    unlocked_worlds  = doc.get("unlocked_worlds", ["monde_1"])

    if world_id not in unlocked_worlds:
        return jsonify({"error": "Monde non débloqué"}), 403

    def build_nodes(tree_dict):
        nodes = []
        for key, node in tree_dict.items():
            can_unlock = all(r in unlocked for r in node.get("requires", []))
            affordable = all(materials.get(mat, 0) >= qty for mat, qty in node.get("cost", {}).items())
            trial_done = node.get("trial") is None or key in completed_trials
            nodes.append({
                "id": key,
                "name": node["name"],
                "description": node["description"],
                "cost": node.get("cost", {}),
                "requires": node.get("requires", []),
                "position": node.get("position", {"x": 400, "y": 300}),
                "unlocked": key in unlocked,
                "can_unlock": can_unlock and key not in unlocked,
                "affordable": affordable and can_unlock and key not in unlocked,
                "trial_required": node.get("trial"),
                "trial_passed": trial_done,
            })
        return nodes

    base_nodes   = build_nodes(SKILL_TREE_BASE)
    player_nodes = build_nodes(SKILL_TREE_PLAYER)

    base_done       = sum(1 for n in base_nodes if n["unlocked"])
    world_completed = base_done == len(base_nodes) and len(base_nodes) > 0
    world_list      = list(WORLDS.keys()) if "WORLDS" in dir() else ["monde_1","monde_2","monde_3","monde_4"]
    try:
        world_idx  = world_list.index(world_id)
        next_world = world_list[world_idx + 1] if world_idx + 1 < len(world_list) else None
    except (ValueError, IndexError):
        next_world = None

    return jsonify({
        "world_id": world_id,
        "world_name": world_id.replace("_", " ").title(),
        "nodes": base_nodes + player_nodes,
        "base_tree": base_nodes,
        "player_tree": player_nodes,
        "unlocked": unlocked,
        "materials": materials,
        "world_completed": world_completed,
        "next_world": next_world,
        "next_world_unlocked": next_world in unlocked_worlds if next_world else False,
    })


@app.route("/api/skilltree/<world_id>/unlock", methods=["POST"])
@require_auth
def unlock_node_world(world_id):
    """Déblocage d'un nœud pour un monde donné (tree = 'base' | 'player')."""
    data     = request.get_json()
    node_key = data.get("node")
    tree     = data.get("tree", "base")

    tree_dict = SKILL_TREE_BASE if tree == "base" else SKILL_TREE_PLAYER
    if node_key not in tree_dict and node_key not in SKILL_TREE:
        return jsonify({"error": "Nœud inconnu"}), 404

    node = tree_dict.get(node_key) or SKILL_TREE.get(node_key)
    doc  = get_user_doc(request.user_id)
    unlocked         = doc.get("unlocked_nodes", [])
    materials        = doc.get("materials", {})
    completed_trials = doc.get("completed_trials", [])

    if node_key in unlocked:
        return jsonify({"error": "Déjà débloqué"}), 400
    if not all(r in unlocked for r in node.get("requires", [])):
        return jsonify({"error": "Prérequis manquants"}), 400
    if node.get("trial") and node_key not in completed_trials:
        return jsonify({"error": "Tu dois réussir l'épreuve de ce nœud avant !"}), 400
    for mat, qty in node.get("cost", {}).items():
        if materials.get(mat, 0) < qty:
            return jsonify({"error": f"Pas assez de {mat}"}), 400

    inc    = {f"materials.{mat}": -qty for mat, qty in node.get("cost", {}).items()}
    update = {"$inc": inc, "$push": {"unlocked_nodes": node_key}}

    new_world = node.get("unlocks")
    if new_world:
        update["$addToSet"] = {"unlocked_worlds": new_world}

    db.users.update_one({"user_id": request.user_id}, update)
    return jsonify({"ok": True, "unlocked": node_key, "new_world": new_world})


@app.route("/api/skilltree")
@require_auth
def get_skilltree():
    doc = get_user_doc(request.user_id)
    unlocked = doc.get("unlocked_nodes", [])
    materials = doc.get("materials", {})
    completed_trials = doc.get("completed_trials", [])

    # Arbre Monde (Base)
    base_nodes = []
    for key, node in SKILL_TREE_BASE.items():
        can_unlock = all(r in unlocked for r in node["requires"])
        affordable = all(materials.get(mat, 0) >= qty for mat, qty in node["cost"].items())
        trial_done = node["trial"] is None or key in completed_trials
        
        base_nodes.append({
            "id": key,
            "name": node["name"],
            "description": node["description"],
            "cost": node["cost"],
            "requires": node["requires"],
            "position": node["position"],
            "unlocked": key in unlocked,
            "can_unlock": can_unlock and key not in unlocked,
            "affordable": affordable and can_unlock and key not in unlocked,
            "trial_required": node["trial"],
            "trial_passed": trial_done,
            "unlocks": node.get("unlocks"),
        })

    # Arbre du Joueur
    player_nodes = []
    for key, node in SKILL_TREE_PLAYER.items():
        can_unlock = all(r in unlocked for r in node["requires"])
        affordable = all(materials.get(mat, 0) >= qty for mat, qty in node["cost"].items())
        trial_done = node["trial"] is None or key in completed_trials

        player_nodes.append({
            "id": key,
            "name": node["name"],
            "description": node["description"],
            "cost": node["cost"],
            "requires": node["requires"],
            "position": node["position"],
            "unlocked": key in unlocked,
            "can_unlock": can_unlock and key not in unlocked,
            "affordable": affordable and can_unlock and key not in unlocked,
            "trial_required": node["trial"],
            "trial_passed": trial_done,
        })

    return jsonify({
        "nodes": base_nodes + player_nodes,   # ← fusion pour compat avec skilltree.html
        "base_tree": base_nodes,
        "player_tree": player_nodes,
        "unlocked": unlocked,
        "materials": materials
    })

@app.route("/api/skilltree/trial/complete", methods=["POST"])
@require_auth
def complete_node_trial():
    """Appelé par le front-end quand le joueur réussit le mini-jeu (OSU ou Test Your Might)."""
    data = request.get_json()
    node_key = data.get("node")
    success = data.get("success", False)

    if not success:
        return jsonify({"error": "Épreuve échouée, réessaye ! 💥"}), 400

    db.users.update_one(
        {"user_id": request.user_id},
        {"$addToSet": {"completed_trials": node_key}}
    )
    return jsonify({"ok": True, "message": "Épreuve validée avec succès ! 🎉"})

@app.route("/api/skilltree/unlock", methods=["POST"])
@require_auth
def unlock_node():
    data = request.get_json()
    node_key = data.get("node")

    if node_key not in SKILL_TREE:
        return jsonify({"error": "Nœud inconnu"}), 404

    node = SKILL_TREE[node_key]
    doc = get_user_doc(request.user_id)
    unlocked = doc.get("unlocked_nodes", [])
    materials = doc.get("materials", {})
    completed_trials = doc.get("completed_trials", [])

    if node_key in unlocked:
        return jsonify({"error": "Déjà débloqué"}), 400
    if not all(r in unlocked for r in node["requires"]):
        return jsonify({"error": "Prérequis manquants"}), 400
    if node.get("trial") and node_key not in completed_trials:
        return jsonify({"error": "Tu dois réussir l'épreuve de ce nœud avant !"}), 400
    for mat, qty in node["cost"].items():
        if materials.get(mat, 0) < qty:
            return jsonify({"error": f"Pas assez de {mat}"}), 400

    inc = {f"materials.{mat}": -qty for mat, qty in node["cost"].items()}
    inc_update = {"$inc": inc, "$push": {"unlocked_nodes": node_key}}

    if "unlocks" in node:
        inc_update["$addToSet"] = {"unlocked_worlds": node["unlocks"]}

    db.users.update_one({"user_id": request.user_id}, inc_update)
    return jsonify({"ok": True, "unlocked": node_key, "new_world": node.get("unlocks")})

# ─────────────────────────────────────────────────────────────────────────────
# Routes Pixel Map & Invitation de Pixels aux autres joueurs
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/pixelmap/<world_id>")
@require_auth
def get_pixelmap(world_id):
    if world_id not in WORLDS:
        return jsonify({"error": "Monde inconnu"}), 404

    doc = get_user_doc(request.user_id)
    if world_id not in doc.get("unlocked_worlds", ["monde_1"]):
        return jsonify({"error": "Monde verrouillé"}), 403

    pixels = list(db.pixels.find(
        {"world": world_id},
        {"_id": 0, "x": 1, "y": 1, "color": 1, "placed_by": 1, "placed_at": 1}
    ))

    return jsonify({
        "world": WORLDS[world_id],
        "pixels": pixels,
        "grid_size": WORLDS[world_id]["grid_size"],
        "user_pixels_remaining": doc.get("pixels_remaining", 0),
    })

@app.route("/api/pixelmap/<world_id>/place", methods=["POST"])
@require_auth
def place_pixel(world_id):
    if world_id not in WORLDS:
        return jsonify({"error": "Monde inconnu"}), 404

    doc = get_user_doc(request.user_id)
    if world_id not in doc.get("unlocked_worlds", ["monde_1"]):
        return jsonify({"error": "Monde verrouillé"}), 403

    pixels_left = doc.get("pixels_remaining", 0)
    if pixels_left <= 0:
        return jsonify({"error": "Plus de pixels disponibles"}), 400

    data = request.get_json()
    x, y, color = int(data["x"]), int(data["y"]), str(data["color"])
    size = WORLDS[world_id]["grid_size"]

    if not (0 <= x < size and 0 <= y < size):
        return jsonify({"error": "Coordonnées hors grille"}), 400
    if not color.startswith("#") or len(color) not in (4, 7):
        return jsonify({"error": "Couleur invalide"}), 400

    db.pixels.update_one(
        {"world": world_id, "x": x, "y": y},
        {"$set": {
            "color": color,
            "placed_by": request.user_id,
            "placed_at": datetime.utcnow(),
        }},
        upsert=True
    )
    db.users.update_one({"user_id": request.user_id}, {"$inc": {"pixels_remaining": -1}})

    return jsonify({"ok": True, "pixels_remaining": pixels_left - 1})

@app.route("/api/pixel/invite", methods=["POST"])
@require_auth
@require_auth
def invite_to_pixel_zone():
    """Système d'invitation au pixel : envoie une notification à un autre joueur."""
    doc = get_user_doc(request.user_id)
    data = request.get_json()
    target_username = data.get("target_username")
    world_id = data.get("world_id")
    x = data.get("x")
    y = data.get("y")

    target_user = db.users.find_one({"username": target_username})
    if not target_user:
        return jsonify({"error": "Joueur introuvable sur le serveur."}), 404

    invitation = {
        "from": doc.get("username", "Un Gardien"),
        "from_id": request.user_id,
        "world_id": world_id,
        "coords": f"[{x}, {y}]",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    db.users.update_one(
        {"user_id": target_user["user_id"]},
        {"$push": {"pixel_invitations": invitation}}
    )
    return jsonify({"ok": True, "message": f"Invitation envoyée à {target_username} !"})


@app.route("/api/pixel/invitations")
@require_auth
def get_pixel_invitations():
    """Récupère les invitations pixel en attente pour l'utilisateur connecté."""
    doc = get_user_doc(request.user_id)
    invitations = doc.get("pixel_invitations", [])[-10:]  # 10 dernières
    return jsonify({"invitations": invitations})


@app.route("/api/admin/cleanup-anonymous", methods=["POST"])
@require_auth
def cleanup_anonymous():
    """#3 Supprime les profils anonymes de test de la BDD."""
    result = db.users.delete_many({
        "$or": [
            {"username": "Joueur Anonyme"},
            {"username": {"$regex": "^Anonyme"}},
            {"user_id": {"$not": {"$regex": "^[0-9]+$"}}}
        ]
    })
    return jsonify({"ok": True, "deleted": result.deleted_count})

# ─────────────────────────────────────────────────────────────────────────────
# Routes Classes & Choix Originel
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/classes")
def get_classes():
    return jsonify({"classes": CLASSES})

@app.route("/api/classes/choose", methods=["POST"])
@require_auth
def choose_class():
    data = request.get_json()
    classe = data.get("classe")

    if classe not in CLASSES:
        return jsonify({"error": "Classe inconnue"}), 404

    doc = get_user_doc(request.user_id)
    if doc.get("classe") and doc.get("classe") != "Aucune":
        return jsonify({"error": "Tu as déjà choisi une classe"}), 400

    db.users.update_one(
        {"user_id": request.user_id},
        {"$set": {"classe": classe}}
    )
    return jsonify({"ok": True, "classe": classe})

# ─────────────────────────────────────────────────────────────────────────────
# Routes Combat de Boss (Les Gardiens corrompus de l'Arbre)
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/boss/status")
@require_auth
def get_boss_status():
    doc = get_user_doc(request.user_id)
    current_world = doc.get("unlocked_worlds", ["monde_1"])[-1]
    
    if current_world not in BOSSES:
        return jsonify({"error": "Aucun boss dans cette zone"}), 400
        
    boss_info = BOSSES[current_world]
    progress = doc.get("boss_progress", {})
    current_hp = progress.get(boss_info["id"], boss_info["max_hp"])
    
    return jsonify({
        "boss": boss_info,
        "current_hp": current_hp,
        "is_dead": current_hp <= 0
    })

@app.route("/api/boss/attack", methods=["POST"])
@require_auth
def attack_boss():
    """Attaque le boss du monde actuel en utilisant la puissance de l'arme équipée."""
    doc = get_user_doc(request.user_id)
    current_world = doc.get("unlocked_worlds", ["monde_1"])[-1]
    
    if current_world not in BOSSES:
        return jsonify({"error": "Pas de boss ici"}), 400
        
    boss_info = BOSSES[current_world]
    boss_id = boss_info["id"]
    current_hp = doc.get("boss_progress", {}).get(boss_id, boss_info["max_hp"])
    
    if current_hp <= 0:
        return jsonify({"error": "Ce Gardien est déjà purifié/vaincu pour ce monde !"}), 400

    # Recherche des dégâts de l'arme équipée
    equipped_weapon = next((item for item in doc.get("inventory", []) if item.get("type") == "weapon" and item.get("equipped") is True), None)
    base_damage = equipped_weapon["stat"] if equipped_weapon else 2 # Mains nues = 2 dégâts
    
    # Bonus de l'arbre joueur
    if "fureur_du_gardien" in doc.get("unlocked_nodes", []):
        base_damage = int(base_damage * 1.15)

    new_hp = max(0, current_hp - base_damage)
    
    update_query = {"$set": {f"boss_progress.{boss_id}": new_hp}}
    
    # Si le boss meurt, on distribue sa récompense de points d'activité
    if new_hp == 0:
        update_query["$inc"] = {"activity_points": boss_info["reward_points"]}

    db.users.update_one({"user_id": request.user_id}, update_query)
    
    return jsonify({
        "ok": True,
        "damage_dealt": base_damage,
        "new_hp": new_hp,
        "boss_defeated": new_hp == 0,
        "reward": boss_info["reward_points"] if new_hp == 0 else 0
    })

# ─────────────────────────────────────────────────────────────────────────────
# Routes Gacha & Système de Pitié (10 étapes — 200 tirages max)
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/gacha/pity/status")
@require_auth
def get_pity_status():
    doc = get_user_doc(request.user_id)
    return jsonify({"pity": doc.get("gacha_pity")})

@app.route("/api/gacha/pull", methods=["POST"])
@require_auth
def pull_gacha():
    """Gère un tirage avec l'augmentation par étape de 5% de pitié tous les 20 tirages."""
    data = request.get_json()
    pull_type = data.get("type") # "classe" ou "race"
    
    doc = get_user_doc(request.user_id)
    ticket_field = f"tickets_{pull_type}"
    
    if doc.get(ticket_field, 0) < 1:
        return jsonify({"error": f"Tu n'as pas de Ticket {pull_type.capitalize()} ! Accède au Shop."}), 400

    pity_data = doc.get("gacha_pity", {"total_pulls": 0, "current_step": 0, "bonus_chance": 0.0})
    total_pulls = pity_data.get("total_pulls", 0) + 1
    
    # SOFT PITY : dès 10 tirages sans légendaire, +5% tous les 10 tirages (max +50% à 110 tirages)
    current_step = total_pulls // 10
    if current_step > 10: current_step = 10
    bonus_chance = current_step * 5.0

    # HARD PITY : à 200 tirages, légendaire garanti (100%)
    hard_pity_triggered = total_pulls >= 200

    roll = _random.uniform(0, 100)
    legendary_threshold = 3.0 + bonus_chance
    
    pool = GACHA_CLASSES if pull_type == "classe" else GACHA_RACES
    
    if hard_pity_triggered or roll <= legendary_threshold:
        gained_rarity = "legendaire"
        # Reset pitié après légendaire
        total_pulls = 0
        current_step = 0
        bonus_chance = 0.0
    elif roll <= legendary_threshold + 12:
        gained_rarity = "epique"
    elif roll <= legendary_threshold + 12 + 30:
        gained_rarity = "rare"
    else:
        gained_rarity = "commun"

    # Filtrer les entités de cette rareté
    available_rewards = [item for item in pool if item["rarity"] == gained_rarity]
    reward = _random.choice(available_rewards)

    # Sauvegarde du choix en base (on stocke l'id court, pas le nom affiché,
    # pour rester cohérent avec RACES_INFO / GACHA_CLASSES côté frontend)
    update_set = {
        pull_type: reward["id"],
        "gacha_pity.total_pulls": total_pulls,
        "gacha_pity.current_step": current_step,
        "gacha_pity.bonus_chance": bonus_chance
    }
    
    db.users.update_one(
        {"user_id": request.user_id},
        {
            "$set": update_set,
            "$inc": {ticket_field: -1},
            "$push": {f"{pull_type}_history": reward["id"]}
        }
    )

    return jsonify({
        "ok": True,
        "reward": reward,
        "pity": {
            "total_pulls": total_pulls,
            "current_step": current_step,
            "bonus_chance": bonus_chance,
            "hard_pity_triggered": hard_pity_triggered if 'hard_pity_triggered' in dir() else False
        }
    })

# ─────────────────────────────────────────────────────────────────────────────
# Routes Classement
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    users = list(db.users.find({
        "user_id": {"$regex": "^[0-9]+$"},
        "username": {"$ne": "Joueur Anonyme"}
    }))
    
    leaderboard = []
    for u in users:
        vocal_cumule = u.get("vocal_points_cumules", u.get("vocal_points", 0))
        messages_cumule = u.get("message_points_cumules", u.get("message_points", 0))
        total_historique = vocal_cumule + messages_cumule
        
        leaderboard.append({
            "user_id": str(u.get("user_id", "")),
            "username": u.get("username", "Joueur"),
            "avatar": u.get("avatar") or None,
            "classe": u.get("classe", "Aucune"),
            "race": u.get("race", "Aucune"),
            "total_points": total_historique,
            "details": {
                "vocal": u.get("vocal_points", 0),
                "messages": u.get("message_points", 0)
            }
        })
        
    leaderboard.sort(key=lambda x: x["total_points"], reverse=True)
    return jsonify(leaderboard[:10])

# ─────────────────────────────────────────────────────────────────────────────
# Routes Codes Promo
# ─────────────────────────────────────────────────────────────────────────────

REWARD_LABELS = {
    "message_points":   "points messages",
    "vocal_points":     "points vocal",
    "pixels_remaining": "pixels",
    "pierre":  "🪨 Pierre",
    "bois":    "🪵 Bois",
    "fer":     "⚙️ Fer",
    "cristal": "💎 Cristal",
    "magie":   "✨ Essence magique",
}

@app.route("/api/codes/redeem", methods=["POST"])
@require_auth
def redeem_code():
    data     = request.get_json()
    raw_code = data.get("code", "").strip().upper()

    if not raw_code:
        return jsonify({"error": "Code vide"}), 400

    code_doc = db.codes.find_one({"code": raw_code})

    if not code_doc:
        return jsonify({"error": "Code invalide ❌"}), 404
    if not code_doc.get("active", True):
        return jsonify({"error": "Ce code est désactivé"}), 400

    uid = request.user_id

    if uid in code_doc.get("used_by", []):
        return jsonify({"error": "Tu as déjà utilisé ce code 😅"}), 400

    total_max = code_doc.get("total_max")
    if total_max is not None and code_doc.get("total_used", 0) >= total_max:
        return jsonify({"error": "Ce code a atteint sa limite d'utilisations 😢"}), 400

    rewards = code_doc.get("rewards", {})
    if not rewards:
        return jsonify({"error": "Code sans récompenses"}), 400

    inc_fields = {}
    for field, amount in rewards.items():
        if field in ("pierre", "bois", "fer", "cristal", "magie"):
            inc_fields[f"materials.{field}"] = amount
        else:
            inc_fields[field] = amount

    db.users.update_one({"user_id": uid}, {"$inc": inc_fields}, upsert=True)
    db.codes.update_one(
        {"code": raw_code},
        {"$push": {"used_by": uid}, "$inc": {"total_used": 1}}
    )

    rewards_display = []
    for field, amount in rewards.items():
        label = REWARD_LABELS.get(field, field)
        rewards_display.append(f"+{amount} {label}")

    return jsonify({"ok": True, "rewards": rewards_display})

@app.route("/api/codes/check", methods=["POST"])
@require_auth
def check_code():
    data     = request.get_json()
    raw_code = data.get("code", "").strip().upper()
    if not raw_code:
        return jsonify({"valid": False}), 200

    code_doc = db.codes.find_one({"code": raw_code})
    if not code_doc or not code_doc.get("active", True):
        return jsonify({"valid": False, "reason": "Invalide"}), 200

    uid          = request.user_id
    already_used = uid in code_doc.get("used_by", [])
    total_max    = code_doc.get("total_max")
    exhausted    = total_max is not None and code_doc.get("total_used", 0) >= total_max

    rewards = code_doc.get("rewards", {})
    rewards_display = [
        f"+{amt} {REWARD_LABELS.get(f, f)}" for f, amt in rewards.items()
    ]

    return jsonify({
        "valid":        not already_used and not exhausted,
        "already_used": already_used,
        "exhausted":    exhausted,
        "rewards":      rewards_display,
    })



# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Easter Eggs (#13)
# ─────────────────────────────────────────────────────────────────────────────

EGG_REWARDS = {
    "konami":      {"bois": 5},
    "logo10":      {"pierre": 3},
    "idle30":      {"fer": 2},
    "vacances":    {"magie": 5},
    "tripleimg":   {"pierre": 4},
    "devtools":    {"cristal": 3},
    "selectname":  {"magie": 2},
    "scrollbottom":{"bois": 3},
}

@app.route("/api/easter-egg/claim", methods=["POST"])
@require_auth
def claim_easter_egg():
    data   = request.get_json()
    egg_id = data.get("egg_id")
    if egg_id not in EGG_REWARDS:
        return jsonify({"error": "Easter egg inconnu"}), 404

    doc = get_user_doc(request.user_id)
    already_found = doc.get("found_eggs", [])
    if egg_id in already_found:
        return jsonify({"ok": True, "already_found": True})

    reward = EGG_REWARDS[egg_id]
    inc = {f"materials.{mat}": qty for mat, qty in reward.items()}
    db.users.update_one(
        {"user_id": request.user_id},
        {"$inc": inc, "$push": {"found_eggs": egg_id}}
    )
    return jsonify({"ok": True, "reward": reward})


# ─────────────────────────────────────────────────────────────────────────────
# Marchand — Vente de matériaux (#5)
# ─────────────────────────────────────────────────────────────────────────────

SELL_PRICES = {"bois": 4, "pierre": 5, "fer": 12, "cristal": 30, "magie": 50}

@app.route("/api/merchant/sell", methods=["POST"])
@require_auth
def merchant_sell():
    data = request.get_json()
    item = data.get("item")
    qty  = int(data.get("quantity", 1))

    if item not in SELL_PRICES:
        return jsonify({"error": "Matériau non vendable"}), 400
    if qty < 1:
        return jsonify({"error": "Quantité invalide"}), 400

    doc = get_user_doc(request.user_id)
    stock = doc.get("materials", {}).get(item, 0)
    if stock < qty:
        return jsonify({"error": f"Tu n'as que {stock}× {item}"}), 400

    earned = SELL_PRICES[item] * qty
    db.users.update_one(
        {"user_id": request.user_id},
        {
            "$inc": {
                f"materials.{item}": -qty,
                "vocal_points": earned   # on ajoute aux points vocal (comptent pour le total)
            }
        }
    )
    total = (doc.get("vocal_points", 0) + earned +
             doc.get("message_points", 0) -
             doc.get("spent_points", 0))
    return jsonify({"ok": True, "earned": earned, "remaining_points": max(0, total)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

# ─────────────────────────────────────────────────────────────────────────────
# GACHA INFO — Résumé tickets + classe/race actuelle (utilisé par gacha.html)
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/gacha/info")
@require_auth
def gacha_info():
    doc = get_user_doc(request.user_id)
    return jsonify({
        "tickets_classe": doc.get("tickets_classe", 0),
        "tickets_race":   doc.get("tickets_race", 0),
        "current_classe": doc.get("classe"),
        "current_race":   doc.get("race"),
        "rarities":       RARITIES,
    })

# ─────────────────────────────────────────────────────────────────────────────
# QUÊTES QUOTIDIENNES
# ─────────────────────────────────────────────────────────────────────────────

import hashlib as _hashlib

QUEST_TYPES = [
    {"id":"messages", "label":"Envoie {n} messages",          "icon":"💬", "targets":[5,10,20],  "rewards":{"tickets_classe":1}},
    {"id":"vocal",    "label":"Passe {n} minutes en vocal",    "icon":"🎙️","targets":[5,15,30],  "rewards":{"tickets_race":1}},
    {"id":"pixels",   "label":"Pose {n} pixels sur la map",    "icon":"🎨","targets":[5,10,25],  "rewards":{"tickets_classe":1,"tickets_race":1}},
    {"id":"messages2","label":"Envoie {n} messages",           "icon":"💬","targets":[15,30,50], "rewards":{"tickets_classe":2}},
    {"id":"boutique", "label":"Achète {n} articles en boutique","icon":"🛒","targets":[1,3,5],   "rewards":{"tickets_race":2}},
]

def get_daily_quest(user_id: str) -> dict:
    """Génère une quête déterministe par joueur et par jour (1 seule quête/jour)."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    seed  = int(_hashlib.md5(f"{user_id}{today}".encode()).hexdigest(), 16)
    rng   = _random.Random(seed)

    quest_type = QUEST_TYPES[seed % len(QUEST_TYPES)]
    target     = rng.choice(quest_type["targets"])
    return {
        "id":      quest_type["id"],
        "label":   quest_type["label"].replace("{n}", str(target)),
        "icon":    quest_type["icon"],
        "target":  target,
        "rewards": quest_type["rewards"],
        "date":    today,
    }

def _quest_progress(doc: dict, quest: dict, today: str) -> int:
    qid = quest["id"]
    if doc.get("daily_date") != today and qid != "boutique":
        if qid not in ("boutique",):
            return 0
    if qid in ("messages", "messages2"):
        return doc.get("daily_messages", 0) if doc.get("daily_date") == today else 0
    elif qid == "vocal":
        return doc.get("daily_vocal_minutes", 0) if doc.get("daily_date") == today else 0
    elif qid == "pixels":
        return doc.get("daily_pixels", 0) if doc.get("daily_date") == today else 0
    elif qid == "boutique":
        return doc.get("daily_purchases", 0) if doc.get("daily_date") == today else 0
    return 0

@app.route("/api/quests/daily")
@require_auth
def get_daily_quest_route():
    quest = get_daily_quest(request.user_id)
    doc   = get_user_doc(request.user_id)
    today = datetime.utcnow().strftime("%Y-%m-%d")

    progress  = _quest_progress(doc, quest, today)
    completed = doc.get("quest_completed_date") == today

    return jsonify({
        **quest,
        "progress":       min(progress, quest["target"]),
        "completed":      completed,
        "tickets_classe": doc.get("tickets_classe", 0),
        "tickets_race":   doc.get("tickets_race", 0),
    })

@app.route("/api/quests/claim", methods=["POST"])
@require_auth
def claim_quest():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    doc   = get_user_doc(request.user_id)

    if doc.get("quest_completed_date") == today:
        return jsonify({"error": "Quête déjà réclamée aujourd'hui"}), 400

    quest    = get_daily_quest(request.user_id)
    progress = _quest_progress(doc, quest, today)

    if progress < quest["target"]:
        return jsonify({"error": f"Pas encore terminé ({progress}/{quest['target']})"}), 400

    rewards = quest["rewards"]
    db.users.update_one(
        {"user_id": request.user_id},
        {"$inc": rewards, "$set": {"quest_completed_date": today}}
    )
    rewards_display = []
    for field, amt in rewards.items():
        label = {"tickets_classe": "🎫 Ticket Classe", "tickets_race": "🎟️ Ticket Race"}.get(field, field)
        rewards_display.append(f"+{amt} {label}")

    return jsonify({"ok": True, "rewards": rewards_display})
