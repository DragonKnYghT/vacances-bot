import discord
from data_manager import DataManager, POINTS_PARTICIPATION, POINTS_BONNE_REPONSE

db = DataManager()

# ──────────────────────────────────────────
#  BUILDERS D'EMBEDS PAR ACTIVITÉ
# ──────────────────────────────────────────

def build_mais_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title="💰 MAIS... du jour !",
        description=(
            f"## Tu prends **{content['montant_grand']}** mais...\n"
            f"### {content['mais']}\n\n"
            f"*{content.get('contexte','')}*"
        ),
        color=0xf1c40f
    )
    embed.add_field(
        name="Comment ça marche ?",
        value=(
            f"✅ Vote pour **prendre {content['montant_grand']}** (malgré le mais...)\n"
            f"❌ Vote pour **refuser** et garder ta dignité\n\n"
            f"🏆 Si tu votes comme la majorité → tu gagnes les points affichés !\n"
            f"😐 Si tu votes différemment → +{POINTS_PARTICIPATION} pts participation quand même"
        ),
        inline=False
    )
    return embed

def build_blindtest_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title="🎵 BLIND TEST du jour !",
        description=f"**Trouve la chanson avec ces paroles :**\n\n*{content['paroles']}*",
        color=0xe91e63
    )
    embed.add_field(name="💡 Indice bonus", value=content.get("indice_bonus", "Aucun indice"), inline=False)
    embed.add_field(
        name="🎯 Comment participer ?",
        value=f"Utilise `/jouer <titre> - <artiste>` !\n+{POINTS_PARTICIPATION} pts participation | +{POINTS_BONNE_REPONSE} pts par bonne réponse (titre/artiste/source)",
        inline=False
    )
    return embed

def build_roi_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title="👑 ROI DU SERVEUR — Un Roi se cache parmi vous !",
        description="Un membre a été secrètement désigné Roi. Trouvez-le !",
        color=0xffd700
    )
    embed.add_field(name="⚔️ Règles", value=(
        "• Utilise `/deviner @membre` pour tenter de trouver le Roi\n"
        "• **3 tentatives max** par jour\n"
        "• Le Roi gagne **+2 pts** chaque heure qu'il reste non-découvert\n"
        "• Celui qui trouve le Roi gagne **+20 pts** !\n"
        "• Des indices seront envoyés toutes les 2-3 heures"
    ), inline=False)
    embed.add_field(name="🕐 Premier indice", value="Dans quelques heures...", inline=False)
    return embed

def build_sondage_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title="📊 SONDAGE ABSURDE du jour",
        description=f"## {content['question']}",
        color=0x1abc9c
    )
    emojis = content.get("emojis", ["🔴", "🟡", "🟢", "🔵"])
    for i, (opt, emoji) in enumerate(zip(content.get("options", []), emojis)):
        embed.add_field(name=f"{emoji} Option {i+1}", value=opt, inline=True)
    embed.add_field(
        name="Comment participer ?",
        value=f"Réagis avec les emojis ! +{POINTS_PARTICIPATION} pts pour avoir voté",
        inline=False
    )
    return embed

def build_dilemme_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title="🤔 DILEMME IMPOSSIBLE du jour !",
        description=f"## {content['question']}",
        color=0xe74c3c
    )
    embed.add_field(name="🇦 Option A", value=content.get("option_a", ""), inline=True)
    embed.add_field(name="🇧 Option B", value=content.get("option_b", ""), inline=True)
    if content.get("twist"):
        embed.add_field(name="⚡ Le twist", value=content["twist"], inline=False)
    embed.add_field(
        name="Comment participer ?",
        value=f"Réagis avec 🇦 ou 🇧 !\n+{POINTS_PARTICIPATION} pts participation | +{POINTS_BONNE_REPONSE} pts si tu votes comme la majorité",
        inline=False
    )
    return embed

def build_tvm_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title="🤥 DEUX VÉRITÉS UN MENSONGE — Soumets les tiennes !",
        description=content.get("invitation", "C'est l'heure du jeu !"),
        color=0xe67e22
    )
    embed.add_field(
        name="📝 Comment ça marche ?",
        value=(
            "1. Utilise `/soumettre <vérité1> | <vérité2> | <mensonge>` en DM au bot\n"
            "2. Le bot va présenter chaque soumission anonymement\n"
            "3. Les autres doivent deviner quelle affirmation est le mensonge\n"
            f"4. +{POINTS_PARTICIPATION} pts participation | +{POINTS_BONNE_REPONSE} pts si tu trouves !"
        ),
        inline=False
    )
    if content.get("exemples"):
        embed.add_field(name="💡 Exemple", value="\n".join(content["exemples"]), inline=False)
    return embed

