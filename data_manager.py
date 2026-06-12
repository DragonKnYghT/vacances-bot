import json
import os
from datetime import datetime, timedelta
import pytz

DATA_FILE = "data.json"
TIMEZONE = pytz.timezone("Europe/Paris")

# Conversion points → pièces DraftBot
# 1 point = 1 pièce (ajuste selon tes préférences)
POINTS_TO_DRAFTBOT = 1

# Points gagnés selon l'activité (aléatoire pour garder le fun)
import random

def get_random_points(week: int) -> int:
    """Génère des points aléatoires avec légère tendance positive."""
    pool = [-10, -5, 0, 5, 10, 15, 20, 25, 30]
    weights = [1, 2, 2, 3, 4, 5, 5, 3, 2]  # tendance positive
    return random.choices(pool, weights=weights)[0]

class DataManager:
    def __init__(self):
        self._ensure_data()

    def _ensure_data(self):
        if not os.path.exists(DATA_FILE):
            default = {
                "state": {
                    "current_week": 1,
                    "week_start": str(datetime.now(TIMEZONE).date()),
                    "started": False
                },
                "scores": {},       # { "week_1": { "user_id": { "points": X, "participations": Y } } }
                "daily_messages": []
            }
            self._save(default)

    def _load(self) -> dict:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: dict):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_state(self) -> dict:
        return self._load()["state"]

    def advance_week(self):
        data = self._load()
        data["state"]["current_week"] += 1
        data["state"]["week_start"] = str(datetime.now(TIMEZONE).date())
        self._save(data)

    def register_participation(self, user_id: str, week: int, reponse: str = None) -> dict:
        data = self._load()
        week_key = f"week_{week}"

        if week_key not in data["scores"]:
            data["scores"][week_key] = {}

        user_scores = data["scores"][week_key]
        today = str(datetime.now(TIMEZONE).date())

        if user_id not in user_scores:
            user_scores[user_id] = {"points": 0, "participations": 0, "last_played": None}

        # Anti-triche : une participation par jour
        if user_scores[user_id].get("last_played") == today:
            return {"already_played": True, "points": 0, "total": user_scores[user_id]["points"]}

        pts = get_random_points(week)
        user_scores[user_id]["points"] += pts
        user_scores[user_id]["participations"] += 1
        user_scores[user_id]["last_played"] = today
        if reponse:
            if "reponses" not in user_scores[user_id]:
                user_scores[user_id]["reponses"] = []
            user_scores[user_id]["reponses"].append(reponse)

        self._save(data)
        return {"already_played": False, "points": pts, "total": user_scores[user_id]["points"]}

    def get_week_scores(self, week: int) -> dict:
        data = self._load()
        return data["scores"].get(f"week_{week}", {})

    def get_user_total(self, user_id: str) -> dict:
        data = self._load()
        total = 0
        for week_key, week_scores in data["scores"].items():
            if user_id in week_scores:
                total += week_scores[user_id]["points"]
        return {
            "total": total,
            "draftbot_delta": total * POINTS_TO_DRAFTBOT
        }

    def get_all_scores(self) -> dict:
        """Agrège les scores de toutes les semaines."""
        data = self._load()
        all_users = {}
        for week_key, week_scores in data["scores"].items():
            for uid, stats in week_scores.items():
                if uid not in all_users:
                    all_users[uid] = {"total": 0, "draftbot_delta": 0}
                all_users[uid]["total"] += stats["points"]
                all_users[uid]["draftbot_delta"] += stats["points"] * POINTS_TO_DRAFTBOT
        return all_users

    def export_final_recap(self):
        """Exporte un JSON lisible pour toi avec ce que tu dois donner/retirer sur DraftBot."""
        all_scores = self.get_all_scores()
        export = {
            "date_export": str(datetime.now(TIMEZONE)),
            "joueurs": {}
        }
        for uid, data in all_scores.items():
            action = "DONNER" if data["draftbot_delta"] >= 0 else "RETIRER"
            export["joueurs"][uid] = {
                "points_totaux": data["total"],
                "action_draftbot": action,
                "montant": abs(data["draftbot_delta"])
            }
        with open("recap_final.json", "w", encoding="utf-8") as f:
            json.dump(export, f, indent=2, ensure_ascii=False)

    def save_daily_message(self, msg_id: int, week: int, content: dict):
        data = self._load()
        data["daily_messages"].append({
            "msg_id": msg_id,
            "week": week,
            "date": str(datetime.now(TIMEZONE).date()),
            "content_preview": str(content)[:100]
        })
        self._save(data)
