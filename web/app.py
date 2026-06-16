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

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
CORS(app,
    origins=[
        "https://DragonKnYghT.github.io",
        "http://localhost:3000",
        "http://127.0.0.1:5500",
    ],
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)

# ── MongoDB ──────────────────────────────────────────────────────────────────
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["vacances_bot"]             # ← même DB que le bot

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

# ── Mondes / maps pixel ──────────────────────────────────────────────────────
WORLDS = {
    "monde_1": {"name": "La Forêt des Débuts", "required_nodes": [], "grid_size": 100},
    "monde_2": {"name": "Les Plaines de Feu",  "required_nodes": ["foret_complete"], "grid_size": 100},
    "monde_3": {"name": "L'Océan Profond",     "required_nodes": ["plaines_complete"], "grid_size": 100},
    "monde_4": {"name": "Le Sommet des Dieux", "required_nodes": ["ocean_complete"], "grid_size": 100},
}

# ── Boutique ─────────────────────────────────────────────────────────────────
SHOP_ITEMS = {
    "pierre":  {"name": "Pierre 🪨",    "price": 10,  "category": "materiau"},
    "bois":    {"name": "Bois 🪵",      "price": 8,   "category": "materiau"},
    "fer":     {"name": "Fer ⚙️",       "price": 25,  "category": "materiau"},
    "cristal": {"name": "Cristal 💎",   "price": 60,  "category": "materiau"},
    "magie":   {"name": "Essence magique ✨", "price": 100, "category": "special"},
    "pixel_1": {"name": "Pack Pixels ×10 🎨", "price": 50, "category": "pixel"},
    "ticket_classe": {"name": "Ticket Classe 🎫", "price": 80, "category": "gacha"},
    "ticket_race":   {"name": "Ticket Race 🎟️",  "price": 80, "category": "gacha"},
    "ticket_duo":    {"name": "Duo Classe+Race 🎰","price": 140,"category": "gacha"},
}

