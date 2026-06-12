import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import json
import asyncio
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from ai_generator import generate_activity_content
from data_manager import DataManager
from activities import ACTIVITIES_SCHEDULE

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TIMEZONE = pytz.timezone("Europe/Paris")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
db = DataManager()

# ──────────────────────────────────────────
#  TÂCHES AUTOMATIQUES
# ──────────────────────────────────────────

@tasks.loop(minutes=1)
async def daily_scheduler():
    """Vérifie chaque minute si on doit envoyer l'activité du jour."""
    now = datetime.now(TIMEZONE)
    # Envoi à 10h00 pile
    if now.hour == 10 and now.minute == 0:
        await send_daily_activity()

@tasks.loop(minutes=1)
async def weekly_scheduler():
    """Vérifie chaque minute si une semaine s'est écoulée (lundi 10h00)."""
    now = datetime.now(TIMEZONE)
    state = db.get_state()
    start = datetime.fromisoformat(state["week_start"]).replace(tzinfo=TIMEZONE)

    if now >= start + timedelta(weeks=1) and now.hour == 10 and now.minute == 0:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await send_weekly_recap(channel)
            db.advance_week()
            new_state = db.get_state()
            week_num = new_state["current_week"]
            if week_num <= 8:
                activity = ACTIVITIES_SCHEDULE.get(week_num)
                embed = discord.Embed(
                    title=f"🔄 Semaine {week_num} — {activity['emoji']} {activity['name']}",
                    description=activity["description"],
                    color=activity["color"]
                )
                embed.set_footer(text="Une nouvelle activité chaque jour à 10h00 !")
                await channel.send(embed=embed)
            else:
                await send_final_recap(channel)

async def send_daily_activity():
    """Génère et envoie l'activité du jour via l'IA."""
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    state = db.get_state()
    week_num = state["current_week"]

    if week_num > 8:
        return

    activity_info = ACTIVITIES_SCHEDULE.get(week_num)
    if not activity_info:
        return

    # Génération IA du contenu
    thinking_msg = await channel.send(f"{activity_info['emoji']} *Génération de l'activité du jour...*")
    try:
        content = await generate_activity_content(activity_info["type"], activity_info.get("ai_prompt", ""))
        await thinking_msg.delete()
        embed = activity_info["build_embed"](content)
        embed.set_footer(text=f"Semaine {week_num}/8 • {activity_info['name']} • Réagis ou utilise /jouer pour participer !")
        msg = await channel.send(embed=embed)

        # Ajouter réactions si c'est un vote/dilemme
        if activity_info.get("reactions"):
            for r in activity_info["reactions"]:
                await msg.add_reaction(r)

        db.save_daily_message(msg.id, week_num, content)
    except Exception as e:
        await thinking_msg.edit(content=f"❌ Erreur lors de la génération : {e}")

async def send_weekly_recap(channel):
    """Envoie le récap de fin de semaine avec scores fictifs."""
    state = db.get_state()
    week_num = state["current_week"]
    scores = db.get_week_scores(week_num)
    activity = ACTIVITIES_SCHEDULE.get(week_num, {})

    embed = discord.Embed(
        title=f"📊 Récap Semaine {week_num} — {activity.get('emoji','')} {activity.get('name','')}",
        color=0xf1c40f
    )

    if not scores:
        embed.description = "Personne n'a participé cette semaine 😢"
    else:
        sorted_scores = sorted(scores.items(), key=lambda x: x[1]["points"], reverse=True)
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (uid, data) in enumerate(sorted_scores[:10]):
            try:
                user = await bot.fetch_user(int(uid))
                name = user.display_name
            except:
                name = f"Joueur #{uid[-4:]}"
            medal = medals[i] if i < 3 else f"{i+1}."
            pts = data["points"]
            sign = "+" if pts >= 0 else ""
            lines.append(f"{medal} **{name}** — {sign}{pts} pts fictifs")
        embed.description = "\n".join(lines)

    embed.add_field(
        name="ℹ️ Rappel",
        value="Ces points sont fictifs et seront convertis en pièces DraftBot à la fin des vacances !",
        inline=False
    )
    await channel.send(embed=embed)

async def send_final_recap(channel):
    """Récap final des 8 semaines → conversion DraftBot."""
    all_scores = db.get_all_scores()

    embed = discord.Embed(
        title="🏆 RÉCAP FINAL — Les Vacances sont terminées !",
        description="Voici le bilan complet des 8 semaines de jeu 🎉",
        color=0xe74c3c
    )

    if not all_scores:
        embed.add_field(name="Résultat", value="Aucune participation enregistrée.", inline=False)
    else:
        sorted_final = sorted(all_scores.items(), key=lambda x: x[1]["total"], reverse=True)
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (uid, data) in enumerate(sorted_final[:15]):
            try:
                user = await bot.fetch_user(int(uid))
                name = user.display_name
            except:
                name = f"Joueur #{uid[-4:]}"
            medal = medals[i] if i < 3 else f"{i+1}."
            total = data["total"]
            draftbot = data["draftbot_delta"]
            sign = "+" if draftbot >= 0 else ""
            lines.append(f"{medal} **{name}** — {total} pts → **{sign}{draftbot} pièces DraftBot**")
        embed.description = "\n".join(lines)

    embed.add_field(
        name="📋 Pour toi (admin)",
        value="Un fichier `recap_final.json` a été généré avec tous les montants à appliquer sur DraftBot.",
        inline=False
    )
    await channel.send(embed=embed)
    db.export_final_recap()

