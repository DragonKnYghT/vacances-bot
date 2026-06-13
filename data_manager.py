import json
import os
from datetime import datetime, timedelta
import pytz
import random

DATA_FILE = "data.json"
TIMEZONE = pytz.timezone("Europe/Paris")

POINTS_PARTICIPATION = 5
POINTS_BONNE_REPONSE = 3
POINTS_TO_DRAFTBOT = 1

class DataManager:
    def __init__(self):
        self._ensure_data()

    def _ensure_data(self):
        if not os.path.exists(DATA_FILE):
            self._save({
                "state": {
                    "current_week": 1,
                    "week_start": str(datetime.now(TIMEZONE).date()),
                },
                "scores": {},
                "minigames": {},
                "roi": {},
                "daily_messages": []
            })

    def _load(self) -> dict:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: dict):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ── STATE ──
    def get_state(self) -> dict:
        return self._load()["state"]

    def advance_week(self):
        data = self._load()
        data["state"]["current_week"] += 1
        data["state"]["week_start"] = str(datetime.now(TIMEZONE).date())
        self._save(data)

    # ── POINTS ACTIVITÉS HEBDO ──
    def add_week_points(self, user_id: str, week: int, points: int, reason: str = "") -> dict:
        data = self._load()
        key = f"week_{week}"
        if key not in data["scores"]:
            data["scores"][key] = {}
        if user_id not in data["scores"][key]:
            data["scores"][key][user_id] = {"points": 0, "participations": 0, "last_played": None}
        data["scores"][key][user_id]["points"] += points
        if reason == "participation":
            data["scores"][key][user_id]["participations"] += 1
        data["scores"][key][user_id]["last_played"] = str(datetime.now(TIMEZONE).date())
        self._save(data)
        return {"total_week": data["scores"][key][user_id]["points"]}

    def has_played_today(self, user_id: str, week: int) -> bool:
        data = self._load()
        key = f"week_{week}"
        today = str(datetime.now(TIMEZONE).date())
        user = data["scores"].get(key, {}).get(user_id, {})
        return user.get("last_played") == today

    def get_week_scores(self, week: int) -> dict:
        return self._load()["scores"].get(f"week_{week}", {})

    # ── POINTS MINI-JEUX ──
    def add_points(self, user_id: str, points: int) -> dict:
        data = self._load()
        if user_id not in data["minigames"]:
            data["minigames"][user_id] = {"points": 0}
        data["minigames"][user_id]["points"] += points
        self._save(data)
        total = self.get_user_total(user_id)["total"]
        return {"total": total, "minigame": data["minigames"][user_id]["points"]}

    # ── ROI DU SERVEUR ──
    def set_roi(self, user_id: str, day: str):
        data = self._load()
        data["roi"][day] = {
            "roi_id": user_id,
            "found_by": None,
            "found_at": None,
            "indices_sent": 0,
            "tentatives": {}
        }
        self._save(data)

    def get_roi(self, day: str) -> dict:
        return self._load()["roi"].get(day, {})

    def roi_tentative(self, user_id: str, day: str) -> dict:
        data = self._load()
        roi_data = data["roi"].get(day, {})
        if not roi_data:
            return {"error": "Pas de roi aujourd'hui"}
        tentatives = roi_data.get("tentatives", {})
        count = tentatives.get(user_id, 0)
        if count >= 3:
            return {"error": "max_tentatives"}
        tentatives[user_id] = count + 1
        data["roi"][day]["tentatives"] = tentatives
        self._save(data)
        return {"tentatives_restantes": 3 - tentatives[user_id]}

    def roi_found(self, finder_id: str, day: str):
        data = self._load()
        if day in data["roi"]:
            data["roi"][day]["found_by"] = finder_id
            data["roi"][day]["found_at"] = str(datetime.now(TIMEZONE))
        self._save(data)

    def increment_roi_indice(self, day: str):
        data = self._load()
        if day in data["roi"]:
            data["roi"][day]["indices_sent"] = data["roi"][day].get("indices_sent", 0) + 1
        self._save(data)

    # ── SCORES GLOBAUX ──
    def get_user_total(self, user_id: str) -> dict:
        data = self._load()
        week_total = sum(
            data["scores"].get(k, {}).get(user_id, {}).get("points", 0)
            for k in data["scores"]
        )
        minigame_total = data["minigames"].get(user_id, {}).get("points", 0)
        total = week_total + minigame_total
        return {"total": total, "draftbot_delta": total * POINTS_TO_DRAFTBOT}

    def get_all_scores(self) -> dict:
        data = self._load()
        all_users = {}
        for week_key, week_scores in data["scores"].items():
            for uid, stats in week_scores.items():
                if uid not in all_users:
                    all_users[uid] = {"total": 0, "draftbot_delta": 0}
                all_users[uid]["total"] += stats["points"]
        for uid, stats in data["minigames"].items():
            if uid not in all_users:
                all_users[uid] = {"total": 0, "draftbot_delta": 0}
            all_users[uid]["total"] += stats["points"]
        for uid in all_users:
            all_users[uid]["draftbot_delta"] = all_users[uid]["total"] * POINTS_TO_DRAFTBOT
        return all_users

    def save_daily_message(self, msg_id: int, week: int, content: dict):
        data = self._load()
        data["daily_messages"].append({
            "msg_id": msg_id,
            "week": week,
            "date": str(datetime.now(TIMEZONE).date()),
            "content_preview": str(content)[:100]
        })
        self._save(data)

    def export_final_recap(self):
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

    # ── OLYMPIADES ──
    def add_olympiade_score(self, user_id: str, week: int, points: int):
        self.add_week_points(user_id, week, points, "olympiade")

    def get_olympiade_ranking(self, week: int) -> list:
        scores = self.get_week_scores(week)
        return sorted(scores.items(), key=lambda x: x[1]["points"], reverse=True)

    # ── 2 VÉRITÉS 1 MENSONGE ──
    def save_tvm(self, user_id: str, day: str, verites: list, mensonge: str):
        data = self._load()
        if "tvm" not in data:
            data["tvm"] = {}
        data["tvm"][f"{day}_{user_id}"] = {
            "user_id": user_id,
            "verites": verites,
            "mensonge": mensonge,
            "repondants": {}
        }
        self._save(data)

    def get_tvm_list(self, day: str) -> list:
        data = self._load()
        tvm = data.get("tvm", {})
        return [v for k, v in tvm.items() if k.startswith(day)]

