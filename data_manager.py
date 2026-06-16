from pymongo import MongoClient
import os
from datetime import datetime
import pytz
import random

TIMEZONE = pytz.timezone("Europe/Paris")
POINTS_PARTICIPATION = 5
POINTS_BONNE_REPONSE = 3
POINTS_TO_DRAFTBOT = 1

# Connexion MongoDB
client = MongoClient(os.getenv("MONGODB_URL"))
db = client["vacances_bot"]

# Collections
users_col = db["users"]
state_col = db["state"]
scores_col = db["scores"]
roi_col = db["roi"]
tvm_col = db["tvm"]
messages_col = db["messages"]

class DataManager:
    def __init__(self):
        # Initialise l'état si vide
        if state_col.count_documents({}) == 0:
            state_col.insert_one({
                "current_week": 1,
                "week_start": str(datetime.now(TIMEZONE).date())
            })

    # ── STATE ──
    def get_state(self) -> dict:
        s = state_col.find_one({}, {"_id": 0})
        return s or {"current_week": 1, "week_start": str(datetime.now(TIMEZONE).date())}

    def advance_week(self):
        state_col.update_one({}, {"$inc": {"current_week": 1}, "$set": {"week_start": str(datetime.now(TIMEZONE).date())}})

    # ── POINTS ACTIVITÉS HEBDO ──
    def add_week_points(self, user_id: str, week: int, points: int, reason: str = "") -> dict:
        today = str(datetime.now(TIMEZONE).date())
        scores_col.update_one(
            {"user_id": user_id, "week": week},
            {
                "$inc": {"points": points, "participations": 1 if reason == "participation" else 0},
                "$set": {"last_played": today}
            },
            upsert=True
        )
        doc = scores_col.find_one({"user_id": user_id, "week": week})
        return {"total_week": doc["points"]}

    def has_played_today(self, user_id: str, week: int) -> bool:
        today = str(datetime.now(TIMEZONE).date())
        doc = scores_col.find_one({"user_id": user_id, "week": week})
        return doc and doc.get("last_played") == today

    def get_week_scores(self, week: int) -> dict:
        docs = scores_col.find({"week": week}, {"_id": 0})
        return {d["user_id"]: {"points": d["points"], "participations": d.get("participations", 0)} for d in docs}

    # ── POINTS MINI-JEUX ──
    def add_points(self, user_id: str, points: int) -> dict:
        users_col.update_one(
            {"user_id": user_id},
            {"$inc": {"minigame_points": points}},
            upsert=True
        )
        total = self.get_user_total(user_id)["total"]
        doc = users_col.find_one({"user_id": user_id})
        return {"total": total, "minigame": doc.get("minigame_points", 0)}

    # ── ROI DU SERVEUR ──
    def set_roi(self, user_id: str, day: str):
        roi_col.update_one(
            {"day": day},
            {"$set": {"roi_id": user_id, "found_by": None, "found_at": None, "indices_sent": 0, "tentatives": {}}},
            upsert=True
        )

    def get_roi(self, day: str) -> dict:
        doc = roi_col.find_one({"day": day}, {"_id": 0})
        return doc or {}

    def roi_tentative(self, user_id: str, day: str) -> dict:
        doc = roi_col.find_one({"day": day})
        if not doc:
            return {"error": "Pas de roi aujourd'hui"}
        tentatives = doc.get("tentatives", {})
        count = tentatives.get(user_id, 0)
        if count >= 3:
            return {"error": "max_tentatives"}
        tentatives[user_id] = count + 1
        roi_col.update_one({"day": day}, {"$set": {"tentatives": tentatives}})
        return {"tentatives_restantes": 3 - tentatives[user_id]}

    def roi_found(self, finder_id: str, day: str):
        roi_col.update_one({"day": day}, {"$set": {"found_by": finder_id, "found_at": str(datetime.now(TIMEZONE))}})

    def increment_roi_indice(self, day: str):
        roi_col.update_one({"day": day}, {"$inc": {"indices_sent": 1}})

    # ── SCORES GLOBAUX ──
    def get_user_total(self, user_id: str) -> dict:
        week_docs = scores_col.find({"user_id": user_id})
        week_total = sum(d.get("points", 0) for d in week_docs)
        user_doc = users_col.find_one({"user_id": user_id}) or {}
        minigame_total = user_doc.get("minigame_points", 0)
        total = week_total + minigame_total
        return {"total": total, "draftbot_delta": total * POINTS_TO_DRAFTBOT}

    def get_all_scores(self) -> dict:
        all_users = {}
        for doc in scores_col.find():
            uid = doc["user_id"]
            if uid not in all_users:
                all_users[uid] = {"total": 0, "draftbot_delta": 0}
            all_users[uid]["total"] += doc.get("points", 0)
        for doc in users_col.find():
            uid = doc["user_id"]
            if uid not in all_users:
                all_users[uid] = {"total": 0, "draftbot_delta": 0}
            all_users[uid]["total"] += doc.get("minigame_points", 0)
        for uid in all_users:
            all_users[uid]["draftbot_delta"] = all_users[uid]["total"] * POINTS_TO_DRAFTBOT
        return all_users

    def save_daily_message(self, msg_id: int, week: int, content: dict):
        messages_col.insert_one({
            "msg_id": msg_id,
            "week": week,
            "date": str(datetime.now(TIMEZONE).date()),
            "content_preview": str(content)[:100]
        })

    def export_final_recap(self):
        import json
        all_scores = self.get_all_scores()
        export = {"date_export": str(datetime.now(TIMEZONE)), "joueurs": {}}
        for uid, data in all_scores.items():
            action = "DONNER" if data["draftbot_delta"] >= 0 else "RETIRER"
            export["joueurs"][uid] = {
                "points_totaux": data["total"],
                "action_draftbot": action,
                "montant": abs(data["draftbot_delta"])
            }
        with open("recap_final.json", "w", encoding="utf-8") as f:
            json.dump(export, f, indent=2, ensure_ascii=False)

    def get_olympiade_ranking(self, week: int) -> list:
        scores = self.get_week_scores(week)
        return sorted(scores.items(), key=lambda x: x[1]["points"], reverse=True)

    def save_tvm(self, user_id: str, day: str, verites: list, mensonge: str):
        tvm_col.update_one(
            {"day": day, "user_id": user_id},
            {"$set": {"verites": verites, "mensonge": mensonge, "repondants": {}}},
            upsert=True
        )

    def get_tvm_list(self, day: str) -> list:
        return list(tvm_col.find({"day": day}, {"_id": 0}))

    # ── POINTS VOCAUX ET MESSAGES (pour le site) ──
    def add_vocal_points(self, user_id: str, minutes: int):
        pts = minutes // 6  # 10 pts par heure (1 pt par 6 min)
        if pts > 0:
            users_col.update_one(
                {"user_id": user_id},
                {"$inc": {"vocal_points": pts, "vocal_minutes": minutes}},
                upsert=True
            )

    def add_message_points(self, user_id: str):
        users_col.update_one(
            {"user_id": user_id},
            {"$inc": {"message_points": 1}},
            upsert=True
        )

    def get_user_site_data(self, user_id: str) -> dict:
        """Données pour le profil du site : UNIQUEMENT messages, vocal, pixels. 
        Suppression totale du choix de classe manuel et des points d'activités/mini-jeux."""
        doc = users_col.find_one({"user_id": user_id}, {"_id": 0}) or {}
        
        # On calcule le total uniquement avec le vocal et les messages
        vocal = doc.get("vocal_points", 0)
        messages = doc.get("message_points", 0)
        total = vocal + messages
        
        return {
            "user_id": user_id,
            "username": doc.get("username", "Joueur Inconnu"),
            "avatar": doc.get("avatar", None),
            "total_points": total,
            "vocal_points": vocal,
            "message_points": messages,
            "pixels": doc.get("pixels", []),
            # On a retiré : "classe" et "minigame_points"
        }

    def set_user_classe(self, user_id: str, classe: str):
        users_col.update_one({"user_id": user_id}, {"$set": {"classe": classe}}, upsert=True)