# ── Skill tree ────────────────────────────────────────────────────────────────
SKILL_TREE = {
    "salle_reunion": {
        "name": "Salle de réunion",
        "description": "Permet de lancer des votes serveur",
        "cost": {"pierre": 5, "bois": 3},
        "requires": [],
        "position": {"x": 400, "y": 50},
        "unlocks": "monde_vote"
    },
    "forge": {
        "name": "La Forge",
        "description": "Réduit le coût des matériaux de 10%",
        "cost": {"pierre": 10, "fer": 5},
        "requires": ["salle_reunion"],
        "position": {"x": 200, "y": 200},
    },
    "bibliotheque": {
        "name": "Bibliothèque",
        "description": "Bonus de +2pts sur les quiz",
        "cost": {"bois": 15, "cristal": 2},
        "requires": ["salle_reunion"],
        "position": {"x": 600, "y": 200},
    },
    "foret_complete": {
        "name": "Maîtrise de la Forêt",
        "description": "Débloque le Monde 2 - Plaines de Feu",
        "cost": {"pierre": 20, "bois": 20, "fer": 10},
        "requires": ["forge", "bibliotheque"],
        "position": {"x": 400, "y": 350},
        "unlocks": "monde_2"
    },
    "plaines_complete": {
        "name": "Maîtrise des Plaines",
        "description": "Débloque le Monde 3 - Océan Profond",
        "cost": {"fer": 30, "cristal": 10, "magie": 2},
        "requires": ["foret_complete"],
        "position": {"x": 400, "y": 500},
        "unlocks": "monde_3"
    },
    "ocean_complete": {
        "name": "Maîtrise de l'Océan",
        "description": "Débloque le Monde 4 - Sommet des Dieux",
        "cost": {"cristal": 30, "magie": 10},
        "requires": ["plaines_complete"],
        "position": {"x": 400, "y": 650},
        "unlocks": "monde_4"
    },
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
    """Récupère ou crée le document utilisateur dans MongoDB avec sécurité Gacha."""
    doc = db.users.find_one({"user_id": user_id})
    if not doc:
        doc = {
            "user_id": user_id,
            "points": 0,
            "vocal_points": 0,
            "message_points": 0,
            "activity_points": 0,
            "minigame_points": 0,
            "classe": None,
            "race": None,
            "tickets_classe": 0,
            "tickets_race": 0,
            "classe_history": [],
            "race_history": [],
            "materials": {},
            "pixels_remaining": 0,
            "unlocked_worlds": ["monde_1"],
            "unlocked_nodes": [],
            "created_at": datetime.utcnow()
        }
        db.users.insert_one(doc)
    else:
        # Sécurité pour les anciens comptes : on s'assure que les listes et tickets existent
        modified = False
        updates = {}
        if "tickets_classe" not in doc:
            doc["tickets_classe"] = 0
            updates["tickets_classe"] = 0
        if "tickets_race" not in doc:
            doc["tickets_race"] = 0
            updates["tickets_race"] = 0
        if "race" not in doc:
            doc["race"] = None
            updates["race"] = None
        
        if updates:
            db.users.update_one({"user_id": user_id}, {"$set": updates})
            
    return doc

def apply_class_discount(user_doc: dict, item_key: str, base_price: int) -> int:
    user_classe = user_doc.get("classe")
    if not user_classe:
        return base_price

    # On cherche la classe de l'utilisateur dans la liste du Gacha pour obtenir ses vrais bonus
    classe_meta = next((c for c in GACHA_CLASSES if c["id"] == user_classe), None)
    
    # Si pas trouvé dans le Gacha, on cherche dans l'ancien dictionnaire de secours
    if not classe_meta:
        classe_meta = CLASSES.get(user_classe)

    if not classe_meta:
        return base_price

    item = SHOP_ITEMS.get(item_key, {})
    
    # Gestion du coût des pixels
    if item.get("category") == "pixel":
        pixel_cost_multiplier = classe_meta.get("pixel_cost", 1.0)
        return int(base_price * pixel_cost_multiplier)

    # Gestion des réductions de la boutique
    discount = classe_meta.get("shop_discount", 0.0)
    return int(base_price * (1 - discount))

# ─────────────────────────────────────────────────────────────────────────────
# Routes OAuth2
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/auth/login")
def auth_login():
    """Redirige vers Discord pour l'autorisation."""
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
    """Discord redirige ici avec un code. On l'échange contre un token."""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Code manquant"}), 400

    # Échange du code contre un access token Discord
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

    # Récupère l'utilisateur Discord
    user_resp = requests.get(
        f"{DISCORD_API_BASE}/users/@me",
        headers={"Authorization": f"Bearer {discord_token}"},
    )
    if not user_resp.ok:
        return jsonify({"error": "Impossible de récupérer l'utilisateur"}), 400

    discord_user = user_resp.json()
    user_id = discord_user["id"]

    # Crée/met à jour en base
    db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "username": discord_user["username"],
            "avatar": discord_user.get("avatar"),
            "global_name": discord_user.get("global_name"),
            "last_login": datetime.utcnow(),
        }},
        upsert=True
    )
    get_user_doc(user_id)  # s'assure que tous les champs existent

    # Génère un JWT et redirige vers le site
    token = make_jwt(user_id, discord_token)
    site_url = os.environ.get("SITE_URL", "https://TON_USERNAME.github.io/vacances-bot")
    return redirect(f"{site_url}/callback.html?token={token}")

@app.route("/auth/me")
@require_auth
def auth_me():
    """Renvoie les infos Discord de l'utilisateur connecté."""
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
# Routes Profil
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/profile")
@require_auth
def get_profile():
    doc = get_user_doc(request.user_id)
    doc.pop("_id", None)

    # Calcul du total de points
    doc["total_points"] = (
        doc.get("vocal_points", 0) +
        doc.get("message_points", 0) +
        doc.get("activity_points", 0) +
        doc.get("minigame_points", 0)
    )
    # Classement global
    pipeline = [
        {"$addFields": {"total": {"$add": [
            {"$ifNull": ["$vocal_points", 0]},
            {"$ifNull": ["$message_points", 0]},
            {"$ifNull": ["$activity_points", 0]},
            {"$ifNull": ["$minigame_points", 0]},
        ]}}},
        {"$sort": {"total": -1}},
        {"$group": {"_id": None, "ids": {"$push": "$user_id"}}},
    ]
    result = list(db.users.aggregate(pipeline))
    if result and request.user_id in result[0]["ids"]:
        doc["rank"] = result[0]["ids"].index(request.user_id) + 1
    else:
        doc["rank"] = None

    return jsonify(doc)

