import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import asyncio
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from ai_generator import generate_activity_content
from data_manager import DataManager, POINTS_PARTICIPATION, POINTS_BONNE_REPONSE
from activities import ACTIVITIES_SCHEDULE
from minigames import setup_menu_command

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TIMEZONE = pytz.timezone("Europe/Paris")

# Flask géré par server.py

# ── Bot ──
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
    now = datetime.now(TIMEZONE)
    if now.hour == 10 and now.minute == 0:
        await send_daily_activity()

@tasks.loop(minutes=1)
async def weekly_scheduler():
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
                    title=f"🔄 Semaine {week_num}/8 — {activity['emoji']} {activity['name']}",
                    description=activity["description"],
                    color=activity["color"]
                )
                embed.set_footer(text="Nouvelle activité chaque jour à 10h00 !")
                await channel.send(embed=embed)
            else:
                await send_final_recap(channel)

@tasks.loop(hours=2)
async def roi_indices_scheduler():
    """Envoie un indice pour le Roi du serveur toutes les 2h (semaine 3 uniquement, pas la nuit)."""
    state = db.get_state()
    if state["current_week"] != 3:
        return
    now = datetime.now(TIMEZONE)
    if now.hour < 8 or now.hour >= 23:
        return
    today = str(now.date())
    roi_data = db.get_roi(today)
    if not roi_data or roi_data.get("found_by"):
        return
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return
    nb_indice = roi_data.get("indices_sent", 0) + 1
    try:
        content = await generate_activity_content("roi_indice", f"Indice numéro {nb_indice}, de plus en plus précis")
        db.increment_roi_indice(today)
        embed = discord.Embed(
            title=f"👑 Indice #{nb_indice} — Qui est le Roi ?",
            description=f"*{content['indice']}*",
            color=0xffd700
        )
        embed.set_footer(text="Utilise /deviner @membre pour tenter ta chance ! (3 essais/jour)")
        await channel.send(embed=embed)
    except Exception as e:
        print(f"Erreur indice roi : {e}")

async def send_daily_activity():
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

    thinking_msg = await channel.send(f"{activity_info['emoji']} *Génération de l'activité du jour...*")
    try:
        content = await generate_activity_content(activity_info["type"])
        await thinking_msg.delete()
        embed = activity_info["build_embed"](content)
        embed.set_footer(text=f"Semaine {week_num}/8 • {activity_info['name']} • +{POINTS_PARTICIPATION} pts participation | +{POINTS_BONNE_REPONSE} pts bonne réponse")
        msg = await channel.send(embed=embed)
        if activity_info.get("reactions"):
            for r in activity_info["reactions"]:
                await msg.add_reaction(r)
        db.save_daily_message(msg.id, week_num, content)

        # Semaine 3 : tirer le Roi au sort
        if week_num == 3:
            members = [m for m in channel.guild.members if not m.bot]
            if members:
                import random
                roi = random.choice(members)
                today = str(datetime.now(TIMEZONE).date())
                db.set_roi(str(roi.id), today)
                try:
                    await roi.send(
                        "👑 **Tu es le Roi du serveur aujourd'hui !**\n"
                        "Les membres vont recevoir des indices sur toi toutes les 2h.\n"
                        "Reste discret ! Tu gagnes +2 pts chaque heure que tu restes non-découvert. 🤫"
                    )
                except:
                    pass
    except Exception as e:
        await thinking_msg.edit(content=f"❌ Erreur génération : {e}")

