import discord

# ──────────────────────────────────────────────────────────────
#  PLANNING DES 8 SEMAINES
#  Modifie les "name" et "type" selon les résultats de tes votes !
#  Les types disponibles : dilemme, fake_news, quiz, geoguessr,
#                          boss, ce_que_tu_preferes, sondage_absurde,
#                          deux_verites_mensonge, histoire_collaborative, defi
# ──────────────────────────────────────────────────────────────

def build_dilemme_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title="🤔 DILEMME IMPOSSIBLE du jour !",
        description=f"## {content['question']}",
        color=0xe74c3c
    )
    embed.add_field(name="🅰️ Option A", value=content["option_a"], inline=True)
    embed.add_field(name="🅱️ Option B", value=content["option_b"], inline=True)
    if content.get("twist"):
        embed.add_field(name="⚡ Le twist", value=content["twist"], inline=False)
    embed.add_field(name="Comment voter ?", value="Réagis avec 🅰️ ou 🅱️ !", inline=False)
    return embed

def build_fake_news_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"📰 {content['titre']}",
        description=content["contenu"],
        color=0x95a5a6
    )
    embed.set_footer(text=f"Source : {content['source']} | ⚠️ C'est une FAKE NEWS fictive et humoristique !")
    embed.add_field(name="🎯 À toi !", value="Utilise `/jouer` pour donner ton avis ou inventer la suite !", inline=False)
    return embed

def build_quiz_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title="🧠 QUIZ du jour !",
        description=f"## {content['question']}",
        color=0x3498db
    )
    embed.add_field(name="💡 Indice", value=f"||{content['indice']}||", inline=False)
    embed.add_field(name="✅ Réponse", value=f"||{content['reponse']}||", inline=True)
    embed.add_field(name="📚 Anecdote", value=f"||{content['anecdote']}||", inline=False)
    embed.add_field(name="Comment jouer ?", value="Utilise `/jouer <ta réponse>` pour participer !", inline=False)
    return embed

def build_geoguessr_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title="🗺️ GEOGUESSR TEXTUEL — Trouve le lieu !",
        description=f"**Difficulté : {content['difficulte']}**",
        color=0x27ae60
    )
    for i, indice in enumerate(content["indices"], 1):
        embed.add_field(name=f"Indice {i}", value=indice, inline=False)
    embed.add_field(name="✅ Réponse", value=f"||{content['reponse']}||", inline=True)
    embed.add_field(name="🌍 Anecdote", value=f"||{content['anecdote']}||", inline=True)
    embed.add_field(name="Comment jouer ?", value="Utilise `/jouer <nom du lieu>` pour répondre !", inline=False)
    return embed

def build_boss_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"⚔️ BOSS DE LA SEMAINE : {content['nom']}",
        description=content["description"],
        color=0x8e44ad
    )
    embed.add_field(name="❤️ PV du boss", value=f"{content['pv']} HP", inline=True)
    embed.add_field(name="🏆 Récompense", value=content["recompense"], inline=True)
    attaques = "\n".join([f"• {a}" for a in content["attaques"]])
    embed.add_field(name="⚡ Attaques", value=attaques, inline=False)
    embed.add_field(name="Comment attaquer ?", value="Utilise `/jouer` pour infliger des dégâts aléatoires !", inline=False)
    return embed

def build_preference_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title="❓ CE QUE TU PRÉFÈRES",
        description=f"## {content['question']}",
        color=0xf39c12
    )
    embed.add_field(name=f"{content['emoji_a']} Option A", value=content["option_a"], inline=True)
    embed.add_field(name=f"{content['emoji_b']} Option B", value=content["option_b"], inline=True)
    embed.add_field(name="Comment voter ?", value=f"Réagis avec {content['emoji_a']} ou {content['emoji_b']} !", inline=False)
    return embed

def build_sondage_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title="📊 SONDAGE ABSURDE du jour",
        description=f"## {content['question']}",
        color=0x1abc9c
    )
    for i, (opt, emoji) in enumerate(zip(content["options"], content["emojis"])):
        embed.add_field(name=f"{emoji} Option {i+1}", value=opt, inline=True)
    embed.add_field(name="Comment voter ?", value="Réagis avec les emojis ci-dessus !", inline=False)
    return embed

