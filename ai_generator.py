import os
import json
import random
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

PROMPTS = {
    "mais": """Génère un défi "X€ ou Y€ mais..." pour Discord francophone.
Format JSON strict :
{
  "montant_petit": "10€",
  "montant_grand": "200€",
  "mais": "la condition absurde/gênante/drôle",
  "contexte": "une phrase courte pour mettre en ambiance"
}
Le "mais" doit être créatif et drôle.""",

    "blindtest": """Génère un blind test textuel pour Discord francophone.
Format JSON strict :
{
  "paroles": "4-5 lignes de paroles caractéristiques (pas le refrain évident)",
  "titre": "titre exact",
  "artiste": "nom exact",
  "source": "film/série/jeu ou null",
  "annee": "année de sortie",
  "indice_bonus": "un indice sans révéler le titre"
}
Choisis des chansons variées et connues.""",

    "roi_indice": """Génère un indice pour deviner une personne mystère sur Discord.
Format JSON strict :
{
  "indice": "un indice amusant sur la personnalité/comportements, sans donner le nom"
}""",

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
  "option_a": "description complète de A",
  "option_b": "description complète de B",
  "twist": "détail absurde qui complique encore le choix"
}""",

    "deux_verites_mensonge_invite": """Génère un message d'invitation pour le jeu 2 vérités 1 mensonge.
Format JSON strict :
{
  "invitation": "message fun pour inviter les gens",
  "exemples": ["exemple de vérité", "exemple de mensonge drôle"]
}""",

    "recette": """Génère une liste d'ingrédients pour un jeu de recette impossible.
Format JSON strict :
{
  "titre_mystere": "nom mystérieux du plat",
  "ingredients": [
    {"nom": "ingrédient", "quantite": "200g", "niveau": "normal"},
    {"nom": "ingrédient bizarre", "quantite": "3 cuillères", "niveau": "wtf"},
    {"nom": "ingrédient impossible", "quantite": "au goût", "niveau": "impossible"}
  ],
  "contrainte": "contrainte de préparation absurde"
}""",

    "olympiade_epreuve": """Génère une épreuve pour les Olympiades Discord.
Format JSON strict :
{
  "nom": "nom de l'épreuve",
  "emoji": "emoji",
  "description": "description en 2 phrases",
  "comment_participer": "instruction pour /jouer",
  "critere_victoire": "comment les points sont attribués"
}""",

    "quiz_question": """Génère une question de quiz culture générale DIFFÉRENTE à chaque fois.
Format JSON strict :
{
  "question": "la question",
  "propositions": ["réponse A", "réponse B", "réponse C", "réponse D"],
  "bonne_reponse": 0,
  "anecdote": "fait fun sur la réponse"
}
IMPORTANT: mélange les propositions, indique l'index correct (0-3) dans bonne_reponse.""",

    "champion_question": """Génère une question de quiz UNIQUE et ORIGINALE sur le thème donné.
Format JSON strict :
{
  "question": "la question",
  "propositions": ["proposition A", "proposition B", "proposition C", "proposition D"],
  "bonne_reponse": 1,
  "niveau": "Facile/Moyen/Difficile",
  "anecdote": "anecdote fun"
}
IMPORTANT: sois créatif, ne répète jamais les mêmes questions. Mélange les propositions.""",
}

async def generate_activity_content(activity_type: str, extra_context: str = "") -> dict:
    prompt = PROMPTS.get(activity_type, PROMPTS["dilemme"])
    if extra_context:
        prompt += f"\n\nThème/Contexte spécifique : {extra_context}"

    # Seed aléatoire pour forcer la variété
    seed = random.randint(1000, 99999)
    full_prompt = (
        f"[Variation #{seed}] Tu es un générateur de contenu fun pour Discord francophone. "
        "Réponds UNIQUEMENT en JSON valide, sans texte avant/après, sans backticks markdown.\n\n"
        + prompt
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=full_prompt,
    )

    text = response.text.strip()
    print(f"[GEMINI RAW] {repr(text[:300])}")

    # Nettoyage
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            p = part.strip().lstrip("json").strip()
            if p.startswith("{"):
                text = p
                break

    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]

    print(f"[GEMINI CLEAN] {repr(text[:200])}")
    return json.loads(text)