# ─────────────────────────────────────────────────────────────────────────────
# Routes Boutique
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/shop")
@require_auth
def get_shop():
    doc = get_user_doc(request.user_id)
    total_points = (
        doc.get("vocal_points", 0) +
        doc.get("message_points", 0) +
        doc.get("minigame_points", 0) +
        doc.get("activity_points", 0)
    )
    available = max(0, total_points - doc.get("spent_points", 0))
    items = []
    for key, item in SHOP_ITEMS.items():
        discounted = apply_class_discount(doc, key, item["price"])
        items.append({
            "id": key,
            "name": item["name"],
            "base_price": item["price"],
            "price": discounted,
            "category": item["category"],
            "discounted": discounted < item["price"],
        })
    return jsonify({"items": items, "user_points": available})

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
        doc.get("message_points", 0) +
        doc.get("minigame_points", 0) +
        doc.get("activity_points", 0)
    )
    available = max(0, total_points - doc.get("spent_points", 0))

    if available < price:
        return jsonify({"error": "Pas assez de points"}), 400

    mat_field = f"materials.{item_key}"
    
    # Préparation propre des dictionnaires MongoDB pour éviter les KeyError en Python
    update = {
        "$inc": {"spent_points": price}
    }

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
# ─────────────────────────────────────────────────────────────────────────────
# Routes Skill Tree
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/skilltree")
@require_auth
def get_skilltree():
    doc = get_user_doc(request.user_id)
    unlocked = doc.get("unlocked_nodes", [])
    materials = doc.get("materials", {})

    nodes = []
    for key, node in SKILL_TREE.items():
        can_unlock = all(r in unlocked for r in node["requires"])
        affordable = all(
            materials.get(mat, 0) >= qty
            for mat, qty in node["cost"].items()
        )
        nodes.append({
            "id": key,
            "name": node["name"],
            "description": node["description"],
            "cost": node["cost"],
            "requires": node["requires"],
            "position": node["position"],
            "unlocked": key in unlocked,
            "can_unlock": can_unlock and key not in unlocked,
            "affordable": affordable and can_unlock and key not in unlocked,
            "unlocks": node.get("unlocks"),
        })

    return jsonify({"nodes": nodes, "unlocked": unlocked, "materials": materials})

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

    if node_key in unlocked:
        return jsonify({"error": "Déjà débloqué"}), 400
    if not all(r in unlocked for r in node["requires"]):
        return jsonify({"error": "Prérequis manquants"}), 400
    for mat, qty in node["cost"].items():
        if materials.get(mat, 0) < qty:
            return jsonify({"error": f"Pas assez de {mat}"}), 400

    # Déduire les matériaux
    inc = {f"materials.{mat}": -qty for mat, qty in node["cost"].items()}
    inc_update = {"$inc": inc, "$push": {"unlocked_nodes": node_key}}

    # Déverrouillle un monde si applicable
    if "unlocks" in node:
        inc_update["$addToSet"] = {"unlocked_worlds": node["unlocks"]}

    db.users.update_one({"user_id": request.user_id}, inc_update)
    return jsonify({"ok": True, "unlocked": node_key, "new_world": node.get("unlocks")})

# ─────────────────────────────────────────────────────────────────────────────
# Routes Pixel Map
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/pixelmap/<world_id>")
@require_auth
def get_pixelmap(world_id):
    if world_id not in WORLDS:
        return jsonify({"error": "Monde inconnu"}), 404

    doc = get_user_doc(request.user_id)
    if world_id not in doc.get("unlocked_worlds", ["monde_1"]):
        return jsonify({"error": "Monde verrouillé"}), 403

    # Récupère tous les pixels de ce monde
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

# ─────────────────────────────────────────────────────────────────────────────
# Routes Classes
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
    if doc.get("classe"):
        return jsonify({"error": "Tu as déjà choisi une classe"}), 400

    db.users.update_one(
        {"user_id": request.user_id},
        {"$set": {"classe": classe}}
    )
    return jsonify({"ok": True, "classe": classe})

