"""
Point d'entrée principal pour Render.
Lance Flask sur le bon port, puis le bot Discord.
"""
import os
import asyncio
import threading
from dotenv import load_dotenv

load_dotenv()

from web.app import app as web_app

app = web_app

@app.route("/")
def home():
    return "Bot en ligne ! 🤖", 200

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    # Lance le bot dans un thread séparé
    def run_bot():
        import bot as discord_bot
        asyncio.run(discord_bot.run_bot())

    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # Flask en principal (Render détecte le port)
    port = int(os.getenv("PORT", 10000))
    print(f"🌐 Serveur web démarré sur le port {port}")
    app.run(host="0.0.0.0", port=port, use_reloader=False)