def build_recette_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"🧪 RECETTE IMPOSSIBLE : {content.get('titre_mystere', '???')}",
        description="L'IA vous a concocté une liste d'ingrédients... à vous d'inventer la recette !",
        color=0x27ae60
    )
    ingredients_text = ""
    for ing in content.get("ingredients", []):
        niveau_emoji = {"normal": "🟢", "wtf": "🟠", "impossible": "🔴"}.get(ing.get("niveau", "normal"), "⚪")
        ingredients_text += f"{niveau_emoji} **{ing['quantite']}** de {ing['nom']}\n"
    embed.add_field(name="🥘 Ingrédients", value=ingredients_text or "???", inline=False)
    embed.add_field(name="⚠️ Contrainte", value=content.get("contrainte", ""), inline=False)
    embed.add_field(
        name="👨‍🍳 Comment participer ?",
        value=f"Utilise `/jouer <ta recette>` pour soumettre ta création !\nLes meilleures recettes seront votées. +{POINTS_PARTICIPATION} pts participation | +{POINTS_BONNE_REPONSE} pts si ta recette gagne le vote !",
        inline=False
    )
    return embed

def build_olympiade_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"{content.get('emoji','🎪')} OLYMPIADES — {content.get('nom', 'Épreuve du jour')}",
        description=content.get("description", ""),
        color=0x3498db
    )
    embed.add_field(name="📋 Comment participer ?", value=content.get("comment_participer", ""), inline=False)
    embed.add_field(name="🏅 Points", value=content.get("critere_victoire", ""), inline=False)
    return embed

# ──────────────────────────────────────────
#  PLANNING DES 8 SEMAINES
# ──────────────────────────────────────────

ACTIVITIES_SCHEDULE = {
    1: {
        "name": "Mais... (10€ ou 200€ mais...)",
        "emoji": "💰",
        "type": "mais",
        "color": 0xf1c40f,
        "description": "Chaque jour : prends l'argent mais il y a un catch ! Vote ✅ ou ❌, bonus si tu votes comme la majorité.",
        "reactions": ["✅", "❌"],
        "build_embed": build_mais_embed,
    },
    2: {
        "name": "Blind Test",
        "emoji": "🎵",
        "type": "blindtest",
        "color": 0xe91e63,
        "description": "Des paroles de chanson chaque jour → trouve titre, artiste et source !",
        "reactions": ["🎵"],
        "build_embed": build_blindtest_embed,
    },
    3: {
        "name": "Roi du Serveur",
        "emoji": "👑",
        "type": "roi_indice",
        "color": 0xffd700,
        "description": "Un Roi secret tiré au sort. Indices toutes les 2-3h, 3 tentatives max/jour. Trouvez-le !",
        "reactions": [],
        "build_embed": build_roi_embed,
    },
    4: {
        "name": "Sondage Absurde",
        "emoji": "📊",
        "type": "sondage_absurde",
        "color": 0x1abc9c,
        "description": "Des sondages fous générés par l'IA. Participe et gagne des points !",
        "reactions": ["🔴", "🟡", "🟢", "🔵"],
        "build_embed": build_sondage_embed,
    },
    5: {
        "name": "Dilemme Impossible",
        "emoji": "🤔",
        "type": "dilemme",
        "color": 0xe74c3c,
        "description": "Un dilemme impossible chaque jour. Vote et gagne si tu choisis comme la majorité !",
        "reactions": ["🇦", "🇧"],
        "build_embed": build_dilemme_embed,
    },
    6: {
        "name": "Deux Vérités Un Mensonge",
        "emoji": "🤥",
        "type": "deux_verites_mensonge_invite",
        "color": 0xe67e22,
        "description": "Soumets tes 2 vérités 1 mensonge, les autres doivent trouver lequel est faux !",
        "reactions": ["1️⃣", "2️⃣", "3️⃣"],
        "build_embed": build_tvm_embed,
    },
    7: {
        "name": "Recette Impossible",
        "emoji": "🧪",
        "type": "recette",
        "color": 0x27ae60,
        "description": "L'IA donne des ingrédients improbables, crée la meilleure recette !",
        "reactions": ["🍽️"],
        "build_embed": build_recette_embed,
    },
    8: {
        "name": "Olympiades du Serveur",
        "emoji": "🎪",
        "type": "olympiade_epreuve",
        "color": 0x3498db,
        "description": "Épreuves quotidiennes, classement dévoilé progressivement du top 10 au podium final !",
        "reactions": ["🏅"],
        "build_embed": build_olympiade_embed,
    },
}