# ─────────────────────────────────────────────────────────────────────────────
# Routes Classement
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    # On récupère les utilisateurs triés par points décroissants (Top 10)
    users = list(db.users.find().sort([
        ("vocal_points", -1),
        ("message_points", -1),
        ("activity_points", -1),
        ("minigame_points", -1)
    ]).limit(10))
    
    leaderboard = []
    for u in users:
        # Sécurité : On calcule le total proprement pour chaque joueur
        total = (
            u.get("vocal_points", 0) +
            u.get("message_points", 0) +
            u.get("activity_points", 0) +
            u.get("minigame_points", 0)
        )
        
        leaderboard.append({
            "user_id": str(u.get("user_id", "")), # On force en string pour le JS
            "username": u.get("username", "Joueur Anonyme"), # Nom par défaut propre
            "avatar": u.get("avatar") or None, # Évite le "undefined" si pas d'avatar
            "classe": u.get("classe"),
            "race": u.get("race"),
            "total_points": total,
            "details": {
                "vocal": u.get("vocal_points", 0),
                "messages": u.get("message_points", 0),
                "activity": u.get("activity_points", 0),
                "minigames": u.get("minigame_points", 0)
            }
        })
        
    return jsonify(leaderboard)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)

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

    # Déjà utilisé par ce joueur
    if uid in code_doc.get("used_by", []):
        return jsonify({"error": "Tu as déjà utilisé ce code 😅"}), 400

    # Limite globale
    total_max = code_doc.get("total_max")
    if total_max is not None and code_doc.get("total_used", 0) >= total_max:
        return jsonify({"error": "Ce code a atteint sa limite d'utilisations 😢"}), 400

    # Applique les récompenses
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
# GACHA — Classes & Races
# ─────────────────────────────────────────────────────────────────────────────

import random as _random

RARITIES = {
    "commun":    {"label": "Commun",    "color": "#7a7f9a", "chance": 55},
    "rare":      {"label": "Rare",      "color": "#5ca8f0", "chance": 30},
    "epique":    {"label": "Épique",    "color": "#7c5cfc", "chance": 12},
    "legendaire":{"label": "Légendaire","color": "#f5c542", "chance": 3},
}

GACHA_CLASSES = [
    # Communs
    {"id":"soldat",      "name":"Soldat ⚔️",        "rarity":"commun",    "bonus":"Résistance +10% dégâts","upgrade_discount":0.05,"shop_discount":0.0,"pixel_cost":1.0},
    {"id":"paysan",      "name":"Paysan 🌾",         "rarity":"commun",    "bonus":"Matériaux +5% à la récolte","upgrade_discount":0.0,"shop_discount":0.05,"pixel_cost":1.0},
    {"id":"marchand",    "name":"Marchand 💰",       "rarity":"commun",    "bonus":"-10% en boutique","upgrade_discount":0.0,"shop_discount":0.10,"pixel_cost":1.0},
    {"id":"eclaireur",   "name":"Éclaireur 🗺️",     "rarity":"commun",    "bonus":"Maps débloquées +vite","upgrade_discount":0.0,"shop_discount":0.0,"pixel_cost":1.0,"map_discount":0.15},
    # Rares
    {"id":"guerrier",    "name":"Guerrier 🛡️",      "rarity":"rare",      "bonus":"-15% améliorations","upgrade_discount":0.15,"shop_discount":0.0,"pixel_cost":1.0},
    {"id":"architecte",  "name":"Architecte 🏗️",   "rarity":"rare",      "bonus":"Pixels à moitié prix","upgrade_discount":0.0,"shop_discount":0.0,"pixel_cost":0.5},
    {"id":"alchimiste",  "name":"Alchimiste ⚗️",    "rarity":"rare",      "bonus":"-20% matériaux spéciaux","upgrade_discount":0.0,"shop_discount":0.15,"pixel_cost":1.0},
    {"id":"barde",       "name":"Barde 🎵",          "rarity":"rare",      "bonus":"+2pts par activité","upgrade_discount":0.0,"shop_discount":0.0,"pixel_cost":1.0,"activity_bonus":2},
    # Épiques
    {"id":"mage",        "name":"Mage 🔮",           "rarity":"epique",    "bonus":"-10% boutique + bonus quiz","upgrade_discount":0.0,"shop_discount":0.10,"pixel_cost":1.0,"activity_bonus":3},
    {"id":"paladin",     "name":"Paladin ✨",        "rarity":"epique",    "bonus":"-20% améliorations + résistance","upgrade_discount":0.20,"shop_discount":0.0,"pixel_cost":1.0},
    {"id":"ninja",       "name":"Ninja 🥷",          "rarity":"epique",    "bonus":"Pixels ×3 par achat","upgrade_discount":0.0,"shop_discount":0.0,"pixel_cost":0.33,"pixel_triple":True},
    {"id":"druide",      "name":"Druide 🌿",         "rarity":"epique",    "bonus":"Matériaux nature ×2","upgrade_discount":0.05,"shop_discount":0.10,"pixel_cost":0.8},
    # Légendaires
    {"id":"roi",         "name":"Roi 👑",            "rarity":"legendaire","bonus":"TOUT -25%","upgrade_discount":0.25,"shop_discount":0.25,"pixel_cost":0.75},
    {"id":"sorcier",     "name":"Sorcier Noir 🧙",   "rarity":"legendaire","bonus":"+5pts toutes activités + pixels gratuits","upgrade_discount":0.0,"shop_discount":0.0,"pixel_cost":0.0,"activity_bonus":5},
    {"id":"titan",       "name":"Titan ⚡",          "rarity":"legendaire","bonus":"Double points vocal/messages","upgrade_discount":0.10,"shop_discount":0.10,"pixel_cost":0.5},
]

