"""
Point d'entrée principal.
Lance Flask (port détecté par Render) + le bot Discord en parallèle.
"""
import asyncio
import threading
import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

# ── Serveur web Flask (pour Render) ──
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot en ligne ! 🤖", 200

@app.route("/health")
def health():
    return "OK", 200

def run_flask():
    port = int(os.getenv("PORT", 8080))
    print(f"🌐 Serveur web démarré sur le port {port}")
    app.run(host="0.0.0.0", port=port, use_reloader=False)

# ── Bot Discord ──
def run_bot():
    # Import ici pour éviter les conflits d'import
    import bot as discord_bot
    asyncio.run(discord_bot.run_bot())

if __name__ == "__main__":
    # Lance Flask en thread (Render détecte le port immédiatement)
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Lance le bot Discord dans le thread principal
    run_bot()