async def send_weekly_recap(channel):
    state = db.get_state()
    week_num = state["current_week"]
    scores = db.get_week_scores(week_num)
    activity = ACTIVITIES_SCHEDULE.get(week_num, {})
    embed = discord.Embed(
        title=f"📊 Récap Semaine {week_num}/8 — {activity.get('emoji','')} {activity.get('name','')}",
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
            lines.append(f"{medal} **{name}** — {data['points']} pts")
        embed.description = "\n".join(lines)
    embed.add_field(name="ℹ️ Rappel", value="Points fictifs → pièces DraftBot à la fin des vacances !", inline=False)
    await channel.send(embed=embed)

async def send_final_recap(channel):
    all_scores = db.get_all_scores()
    embed = discord.Embed(title="🏆 RÉCAP FINAL — Vacances terminées !", color=0xe74c3c)
    if not all_scores:
        embed.description = "Aucune participation enregistrée."
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
            sign = "+" if data["draftbot_delta"] >= 0 else ""
            lines.append(f"{medal} **{name}** — {data['total']} pts → **{sign}{data['draftbot_delta']} pièces DraftBot**")
        embed.description = "\n".join(lines)
    await channel.send(embed=embed)
    db.export_final_recap()

# ──────────────────────────────────────────
#  COMMANDES SLASH
# ──────────────────────────────────────────

@tree.command(name="jouer", description="Participer à l'activité du jour")
@app_commands.describe(reponse="Ta réponse ou participation")
async def jouer(interaction: discord.Interaction, reponse: str = None):
    state = db.get_state()
    week_num = state["current_week"]
    activity = ACTIVITIES_SCHEDULE.get(week_num)
    if not activity:
        await interaction.response.send_message("❌ Aucune activité en cours.", ephemeral=True)
        return
    if db.has_played_today(str(interaction.user.id), week_num):
        await interaction.response.send_message("⏳ Tu as déjà participé aujourd'hui ! Reviens demain.", ephemeral=True)
        return
    db.add_week_points(str(interaction.user.id), week_num, POINTS_PARTICIPATION, "participation")
    result = db.get_week_scores(week_num).get(str(interaction.user.id), {})
    embed = discord.Embed(
        title=f"{activity['emoji']} Participation enregistrée !",
        color=0x2ecc71
    )
    embed.add_field(name="Points participation", value=f"+{POINTS_PARTICIPATION} pts", inline=True)
    embed.add_field(name="Total semaine", value=f"{result.get('points', POINTS_PARTICIPATION)} pts", inline=True)
    if reponse:
        embed.add_field(name="Ta réponse", value=reponse, inline=False)
    embed.set_footer(text="La bonne réponse sera révélée demain !")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="deviner", description="Deviner qui est le Roi du serveur (semaine 3)")
@app_commands.describe(membre="Le membre que tu penses être le Roi")
async def deviner(interaction: discord.Interaction, membre: discord.Member):
    state = db.get_state()
    if state["current_week"] != 3:
        await interaction.response.send_message("❌ Cette commande est disponible uniquement pendant la semaine du Roi du serveur !", ephemeral=True)
        return
    today = str(datetime.now(TIMEZONE).date())
    roi_data = db.get_roi(today)
    if not roi_data:
        await interaction.response.send_message("❌ Pas de Roi désigné aujourd'hui.", ephemeral=True)
        return
    if roi_data.get("found_by"):
        await interaction.response.send_message("❌ Le Roi a déjà été trouvé aujourd'hui !", ephemeral=True)
        return
    result = db.roi_tentative(str(interaction.user.id), today)
    if "error" in result:
        if result["error"] == "max_tentatives":
            await interaction.response.send_message("❌ Tu as épuisé tes 3 tentatives pour aujourd'hui !", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
        return
    if str(membre.id) == roi_data["roi_id"]:
        db.roi_found(str(interaction.user.id), today)
        db.add_week_points(str(interaction.user.id), 3, 20, "roi_found")
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            roi_member = channel.guild.get_member(int(roi_data["roi_id"]))
            roi_name = roi_member.display_name if roi_member else "???"
            embed = discord.Embed(
                title="👑 LE ROI A ÉTÉ DÉCOUVERT !",
                description=f"**{interaction.user.display_name}** a trouvé que **{roi_name}** était le Roi ! +20 pts 🎉",
                color=0xffd700
            )
            await channel.send(embed=embed)
        await interaction.response.send_message("✅ **BRAVO !** Tu as trouvé le Roi ! +20 pts fictifs !", ephemeral=True)
    else:
        restantes = result["tentatives_restantes"]
        await interaction.response.send_message(
            f"❌ Non, **{membre.display_name}** n'est pas le Roi ! Il te reste **{restantes} tentative(s)** aujourd'hui.",
            ephemeral=True
        )

@tree.command(name="score", description="Voir ton score fictif total")
async def score(interaction: discord.Interaction):
    data = db.get_user_total(str(interaction.user.id))
    embed = discord.Embed(title=f"💰 Score de {interaction.user.display_name}", color=0x3498db)
    embed.add_field(name="Total fictif", value=f"{data['total']} pts", inline=True)
    embed.add_field(name="Estimation DraftBot", value=f"{data['draftbot_delta']:+} pièces", inline=True)
    embed.set_footer(text="Converti en pièces DraftBot à la fin des vacances !")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="classement", description="Voir le classement de la semaine")