def build_deux_verites_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"🤥 DEUX VÉRITÉS UN MENSONGE — Thème : {content['theme']}",
        description="Laquelle est fausse ?",
        color=0xe67e22
    )
    for i, aff in enumerate(content["affirmations"], 1):
        embed.add_field(name=f"Affirmation {i}", value=aff["texte"], inline=False)
    embed.add_field(name="✅ Réponse", value=f"||{content['explication']}||", inline=False)
    embed.add_field(name="Comment jouer ?", value="Utilise `/jouer 1`, `/jouer 2` ou `/jouer 3` !", inline=False)
    return embed

def build_histoire_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"✍️ HISTOIRE COLLABORATIVE — {content['genre']}",
        description=content["debut"],
        color=0x2980b9
    )
    embed.add_field(name="🔮 Et maintenant ?", value=content["cliffhanger"], inline=False)
    embed.add_field(name="Comment participer ?", value="Utilise `/jouer <ta suite>` pour continuer l'histoire !", inline=False)
    return embed

def build_defi_embed(content: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"🔥 DÉFI DE LA SEMAINE : {content['titre']}",
        description=content["description"],
        color=0xc0392b
    )
    embed.add_field(name="📸 Comment participer ?", value=content["comment_participer"], inline=False)
    embed.add_field(name="🏆 Récompense", value=content["recompense"], inline=True)
    return embed

# ──────────────────────────────────────────────────────────────
#  PLANNING — Modifie selon les résultats de tes votes !
#  Ordre suggéré basé sur les votes (du plus populaire au moins)
# ──────────────────────────────────────────────────────────────

ACTIVITIES_SCHEDULE = {
    1: {
        "name": "Dilemme Impossible",
        "emoji": "🤔",
        "type": "dilemme",
        "color": 0xe74c3c,
        "description": "Chaque jour un dilemme impossible généré par l'IA. Vote 🅰️ ou 🅱️ !",
        "reactions": ["🇦", "🇧"],
        "build_embed": build_dilemme_embed,
    },
    2: {
        "name": "Fake News du Jour",
        "emoji": "📰",
        "type": "fake_news",
        "color": 0x95a5a6,
        "description": "L'IA génère une fausse info absurde et humoristique chaque jour !",
        "reactions": ["😂", "🤯", "💀"],
        "build_embed": build_fake_news_embed,
    },
    3: {
        "name": "Sondage Absurde",
        "emoji": "📊",
        "type": "sondage_absurde",
        "color": 0x1abc9c,
        "description": "Des sondages complètement absurdes générés chaque jour par l'IA !",
        "reactions": ["🔴", "🟡", "🟢", "🔵"],
        "build_embed": build_sondage_embed,
    },
    4: {
        "name": "Quiz Culture",
        "emoji": "🧠",
        "type": "quiz",
        "color": 0x3498db,
        "description": "Une question de culture générale par jour. Qui sera le plus fort ?",
        "reactions": ["✅"],
        "build_embed": build_quiz_embed,
    },
    5: {
        "name": "2 Vérités 1 Mensonge",
        "emoji": "🤥",
        "type": "deux_verites_mensonge",
        "color": 0xe67e22,
        "description": "Trouve le mensonge parmi les 3 affirmations !",
        "reactions": ["1️⃣", "2️⃣", "3️⃣"],
        "build_embed": build_deux_verites_embed,
    },
    6: {
        "name": "Ce Que Tu Préfères",
        "emoji": "❓",
        "type": "ce_que_tu_preferes",
        "color": 0xf39c12,
        "description": "A ou B ? Des choix impossibles chaque jour !",
        "reactions": [],  # les emojis viennent du contenu IA
        "build_embed": build_preference_embed,
    },
    7: {
        "name": "Histoire Collaborative",
        "emoji": "✍️",
        "type": "histoire_collaborative",
        "color": 0x2980b9,
        "description": "L'IA lance une histoire, vous la continuez avec `/jouer` !",
        "reactions": ["📖"],
        "build_embed": build_histoire_embed,
    },
    8: {
        "name": "GeoGuessr Textuel",
        "emoji": "🗺️",
        "type": "geoguessr",
        "color": 0x27ae60,
        "description": "Trouve le lieu grâce aux indices ! Le premier qui répond correctement gagne.",
        "reactions": ["🌍"],
        "build_embed": build_geoguessr_embed,
    },
}