GACHA_RACES = [
    # Communs
    {"id":"humain",      "name":"Humain 🧑",         "rarity":"commun",    "bonus":"+5% tous les points"},
    {"id":"gobelin",     "name":"Gobelin 👺",        "rarity":"commun",    "bonus":"Prix boutique -5%"},
    {"id":"orc",         "name":"Orc 💪",            "rarity":"commun",    "bonus":"Points vocal +10%"},
    {"id":"halfelin",    "name":"Halfelin 🍀",       "rarity":"commun",    "bonus":"Chance gacha +2%"},
    # Rares
    {"id":"elfe",        "name":"Elfe 🧝",           "rarity":"rare",      "bonus":"Points messages +15%"},
    {"id":"nain",        "name":"Nain ⛏️",           "rarity":"rare",      "bonus":"Matériaux -10%"},
    {"id":"demon",       "name":"Démon 😈",          "rarity":"rare",      "bonus":"Points activités +10%"},
    {"id":"beastman",   "name":"Homme-Bête 🐾",     "rarity":"rare",      "bonus":"Points vocal +20%"},
    # Épiques
    {"id":"dragon",      "name":"Semi-Dragon 🐉",    "rarity":"epique",    "bonus":"Pixels +50% par achat"},
    {"id":"ange",        "name":"Ange 😇",           "rarity":"epique",    "bonus":"-20% toute la boutique"},
    {"id":"fantome",     "name":"Fantôme 👻",        "rarity":"epique",    "bonus":"Réapparaît 1×/sem si éliminé"},
    {"id":"necromant",   "name":"Nécromanien 💀",    "rarity":"epique",    "bonus":"Récupère 50% mat. dépensés"},
    # Légendaires
    {"id":"phenix",      "name":"Phénix 🔥",         "rarity":"legendaire","bonus":"Reroll gratuit 1×/semaine"},
    {"id":"celeste",     "name":"Être Céleste ⭐",   "rarity":"legendaire","bonus":"Tous les bonus ×1.5"},
    {"id":"ancien",      "name":"Ancien 🌌",         "rarity":"legendaire","bonus":"Débloque map secrète"},
]

def weighted_pick(pool):
    """Tire un élément au hasard en respectant les chances de rareté."""
    rarity_weights = {r: RARITIES[r]["chance"] for r in RARITIES}
    # Groupe par rareté
    by_rarity = {}
    for item in pool:
        r = item["rarity"]
        by_rarity.setdefault(r, []).append(item)

    rarities     = list(by_rarity.keys())
    weights      = [rarity_weights.get(r, 1) for r in rarities]
    chosen_rarity = _random.choices(rarities, weights=weights, k=1)[0]
    return _random.choice(by_rarity[chosen_rarity]), chosen_rarity

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

@app.route("/api/gacha/pull/classe", methods=["POST"])
@require_auth
def gacha_pull_classe():
    doc = get_user_doc(request.user_id)
    if doc.get("tickets_classe", 0) < 1:
        return jsonify({"error": "Pas de ticket classe ! Achètes-en en boutique."}), 400

    result, rarity = weighted_pick(GACHA_CLASSES)
    old_classe = doc.get("classe")

    db.users.update_one(
        {"user_id": request.user_id},
        {
            "$inc": {"tickets_classe": -1},
            "$set": {"classe": result["id"]},
            "$push": {"classe_history": {
                "from": old_classe, "to": result["id"],
                "rarity": rarity, "at": datetime.utcnow()
            }}
        }
    )
    return jsonify({
        "result":   result,
        "rarity":   rarity,
        "rarity_info": RARITIES[rarity],
        "old":      old_classe,
        "tickets_left": doc.get("tickets_classe", 1) - 1,
    })

