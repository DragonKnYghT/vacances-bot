import os
import json
import random
from google import genai

# ──────────────────────────────────────────
#  ROTATION AUTOMATIQUE DES CLÉS GEMINI
#  Dans Render, ajoute : GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.
# ──────────────────────────────────────────

def get_api_keys():
    keys = []
    for i in range(1, 11):
        k = os.getenv(f"GEMINI_API_KEY_{i}")
        if k:
            keys.append(k)
    if not keys:
        k = os.getenv("GEMINI_API_KEY")
        if k:
            keys.append(k)
    return keys

API_KEYS = get_api_keys()
current_key_index = [0]

def rotate_key():
    current_key_index[0] = (current_key_index[0] + 1) % len(API_KEYS)
    print(f"[GEMINI] Rotation → clé {current_key_index[0] + 1}/{len(API_KEYS)}")

PROMPTS = {
    "mais": """Génère un défi "X€ ou Y€ mais..." ORIGINAL et DIFFÉRENT pour Discord francophone.
Format JSON strict :
{
  "montant_petit": "10€",
  "montant_grand": "200€",
  "mais": "la condition absurde/gênante/drôle",
  "contexte": "une phrase courte pour mettre en ambiance"
}""",

    "blindtest": """Génère un blind test textuel VARIÉ pour Discord francophone.
Format JSON strict :
{
  "paroles": "4-5 lignes de paroles caractéristiques (pas le refrain évident)",
  "titre": "titre exact",
  "artiste": "nom exact",
  "source": "film/série/jeu ou null",
  "annee": "année de sortie",
  "indice_bonus": "un indice sans révéler le titre"
}
Choisis des chansons très variées : genres différents, époques différentes.""",

    "roi_indice": """Génère un indice pour deviner une personne mystère sur Discord.
Format JSON strict :
{
  "indice": "un indice amusant sur la personnalité/comportements, sans donner le nom"
}""",

    "sondage_absurde": """Génère un sondage absurde et fun ORIGINAL pour Discord avec 4 options.
Format JSON strict :
{
  "question": "question absurde et originale",
  "options": ["option 1", "option 2", "option 3", "option 4"],
  "emojis": ["🔴", "🟡", "🟢", "🔵"]
}""",

    "dilemme": """Génère un dilemme impossible ORIGINAL et CRÉATIF pour Discord francophone.
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

    "recette": """Génère une liste d'ingrédients ORIGINALE pour un jeu de recette impossible.
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

    "olympiade_epreuve": """Génère une épreuve ORIGINALE pour les Olympiades Discord.
Format JSON strict :
{
  "nom": "nom de l'épreuve",
  "emoji": "emoji",
  "description": "description en 2 phrases",
  "comment_participer": "instruction pour /jouer",
  "critere_victoire": "comment les points sont attribués"
}""",

    "quiz_question": """Génère une question de quiz culture générale UNIQUE et ORIGINALE.
Format JSON strict :
{
  "question": "la question",
  "propositions": ["réponse A", "réponse B", "réponse C", "réponse D"],
  "bonne_reponse": 0,
  "anecdote": "fait fun sur la réponse"
}
Mélange les propositions, indique l'index correct (0-3) dans bonne_reponse.""",

    "champion_question": """Génère une question de quiz UNIQUE et DIFFÉRENTE sur le thème donné en contexte.
IMPORTANT : Des questions ont déjà été posées dans ce contexte — génère une question COMPLÈTEMENT DIFFÉRENTE.
Format JSON strict :
{
  "question": "la question",
  "propositions": ["proposition A", "proposition B", "proposition C", "proposition D"],
  "bonne_reponse": 1,
  "niveau": "Facile/Moyen/Difficile",
  "anecdote": "anecdote fun"
}
Sois créatif, change d'angle, de sous-thème, de difficulté. Mélange les propositions.""",
}

async def generate_activity_content(activity_type: str, extra_context: str = "", previous_questions: list = None) -> dict:
    prompt = PROMPTS.get(activity_type, PROMPTS["dilemme"])
    if extra_context:
        prompt += f"\n\nThème/Contexte : {extra_context}"
    if previous_questions:
        prompt += f"\n\nQuestions déjà posées (NE PAS répéter) :\n" + "\n".join(f"- {q}" for q in previous_questions)

    seed = random.randint(10000, 99999)
    full_prompt = (
        f"[#{seed}] Tu es un générateur de contenu fun pour Discord francophone. "
        "Réponds UNIQUEMENT en JSON valide, sans texte avant/après, sans backticks.\n\n"
        + prompt
    )

    if not API_KEYS:
        raise Exception("Aucune clé GEMINI_API_KEY configurée dans les variables d'environnement !")

    last_error = None
    for attempt in range(len(API_KEYS)):
        try:
            client = genai.Client(api_key=API_KEYS[current_key_index[0]])
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=full_prompt,
            )
            text = response.text.strip()
            print(f"[GEMINI OK] Clé {current_key_index[0]+1} — {repr(text[:100])}")

            # Nettoyage JSON
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

            return json.loads(text)

        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower() or "RESOURCE_EXHAUSTED" in err:
                print(f"[GEMINI] Clé {current_key_index[0]+1} quota épuisé, rotation...")
                rotate_key()
                last_error = e
            else:
                raise e

    raise Exception(f"Toutes les clés Gemini sont épuisées ! Dernière erreur : {last_error}")