async def classement(interaction: discord.Interaction):
    state = db.get_state()
    week_num = state["current_week"]
    scores = db.get_week_scores(week_num)
    embed = discord.Embed(title=f"🏆 Classement — Semaine {week_num}/8", color=0xf1c40f)
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
    embed.add_field(name="Prochaine", value=f"Semaine {week_num+1}" if week_num < 8 else "Récap final !", inline=True)
    await interaction.response.send_message(embed=embed)

# ──────────────────────────────────────────
#  COMMANDE /test
# ──────────────────────────────────────────

@tree.command(name="test", description="🔧 Teste tous les systèmes du bot (admin)")
async def test_bot(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    results = []

    # Test 1 : Connexion Discord
    results.append(("✅", "Connexion Discord", "Bot connecté et opérationnel"))

    # Test 2 : Fichier de données
    try:
        state = db.get_state()
        results.append(("✅", "Base de données", f"Semaine {state['current_week']}/8 — Démarrage le {state['week_start']}"))
    except Exception as e:
        results.append(("❌", "Base de données", str(e)))

    # Test 3 : API Gemini
    try:
        content = await generate_activity_content("dilemme")
        if "question" in content:
            results.append(("✅", "API Gemini (IA)", f"Génération OK — Exemple : *{content['question'][:60]}...*"))
        else:
            results.append(("⚠️", "API Gemini (IA)", "Réponse inattendue"))
    except Exception as e:
        results.append(("❌", "API Gemini (IA)", f"Erreur : {str(e)[:100]}"))

    # Test 4 : Salon Discord
    try:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            results.append(("✅", "Salon Discord", f"#{channel.name} trouvé"))
        else:
            results.append(("❌", "Salon Discord", f"Salon ID {CHANNEL_ID} introuvable — vérifie CHANNEL_ID"))
    except Exception as e:
        results.append(("❌", "Salon Discord", str(e)))

    # Test 5 : Activités
    try:
        state = db.get_state()
        week_num = state["current_week"]
        activity = ACTIVITIES_SCHEDULE.get(week_num)
        if activity:
            results.append(("✅", "Activités", f"Semaine {week_num} : {activity['emoji']} {activity['name']}"))
        else:
            results.append(("⚠️", "Activités", f"Aucune activité pour la semaine {week_num}"))
    except Exception as e:
        results.append(("❌", "Activités", str(e)))

    # Test 6 : Mini-jeux
    try:
        from minigames import setup_menu_command
        results.append(("✅", "Mini-jeux", "Module chargé — /slot /quiz /champion /p4 disponibles"))
    except Exception as e:
        results.append(("❌", "Mini-jeux", str(e)))

    # Test 7 : Système de points
    try:
        test_result = db.add_points("test_user", 0)
        results.append(("✅", "Système de points", "Lecture/écriture OK"))
    except Exception as e:
        results.append(("❌", "Système de points", str(e)))

    # Test 8 : Tâches automatiques
    daily_ok = daily_scheduler.is_running()
    weekly_ok = weekly_scheduler.is_running()
    if daily_ok and weekly_ok:
        results.append(("✅", "Tâches automatiques", "Envoi quotidien 10h00 ✓ | Récap hebdo ✓"))
    else:
        results.append(("⚠️", "Tâches automatiques", f"Daily: {'✓' if daily_ok else '✗'} | Weekly: {'✓' if weekly_ok else '✗'}"))

    # Construire l'embed résultat
    all_ok = all(r[0] == "✅" for r in results)
    has_error = any(r[0] == "❌" for r in results)

    embed = discord.Embed(
        title="🔧 Rapport de test du bot",
        color=0x2ecc71 if all_ok else (0xe74c3c if has_error else 0xf39c12)
    )

    status_global = "✅ Tout fonctionne parfaitement !" if all_ok else ("❌ Des erreurs ont été détectées !" if has_error else "⚠️ Quelques avertissements")
    embed.description = f"**{status_global}**\n"

    for emoji, nom, detail in results:
        embed.add_field(name=f"{emoji} {nom}", value=detail, inline=False)

    embed.set_footer(text=f"Test effectué le {datetime.now(TIMEZONE).strftime('%d/%m/%Y à %H:%M')}")
    await interaction.followup.send(embed=embed, ephemeral=True)

# ──────────────────────────────────────────
#  EVENTS
# ──────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"✅ Bot connecté : {bot.user}")
    setup_menu_command(tree, bot)
    await tree.sync()
    daily_scheduler.start()
    weekly_scheduler.start()
    roi_indices_scheduler.start()
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        state = db.get_state()
        week_num = state["current_week"]
        activity = ACTIVITIES_SCHEDULE.get(week_num, {})
        embed = discord.Embed(
            title="👋 Le bot est en ligne !",
            description=(
                f"Semaine **{week_num}/8** — {activity.get('emoji','')} **{activity.get('name','')}**\n"
                f"Activité envoyée chaque matin à **10h00** !\n\n"
                f"📋 Commandes : `/menu` `/jouer` `/score` `/classement` `/semaine` `/test`"
            ),
            color=0x2ecc71
        )
        await channel.send(embed=embed)

async def run_bot():
    await bot.start(TOKEN)

# ──────────────────────────────────────────
#  POINTS MESSAGES
# ──────────────────────────────────────────

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    # 1 point par message (cooldown : 1 msg/minute compté)
    db.add_message_points(str(message.author.id))
    await bot.process_commands(message)

# ──────────────────────────────────────────
#  POINTS VOCAL
# ──────────────────────────────────────────

# Stocke l'heure d'entrée en vocal de chaque membre
_vocal_join_times = {}

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot:
        return
    uid = str(member.id)

    # Entrée en vocal
    if before.channel is None and after.channel is not None:
        _vocal_join_times[uid] = datetime.now(TIMEZONE)

    # Sortie du vocal
    elif before.channel is not None and after.channel is None:
        join_time = _vocal_join_times.pop(uid, None)
        if join_time:
            minutes = int((datetime.now(TIMEZONE) - join_time).total_seconds() / 60)
            if minutes >= 1:  # minimum 1 minute pour compter
                db.add_vocal_points(uid, minutes)
                print(f"[VOCAL] {member.display_name} : +{minutes} min → {minutes // 6} pts vocal")

# ──────────────────────────────────────────
#  POINTS RÉACTIONS (participation MAIS.../Dilemme/Sondage)
# ──────────────────────────────────────────

# Emojis qui donnent des points de participation selon l'activité
REACTION_EMOJIS = {
    "✅", "❌",           # MAIS...
    "🇦", "🇧",           # Dilemme
    "🔴", "🟡", "🟢", "🔵",  # Sondage absurde
    "1️⃣", "2️⃣", "3️⃣",  # Deux vérités un mensonge
    "🏅", "🍽️", "🎵",    # Olympiades / Recette / Blindtest
}

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return
    emoji_str = str(payload.emoji)
    if emoji_str not in REACTION_EMOJIS:
        return

    state = db.get_state()
    week_num = state["current_week"]

    # Vérifie que c'est bien sur le bon salon
    if payload.channel_id != CHANNEL_ID:
        return

    uid = str(payload.user_id)

    # Évite de compter deux fois (si l'utilisateur retire et remet une réaction)
    if db.has_played_today(uid, week_num):
        return

    db.add_week_points(uid, week_num, POINTS_PARTICIPATION, "participation")
    print(f"[REACTION] {uid} → +{POINTS_PARTICIPATION} pts participation (semaine {week_num})")