# ──────────────────────────────────────────
#  COMMANDES SLASH
# ──────────────────────────────────────────

@tree.command(name="jouer", description="Participer à l'activité de la semaine")
@app_commands.describe(reponse="Ta réponse (pour les devinettes, quiz, etc.)")
async def jouer(interaction: discord.Interaction, reponse: str = None):
    state = db.get_state()
    week_num = state["current_week"]
    activity = ACTIVITIES_SCHEDULE.get(week_num)

    if not activity:
        await interaction.response.send_message("❌ Aucune activité en cours.", ephemeral=True)
        return

    result = db.register_participation(str(interaction.user.id), week_num, reponse)

    if result["already_played"]:
        await interaction.response.send_message("⏳ Tu as déjà participé aujourd'hui ! Reviens demain.", ephemeral=True)
        return

    pts = result["points"]
    sign = "+" if pts >= 0 else ""
    total = result["total"]

    embed = discord.Embed(
        title=f"{activity['emoji']} Participation enregistrée !",
        color=0x2ecc71 if pts >= 0 else 0xe74c3c
    )
    embed.add_field(name="Points du jour", value=f"{sign}{pts} pts fictifs", inline=True)
    embed.add_field(name="Total semaine", value=f"{total} pts fictifs", inline=True)
    if reponse:
        embed.add_field(name="Ta réponse", value=reponse, inline=False)
    embed.set_footer(text="Ces points seront convertis en pièces DraftBot à la fin des vacances !")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="score", description="Voir ton score fictif total")
async def score(interaction: discord.Interaction):
    data = db.get_user_total(str(interaction.user.id))
    embed = discord.Embed(title=f"💰 Score de {interaction.user.display_name}", color=0x3498db)
    embed.add_field(name="Total fictif", value=f"{data['total']} pts", inline=True)
    embed.add_field(name="Conversion DraftBot estimée", value=f"{data['draftbot_delta']:+} pièces", inline=True)
    embed.set_footer(text="Converti en vrai argent DraftBot à la fin des vacances !")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="classement", description="Voir le classement du serveur")
async def classement(interaction: discord.Interaction):
    state = db.get_state()
    week_num = state["current_week"]
    scores = db.get_week_scores(week_num)

    embed = discord.Embed(title=f"🏆 Classement — Semaine {week_num}", color=0xf1c40f)

    if not scores:
        embed.description = "Aucune participation encore cette semaine."
    else:
        sorted_scores = sorted(scores.items(), key=lambda x: x[1]["points"], reverse=True)
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (uid, data) in enumerate(sorted_scores[:10]):
            try:
                user = await bot.fetch_user(int(uid))
                name = user.display_name
            except:
                name = f"Joueur #{uid[-4:]}"
            medal = medals[i] if i < 3 else f"{i+1}."
            lines.append(f"{medal} **{name}** — {data['points']} pts")
        embed.description = "\n".join(lines)

    await interaction.response.send_message(embed=embed)

@tree.command(name="semaine", description="Infos sur la semaine en cours")
async def semaine_info(interaction: discord.Interaction):
    state = db.get_state()
    week_num = state["current_week"]
    activity = ACTIVITIES_SCHEDULE.get(week_num, {})
    start = datetime.fromisoformat(state["week_start"]).replace(tzinfo=TIMEZONE)
    end = start + timedelta(weeks=1)
    jours = max(0, (end - datetime.now(TIMEZONE)).days)

    embed = discord.Embed(
        title=f"📅 Semaine {week_num}/8 — {activity.get('emoji','')} {activity.get('name','')}",
        description=activity.get("description", ""),
        color=activity.get("color", 0x7289da)
    )
    embed.add_field(name="Jours restants", value=f"{jours} jour(s)", inline=True)
    embed.add_field(name="Prochaine activité", value=f"Semaine {week_num+1}" if week_num < 8 else "Récap final !", inline=True)
    await interaction.response.send_message(embed=embed)

# ──────────────────────────────────────────
#  EVENTS
# ──────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"✅ Bot connecté : {bot.user}")
    await tree.sync()
    daily_scheduler.start()
    weekly_scheduler.start()

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        state = db.get_state()
        week_num = state["current_week"]
        activity = ACTIVITIES_SCHEDULE.get(week_num, {})
        embed = discord.Embed(
            title="👋 Le bot est en ligne !",
            description=f"Nous sommes à la **semaine {week_num}/8**\n{activity.get('emoji','')} Activité : **{activity.get('name','')}**\nL'activité du jour est envoyée chaque matin à **10h00** !",
            color=0x2ecc71
        )
        await channel.send(embed=embed)

bot.run(TOKEN)
