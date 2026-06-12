import aiohttp
import os
import json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

PROMPTS = {
    "dilemme": """Génère un dilemme impossible drôle et original pour un serveur Discord francophone.
Format JSON strict :
{
  "question": "Tu dois choisir entre [option A] OU [option B] ?",
  "option_a": "description courte de A",
  "option_b": "description courte de B",
  "twist": "une conséquence absurde/drôle pour rendre le choix difficile"
}
Sois créatif, absurde, et drôle. Pas de violence ni de contenu choquant.""",

    "fake_news": """Génère une fausse information humoristique et absurde pour un serveur Discord francophone.
Format JSON strict :
{
  "titre": "titre de fake news absurde",
  "contenu": "2-3 phrases d'un article fictif complètement absurde",
  "source": "nom d'un faux journal fictif et drôle"
}
Doit être clairement fictif et humoristique, rien de politique ni d'offensant.""",

    "quiz": """Génère une question de quiz culture générale originale.
Format JSON strict :
{
  "question": "la question",
  "reponse": "la réponse correcte",
  "indice": "un indice pas trop facile",
  "anecdote": "une anecdote fun sur la réponse"
}""",

    "geoguessr": """Génère un défi GeoGuessr textuel : décris un lieu sans le nommer.
Format JSON strict :
{
  "indices": ["indice 1", "indice 2", "indice 3", "indice 4"],
  "reponse": "nom du lieu",
  "difficulte": "Facile/Moyen/Difficile",
  "anecdote": "fait fun sur ce lieu"
}
Du plus vague au plus précis.""",

    "boss": """Génère un boss de semaine RPG fun pour un serveur Discord.
Format JSON strict :
{
  "nom": "nom du boss",
  "description": "description épique du boss en 1-2 phrases",
  "pv": 1000,
  "attaques": ["attaque 1", "attaque 2", "attaque 3"],
  "recompense": "récompense pour le vainqueur"
}
Style humour, pas trop sérieux.""",

    "ce_que_tu_preferes": """Génère une question "ce que tu préfères" fun et originale.
Format JSON strict :
{
  "question": "Tu préfères... [A] ou [B] ?",
  "option_a": "option A",
  "option_b": "option B",
  "emoji_a": "emoji pour A",
  "emoji_b": "emoji pour B"
}
Thèmes fun : nourriture, situations absurdes, super-pouvoirs, voyages, etc.""",

    "sondage_absurde": """Génère un sondage absurde et fun pour Discord avec 3-4 options.
Format JSON strict :
{
  "question": "question absurde",
  "options": ["option 1", "option 2", "option 3", "option 4"],
  "emojis": ["🔴", "🟡", "🟢", "🔵"]
}""",

    "deux_verites_mensonge": """Génère un jeu "2 vérités 1 mensonge" sur un thème fun ou culturel.
Format JSON strict :
{
  "theme": "thème",
  "affirmations": [
    {"texte": "affirmation 1", "vrai": true},
    {"texte": "affirmation 2", "vrai": false},
    {"texte": "affirmation 3", "vrai": true}
  ],
  "explication": "explication du mensonge"
}""",

    "histoire_collaborative": """Génère le début d'une histoire collaborative fun avec un cliffhanger.
Format JSON strict :
{
  "debut": "2-3 phrases d'accroche de l'histoire",
  "cliffhanger": "la question/situation qui invite les membres à continuer",
  "genre": "le genre de l'histoire (aventure, horreur comique, SF, etc.)"
}""",

    "defi": """Génère un défi de la semaine fun et réalisable pour des gens sur Discord.
Format JSON strict :
{
  "titre": "nom du défi",
  "description": "description du défi en 2 phrases",
  "comment_participer": "comment poster sa participation",
  "recompense": "ce que gagne le gagnant (fictif)"
}
Exemples : défi photo, défi créatif, défi connaissance..."""
}

async def generate_activity_content(activity_type: str, extra_context: str = "") -> dict:
    """Appelle l'API Gemini (gratuite) pour générer le contenu de l'activité."""
    base_prompt = PROMPTS.get(activity_type, PROMPTS["dilemme"])
    if extra_context:
        base_prompt += f"\n\nContexte supplémentaire : {extra_context}"

    full_prompt = (
        "Tu es un générateur de contenu fun pour Discord. "
        "Réponds UNIQUEMENT en JSON valide, sans aucun texte avant ou après, sans backticks markdown.\n\n"
        + base_prompt
    )

    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 1000
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            GEMINI_URL,
            headers=headers,
            params=params,
            json=payload
        ) as resp:
            data = await resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            # Nettoyer les backticks si l'IA en met
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
