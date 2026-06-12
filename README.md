# 🎮 Bot Vacances Discord

Bot Discord qui anime ton serveur pendant tes vacances avec 8 semaines d'activités générées par l'IA.

## ✨ Fonctionnalités

- 🤖 **Contenu généré par IA** — chaque activité est unique, créée par Claude
- ⏰ **Automatique** — envoi à 10h00 chaque jour, changement de semaine tout seul
- 📊 **Score fictif** — récap hebdo + récap final → tu sais quoi donner sur DraftBot
- 🔐 **Sécurisé** — token et clés jamais sur GitHub

## 🗓️ Planning des 8 semaines

| Semaine | Activité | Description |
|---------|----------|-------------|
| 1 | 🤔 Dilemme Impossible | Vote A ou B sur des dilemmes absurdes |
| 2 | 📰 Fake News du Jour | Fausse info humoristique générée par l'IA |
| 3 | 📊 Sondage Absurde | Sondages complètement fous |
| 4 | 🧠 Quiz Culture | Question de culture générale |
| 5 | 🤥 2 Vérités 1 Mensonge | Trouve le mensonge ! |
| 6 | ❓ Ce Que Tu Préfères | A ou B ? |
| 7 | ✍️ Histoire Collaborative | Continue l'histoire avec /jouer |
| 8 | 🗺️ GeoGuessr Textuel | Trouve le lieu grâce aux indices |

> **Modifie l'ordre dans `activities.py`** une fois que tu as les résultats de tes votes !

## 🚀 Installation

### 1. Cloner le repo
```bash
git clone https://github.com/TON_PSEUDO/TON_REPO.git
cd TON_REPO
pip install -r requirements.txt
```

### 2. Configurer les clés secrètes
```bash
cp .env.example .env
```
Remplis `.env` avec :
- `DISCORD_TOKEN` → sur [discord.com/developers/applications](https://discord.com/developers/applications)
- `CHANNEL_ID` → clic droit sur ton salon Discord > "Copier l'identifiant"
- `ANTHROPIC_API_KEY` → sur [console.anthropic.com](https://console.anthropic.com)

### 3. Lancer localement
```bash
python bot.py
```

## ☁️ Déploiement sur Railway (gratuit)

1. Va sur [railway.app](https://railway.app) et connecte ton GitHub
2. "New Project" → "Deploy from GitHub repo"
3. Dans **Variables**, ajoute :
   - `DISCORD_TOKEN`
   - `CHANNEL_ID`
   - `ANTHROPIC_API_KEY`
4. Railway détecte le `Procfile` et lance le bot automatiquement ✅

## 🎮 Commandes

| Commande | Description |
|----------|-------------|
| `/jouer [réponse]` | Participer à l'activité du jour |
| `/score` | Voir ton score fictif et estimation DraftBot |
| `/classement` | Top 10 de la semaine |
| `/semaine` | Infos sur la semaine en cours |

## 🔐 Sécurité GitHub

Le fichier `.gitignore` protège automatiquement :
- `.env` (tes tokens secrets)
- `data.json` (données des joueurs)
- `recap_final.json` (récap DraftBot)

**Ne jamais pusher `.env` sur GitHub !**

## 💰 Système de score → DraftBot

- Chaque participation donne des points aléatoires (légère tendance positive)
- Récap hebdomadaire chaque dimanche
- À la fin des 8 semaines → `recap_final.json` te dit exactement quoi donner/retirer sur DraftBot

## ⚙️ Personnalisation

- **Changer l'heure** : modifie `now.hour == 10` dans `bot.py`
- **Changer les activités** : édite `ACTIVITIES_SCHEDULE` dans `activities.py`
- **Changer les points** : modifie `get_random_points()` dans `data_manager.py`
- **Ratio points→DraftBot** : modifie `POINTS_TO_DRAFTBOT` dans `data_manager.py`
