# Guide de déploiement — Site Web

## Structure dans ton repo `vacances-bot`

```
vacances-bot/
├── bot.py
├── server.py
├── activities.py
├── minigames.py
├── data_manager.py
├── ai_generator.py
├── requirements.txt        ← celui du bot
├── Procfile                ← celui du bot
└── web/                    ← tout ce dossier est nouveau
    ├── app.py              ← backend Flask
    ├── requirements.txt    ← dépendances Flask
    ├── Procfile            ← pour Render
    ├── DEPLOY.md           ← ce fichier
    ├── index.html
    ├── callback.html
    ├── profile.html
    ├── shop.html
    ├── leaderboard.html
    ├── skilltree.html      ← à venir
    ├── pixelmap.html       ← à venir
    └── static/
        ├── css/global.css
        └── js/
            ├── api.js
            └── ui.js
```

---

## 1. Discord Developer Portal

1. Va sur https://discord.com/developers/applications
2. Sélectionne ton application (ou crée-en une nouvelle)
3. Dans **OAuth2 → General** :
   - Ajoute un Redirect URI : `https://TON_BACKEND.onrender.com/auth/callback`
4. Récupère le **Client ID** et le **Client Secret**

---

## 2. Backend Flask sur Render

### Créer un nouveau Web Service sur Render

- **Repo** : ton repo `vacances-bot`
- **Root Directory** : `web`   ← important !
- **Runtime** : Python
- **Build Command** : `pip install -r requirements.txt`
- **Start Command** : `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`

### Variables d'environnement à configurer sur Render

| Variable              | Valeur                                              |
|-----------------------|-----------------------------------------------------|
| `MONGO_URI`           | Ton URI MongoDB Atlas (le même que le bot)         |
| `DISCORD_CLIENT_ID`   | L'ID de ton app Discord                            |
| `DISCORD_CLIENT_SECRET` | Le secret de ton app Discord                    |
| `DISCORD_REDIRECT_URI` | `https://TON_BACKEND.onrender.com/auth/callback` |
| `FLASK_SECRET_KEY`    | Une chaîne aléatoire longue (ex: générée avec `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `JWT_SECRET`          | Une autre chaîne aléatoire longue                  |
| `SITE_URL`            | `https://TON_USERNAME.github.io/vacances-bot/web`  |

---

## 3. GitHub Pages

1. Dans les settings du repo GitHub → **Pages**
2. Source : `Deploy from a branch`
3. Branch : `main`, Folder : `/ (root)` ou `/web` selon ton setup
   - Si tu choisis `/ (root)`, le site sera à `https://TON_USERNAME.github.io/vacances-bot/web/`
   - Si tu veux un repo séparé, copie juste le dossier `web/` dans un repo `TON_USERNAME.github.io`

---

## 4. Mettre à jour les URLs dans le code

Une fois les deux services déployés, mets à jour :

**`web/static/js/api.js`** ligne 7 :
```js
const API_BASE = "https://TON_BACKEND.onrender.com";
```

**`web/app.py`** ligne dans CORS :
```python
"https://TON_USERNAME.github.io",
```

**`web/app.py`** dans `auth_callback` :
```python
site_url = os.environ.get("SITE_URL", "https://TON_USERNAME.github.io/vacances-bot/web")
```

---

## 5. Vérifier la collection `pixels` dans MongoDB

Le backend va créer automatiquement la collection `pixels` au premier pixel posé.
Si tu veux la créer manuellement avec un index pour les performances :

```js
// Dans MongoDB Atlas → Browse Collections → Add Collection
db.pixels.createIndex({ world: 1, x: 1, y: 1 }, { unique: true })
```

---

## 6. Pages à venir (prochaines étapes)

- `skilltree.html` — Arbre de compétences visuel interactif (SVG)
- `pixelmap.html` — Grille 100×100 pixels collaborative (Canvas)