@app.route("/api/gacha/pull/race", methods=["POST"])
@require_auth
def gacha_pull_race():
    doc = get_user_doc(request.user_id)
    if doc.get("tickets_race", 0) < 1:
        return jsonify({"error": "Pas de ticket race ! Achètes-en en boutique."}), 400

    result, rarity = weighted_pick(GACHA_RACES)
    old_race = doc.get("race")

    db.users.update_one(
        {"user_id": request.user_id},
        {
            "$inc": {"tickets_race": -1},
            "$set": {"race": result["id"]},
            "$push": {"race_history": {
                "from": old_race, "to": result["id"],
                "rarity": rarity, "at": datetime.utcnow()
            }}
        }
    )
    return jsonify({
        "result":   result,
        "rarity":   rarity,
        "rarity_info": RARITIES[rarity],
        "old":      old_race,
        "tickets_left": doc.get("tickets_race", 1) - 1,
    })

# ─────────────────────────────────────────────────────────────────────────────
# QUÊTES QUOTIDIENNES
# ─────────────────────────────────────────────────────────────────────────────

import hashlib as _hashlib

QUEST_TYPES = [
    {"id":"messages", "label":"Envoie {n} messages",       "icon":"💬", "targets":[5,10,20],  "rewards":{"tickets_classe":1}},
    {"id":"vocal",    "label":"Passe {n} minutes en vocal", "icon":"🎙️","targets":[5,15,30],  "rewards":{"tickets_race":1}},
    {"id":"pixels",   "label":"Pose {n} pixels sur la map", "icon":"🎨","targets":[5,10,25],  "rewards":{"tickets_classe":1,"tickets_race":1}},
    {"id":"messages2","label":"Envoie {n} messages",        "icon":"💬","targets":[15,30,50], "rewards":{"tickets_classe":2}},
    {"id":"boutique", "label":"Achète {n} articles en boutique","icon":"🛒","targets":[1,3,5],"rewards":{"tickets_race":2}},
]

def get_daily_quest(user_id: str) -> dict:
    """Génère une quête déterministe par joueur et par jour."""
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

@app.route("/api/quests/daily")
@require_auth
def get_daily_quest_route():
    quest = get_daily_quest(request.user_id)
    doc   = get_user_doc(request.user_id)
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Progression actuelle
    progress = 0
    qid      = quest["id"]
    if qid in ("messages", "messages2"):
        # Compare les messages d'aujourd'hui
        progress = doc.get("daily_messages", 0) if doc.get("daily_date") == today else 0
    elif qid == "vocal":
        progress = doc.get("daily_vocal_minutes", 0) if doc.get("daily_date") == today else 0
    elif qid == "pixels":
        progress = doc.get("daily_pixels", 0) if doc.get("daily_date") == today else 0
    elif qid == "boutique":
        progress = doc.get("daily_purchases", 0) if doc.get("daily_date") == today else 0

    completed = doc.get("quest_completed_date") == today

    return jsonify({
        **quest,
        "progress":  min(progress, quest["target"]),
        "completed": completed,
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
    progress = 0
    qid      = quest["id"]
    if qid in ("messages","messages2"):
        progress = doc.get("daily_messages", 0) if doc.get("daily_date") == today else 0
    elif qid == "vocal":
        progress = doc.get("daily_vocal_minutes", 0) if doc.get("daily_date") == today else 0
    elif qid == "pixels":
        progress = doc.get("daily_pixels", 0) if doc.get("daily_date") == today else 0
    elif qid == "boutique":
        progress = doc.get("daily_purchases", 0) if doc.get("daily_date") == today else 0

    if progress < quest["target"]:
        return jsonify({"error": f"Pas encore terminé ({progress}/{quest['target']})"}), 400

    rewards = quest["rewards"]
    db.users.update_one(
        {"user_id": request.user_id},
        {
            "$inc": rewards,
            "$set": {"quest_completed_date": today}
        }
    )
    rewards_display = []
    for field, amt in rewards.items():
        label = {"tickets_classe":"🎫 Ticket Classe","tickets_race":"🎟️ Ticket Race"}.get(field, field)
        rewards_display.append(f"+{amt} {label}")

    return jsonify({"ok": True, "rewards": rewards_display})
