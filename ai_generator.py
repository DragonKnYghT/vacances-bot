import aiohttp
import os
import json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

PROMPTS = {
    "mais": """Génère un défi "X€ ou Y€ mais..." pour Discord francophone.
Format JSON strict :
{
  "montant_petit": "10€",
  "montant_grand": "200€",
  "mais": "la condition absurde/gênante/drôle",
  "contexte": "une phrase courte pour mettre en ambiance"
}
Le "mais" doit être créatif : humiliant, drôle, bizarre. Ex: "tu dois envoyer un vocal de toi qui chante faux chaque matin pendant une semaine".""",

    "blindtest": """Génère un blind test textuel pour Discord francophone.
Format JSON strict :
{
  "paroles": "4-5 lignes de paroles caractéristiques de la chanson (pas le refrain évident)",
  "titre": "titre exact de la chanson",
  "artiste": "nom exact de l'artiste",
  "source": "film/série/jeu d'où vient la chanson, ou null si aucune",
  "annee": "année de sortie",
  "indice_bonus": "un indice supplémentaire sans révéler le titre"
}
Choisis des chansons variées : pop fr, rap fr, variété, années 80-2020s, BO de films connus.""",

    "roi_indice": """Génère un indice pour deviner une personne mystère sur Discord.
Format JSON strict :
{
  "indice": "un indice vague sur la personnalité/comportements de la personne mystère, sans donner son nom"
}
L'indice doit être amusant et progressivement plus précis selon le numéro d'indice donné en contexte.""",

    "sondage_absurde": """Génère un sondage absurde et fun pour Discord avec 4 options.
Format JSON strict :
{
  "question": "question absurde et originale",
  "options": ["option 1", "option 2", "option 3", "option 4"],
  "emojis": ["🔴", "🟡", "🟢", "🔵"]
}""",

    "dilemme": """Génère un dilemme impossible drôle pour Discord francophone.
Format JSON strict :
{
  "question": "Tu dois choisir entre [A] OU [B] ?",
  "option_a": "description complète de A avec conséquences",
  "option_b": "description complète de B avec conséquences",
  "twist": "un détail absurde qui complique encore plus le choix"
}""",

    "deux_verites_mensonge_invite": """Génère un message pour inviter les membres à soumettre leurs 2 vérités 1 mensonge.
Format JSON strict :
{
  "invitation": "message fun pour inviter les gens à participer",
  "exemples": ["exemple de vérité", "exemple de mensonge drôle"]
}""",

    "recette": """Génère une liste d'ingrédients pour un jeu de recette impossible sur Discord.
Format JSON strict :
{
  "titre_mystere": "nom mystérieux du plat final",
  "ingredients": [
    {"nom": "ingrédient classique", "quantite": "200g", "niveau": "normal"},
    {"nom": "ingrédient bizarre", "quantite": "3 cuillères", "niveau": "wtf"},
    {"nom": "ingrédient normal", "quantite": "1 pincée", "niveau": "normal"},
    {"nom": "ingrédient impossible", "quantite": "au goût", "niveau": "impossible"},
    {"nom": "ingrédient drôle", "quantite": "à volonté", "niveau": "wtf"}
  ],
  "contrainte": "une contrainte de préparation absurde"
}
Mélange des ingrédients normaux et complètement fous.""",

    "olympiade_epreuve": """Génère une épreuve pour les Olympiades Discord.
Format JSON strict :
{
  "nom": "nom de l'épreuve",
  "emoji": "emoji représentatif",
  "description": "description de l'épreuve en 2 phrases",
  "comment_participer": "instruction précise pour participer avec /jouer",
  "critere_victoire": "comment les points seront attribués"
}
Exemples : épreuve de rapidité à répondre, épreuve créative, épreuve de connaissance...""",

    "quiz_question": """Génère une question de quiz culture générale avec 4 propositions.
Format JSON strict :
{
  "question": "la question",
  "propositions": ["réponse A", "réponse B", "réponse C", "réponse D"],
  "bonne_reponse": 0,
  "anecdote": "fait fun sur la réponse"
}
Mélange les propositions aléatoirement et indique l'index correct (0-3) dans bonne_reponse.""",

    "champion_question": """Génère une question style quiz avec 4 propositions.
Format JSON strict :
{
  "question": "la question",
  "propositions": ["proposition A", "proposition B", "proposition C", "proposition D"],
  "bonne_reponse": 1,
  "niveau": "Facile/Moyen/Difficile",
  "anecdote": "anecdote fun"
}
Mélange les propositions aléatoirement.""",
}

async def generate_activity_content(activity_type: str, extra_context: str = "") -> dict:
    prompt = PROMPTS.get(activity_type, PROMPTS["dilemme"])
    if extra_context:
        prompt += f"\n\nContexte : {extra_context}"

    full_prompt = (
        "Tu es un générateur de contenu fun pour serveur Discord francophone. "
        "Réponds UNIQUEMENT en JSON valide, sans texte avant/après, sans backticks.\n\n"
        + prompt
    )

    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {"temperature": 0.9, "maxOutputTokens": 1000}
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(GEMINI_URL, headers=headers, params=params, json=payload) as resp:
            data = await resp.json()
            if "candidates" not in data:
                raise Exception(f"Gemini error: {data}")
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if "```" in text:
                parts = text.split("```")
                text = parts[1] if len(parts) > 1 else parts[0]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
