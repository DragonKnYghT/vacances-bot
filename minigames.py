"""
Mini-jeux permanents accessibles via /menu
- 🎰 Machine à sous (solo)
- 🧠 Question pour un champion (solo/duo/coop/versus)
- 💰 Qui veut gagner des pièces (solo, 4 boutons)
- 🔴 Puissance 4 (duo)
- 🌐 Site web (bouton esthétique vide)
"""
import discord
from discord import app_commands
import random
import uuid
import asyncio
from ai_generator import generate_activity_content
from data_manager import DataManager

db = DataManager()

THEMES_CHAMPION = [
    "Culture générale", "Histoire", "Science", "Sport",
    "Cinéma", "Musique", "Géographie", "Cuisine",
    "Animaux", "Technologies", "Célébrités", "Art"
]

# ──────────────────────────────────────────
#  MACHINE À SOUS
# ──────────────────────────────────────────

SYMBOLES = ["🍒", "🍋", "🍊", "🍇", "⭐", "7️⃣", "💎", "🟢"]
GAINS_TRIPLE = {
    "🟢": 200, "💎": 150, "7️⃣": 120, "⭐": 100,
    "🍇": 50, "🍊": 40, "🍋": 30, "🍒": 20
}

def calcule_gain(rouleaux):
    a, b, c = rouleaux
    if a == b == c:
        gain = GAINS_TRIPLE.get(a, 20)
        return gain - 10, f"TRIPLE {a} ! +{gain} pts brut 🎉"
    if a == b or b == c or a == c:
        s = a if a == b else (b if b == c else a)
        return 5, f"Double {s} ! +5 pts 🎲"
    return -10, "Rien... -10 pts 😢"

async def jouer_machine(interaction: discord.Interaction, parties: list):
    rouleaux = [random.choice(SYMBOLES) for _ in range(3)]
    gain, desc = calcule_gain(rouleaux)
    parties[0] += 1
    result = db.add_points(str(interaction.user.id), gain)
    sign = "+" if gain >= 0 else ""
    embed = discord.Embed(
        title="🎰 Machine à Sous",
        description=f"## {rouleaux[0]}  {rouleaux[1]}  {rouleaux[2]}\n**{desc}**",
        color=0x2ecc71 if gain >= 0 else 0xe74c3c
    )
    embed.add_field(name="Résultat", value=f"{sign}{gain} pts", inline=True)
    embed.add_field(name="Total", value=f"{result['total']} pts fictifs", inline=True)
    embed.set_footer(text=f"Parties : {parties[0]} | 2 symboles = +5 pts | 3 symboles = jackpot !")
    return embed

# ──────────────────────────────────────────
#  PUISSANCE 4
# ──────────────────────────────────────────

class P4Game:
    ROWS, COLS = 6, 7
    EMPTY, P1, P2 = "⬛", "🔴", "🟡"

    def __init__(self, p1, p2):
        self.board = [[self.EMPTY]*self.COLS for _ in range(self.ROWS)]
        self.p1, self.p2 = p1, p2
        self.current = 1
        self.winner = None
        self.moves = 0

    def drop(self, col):
        for r in range(self.ROWS-1, -1, -1):
            if self.board[r][col] == self.EMPTY:
                self.board[r][col] = self.P1 if self.current == 1 else self.P2
                self.moves += 1
                self._check(r, col)
                return True
        return False

    def _check(self, row, col):
        piece = self.board[row][col]
        for dr, dc in [(0,1),(1,0),(1,1),(1,-1)]:
            n = 1
            for d in [1,-1]:
                r, c = row+dr*d, col+dc*d
                while 0<=r<self.ROWS and 0<=c<self.COLS and self.board[r][c]==piece:
                    n += 1; r+=dr*d; c+=dc*d
            if n >= 4:
                self.winner = self.current; return

    def bot_move(self):
        cols = [c for c in range(self.COLS) if self.board[0][c]==self.EMPTY]
        if cols:
            self.current = 2
            self.drop(random.choice(cols))
            self.current = 1

    def next_turn(self):
        self.current = 2 if self.current == 1 else 1

    def is_over(self):
        return self.winner is not None or self.moves >= self.ROWS*self.COLS

    def embed(self):
        nums = "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣"
        board = "\n".join("".join(r) for r in self.board) + "\n" + nums
        p2n = self.p2.display_name if self.p2 else "🤖 Bot"
        if self.winner:
            wn = self.p1.display_name if self.winner==1 else p2n
            title, color = f"🏆 {wn} a gagné !", 0x2ecc71
        elif self.moves >= self.ROWS*self.COLS:
            title, color = "🤝 Match nul !", 0x95a5a6
        else:
            tn = self.p1.display_name if self.current==1 else p2n
            tp = self.P1 if self.current==1 else self.P2
            title, color = f"{tp} Tour de {tn}", 0x3498db
        e = discord.Embed(title=title, description=board, color=color)
        e.set_footer(text=f"🔴 {self.p1.display_name} vs 🟡 {p2n}")
        return e

# ──────────────────────────────────────────
#  COMMANDES SLASH DIRECTES (plus de Views complexes)
# ──────────────────────────────────────────

def setup_menu_command(tree, bot):

    # Stockage en mémoire des parties et états actifs
    machines_parties = {}   # user_id -> [nb_parties]
    p4_games = {}           # channel_id -> P4Game
    p4_challenges = {}      # channel_id -> challenger_user
    quiz_data = {}          # user_id -> content dict

    @tree.command(name="menu", description="🎮 Voir tous les mini-jeux disponibles")
    async def menu(interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 Menu des Mini-Jeux",
            description=(
                "Utilise les commandes ci-dessous pour jouer !\n\n"
                "🎰 `/slot` — Machine à sous\n"
                "🧠 `/champion <thème> <mode>` — Question pour un Champion\n"
                "💰 `/quiz` — Qui veut gagner des pièces ?\n"
                "🔴 `/p4` — Puissance 4 (solo vs bot)\n"
                "⚔️ `/p4defi` — Défier quelqu'un au Puissance 4\n"
                "✅ `/p4accept` — Accepter un défi Puissance 4\n"
                "🌐 `/site` — Site web (bientôt)"
            ),
            color=0x7289da
        )
        embed.set_footer(text="Points fictifs → pièces DraftBot à la fin des vacances !")
        await interaction.response.send_message(embed=embed)

    @tree.command(name="slot", description="🎰 Jouer à la machine à sous")
    async def slot(interaction: discord.Interaction):
        uid = interaction.user.id
        if uid not in machines_parties:
            machines_parties[uid] = [0]
        embed = await jouer_machine(interaction, machines_parties[uid])
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="quiz", description="💰 Qui veut gagner des pièces ? (quiz 4 choix)")
    async def quiz(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            content = await generate_activity_content("quiz_question")
            quiz_data[interaction.user.id] = content
            props = content.get("propositions", [])
            bonne = content.get("bonne_reponse", 0)
            lettres = ["A", "B", "C", "D"]
            embed = discord.Embed(
                title="💰 Qui veut gagner des pièces ?",
                description=f"## {content['question']}",
                color=0xf1c40f
            )
            for i, p in enumerate(props):
                embed.add_field(name=f"{lettres[i]}.", value=p, inline=True)
            embed.set_footer(text="Réponds avec /repondre A, B, C ou D")
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur : {e}", ephemeral=True)

    @tree.command(name="repondre", description="💰 Répondre au quiz en cours")
    @app_commands.describe(choix="Ta réponse : A, B, C ou D")
    @app_commands.choices(choix=[
        app_commands.Choice(name="A", value="0"),
        app_commands.Choice(name="B", value="1"),
        app_commands.Choice(name="C", value="2"),
        app_commands.Choice(name="D", value="3"),
    ])
    async def repondre(interaction: discord.Interaction, choix: app_commands.Choice[str]):
        uid = interaction.user.id
        content = quiz_data.get(uid)
        if not content:
            await interaction.response.send_message("❌ Lance d'abord `/quiz` !", ephemeral=True)
            return
        del quiz_data[uid]
        index = int(choix.value)
        bonne = content.get("bonne_reponse", 0)
        est_bonne = index == bonne
        pts = 20 if est_bonne else -5
        result = db.add_points(str(uid), pts)
        bonne_rep = content["propositions"][bonne]
        anecdote = content.get("anecdote", "")
        sign = "+" if pts >= 0 else ""
        if est_bonne:
            msg = f"✅ **Bonne réponse !** {sign}{pts} pts\n📚 {anecdote}"
        else:
            msg = f"❌ **Raté !** C'était : **{bonne_rep}**\n{sign}{pts} pts\n📚 {anecdote}"
        await interaction.response.send_message(f"{msg}\n💰 Total : {result['total']} pts", ephemeral=True)

    @tree.command(name="champion", description="🧠 Question pour un Champion")
    @app_commands.describe(theme="Le thème de la question", mode="solo, versus ou coop")
    @app_commands.choices(
        theme=[app_commands.Choice(name=t, value=t) for t in THEMES_CHAMPION],
        mode=[
            app_commands.Choice(name="🎯 Solo (privé)", value="solo"),
            app_commands.Choice(name="⚔️ Versus (public, 1er gagne bonus)", value="versus"),
            app_commands.Choice(name="🤝 Coop (public, tout le monde joue)", value="coop"),
        ]
    )
    async def champion(interaction: discord.Interaction, theme: app_commands.Choice[str], mode: app_commands.Choice[str]):
        is_public = mode.value in ("versus", "coop")
        await interaction.response.defer(ephemeral=not is_public)
        try:
            content = await generate_activity_content("champion_question", theme.value)
            content["theme"] = theme.value
            props = content.get("propositions", [])
            bonne = content.get("bonne_reponse", 0)
            lettres = ["A", "B", "C", "D"]
            mode_labels = {"solo": "Solo 🎯", "versus": "Versus ⚔️", "coop": "Coop 🤝"}
            embed = discord.Embed(
                title=f"🧠 Question pour un Champion — {mode_labels[mode.value]}",
                description=f"## {content['question']}",
                color=0x3498db
            )
            embed.add_field(name="Niveau", value=content.get("niveau","?"), inline=True)
            embed.add_field(name="Thème", value=theme.value, inline=True)
            for i, p in enumerate(props):
                embed.add_field(name=f"{lettres[i]}.", value=p, inline=True)

            if mode.value == "solo":
                embed.set_footer(text=f"Réponds avec /champion_rep {' / '.join(lettres[:len(props)])}")
            else:
                embed.set_footer(text=f"Réponds avec /champion_rep A, B, C ou D !")

            # Stocker la question avec mode
            game_id = f"{interaction.channel_id}_{uuid.uuid4().hex[:6]}"
            quiz_data[f"champ_{interaction.user.id}"] = {
                "content": content, "mode": mode.value,
                "auteur": interaction.user.id, "repondu": set(),
                "premier": None, "game_id": game_id
            }
            await interaction.followup.send(embed=embed, ephemeral=not is_public)
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur : {e}", ephemeral=True)

    @tree.command(name="champion_rep", description="🧠 Répondre à la question Champion en cours")
    @app_commands.describe(choix="Ta réponse : A, B, C ou D")
    @app_commands.choices(choix=[
        app_commands.Choice(name="A", value="0"),
        app_commands.Choice(name="B", value="1"),
        app_commands.Choice(name="C", value="2"),
        app_commands.Choice(name="D", value="3"),
    ])
    async def champion_rep(interaction: discord.Interaction, choix: app_commands.Choice[str]):
        uid = str(interaction.user.id)
        # Cherche une question active (solo = la sienne, versus/coop = n'importe laquelle dans le salon)
        game_key = None
        game = None
        # Solo : cherche sa propre question
        k = f"champ_{interaction.user.id}"
        if k in quiz_data:
            game_key, game = k, quiz_data[k]
        else:
            # Versus/Coop : cherche une question publique dans ce salon
            for key, val in quiz_data.items():
                if key.startswith("champ_") and val["mode"] in ("versus","coop"):
                    game_key, game = key, val
                    break

        if not game:
            await interaction.response.send_message("❌ Aucune question active ! Lance `/champion` d'abord.", ephemeral=True)
            return

        if uid in game["repondu"]:
            await interaction.response.send_message("Tu as déjà répondu !", ephemeral=True)
            return

        game["repondu"].add(uid)
        index = int(choix.value)
        content = game["content"]
        bonne = content.get("bonne_reponse", 0)
        est_bonne = index == bonne
        est_premier = game["premier"] is None and est_bonne
        if est_premier:
            game["premier"] = uid

        mode = game["mode"]
        if mode == "versus":
            pts = 30 if (est_bonne and est_premier) else (10 if est_bonne else -5)
        elif mode == "coop":
            pts = 20 if est_bonne else 0
        else:
            pts = 30 if est_bonne else -5
            del quiz_data[game_key]  # solo : une seule réponse

        result = db.add_points(uid, pts)
        bonne_rep = content["propositions"][bonne]
        anecdote = content.get("anecdote","")
        sign = "+" if pts >= 0 else ""

        if est_bonne:
            msg = f"✅ **Bonne réponse !** {sign}{pts} pts"
            if est_premier and mode == "versus":
                msg += " 🏆 Premier !"
            msg += f"\n📚 {anecdote}"
        else:
            msg = f"❌ **Raté !** C'était : **{bonne_rep}**\n{sign}{pts} pts"
            if mode != "coop":
                msg += f"\n📚 {anecdote}"

        await interaction.response.send_message(f"{msg}\n💰 Total : {result['total']} pts", ephemeral=True)

    @tree.command(name="p4", description="🔴 Jouer au Puissance 4 contre le bot")
    async def p4(interaction: discord.Interaction):
        cid = interaction.channel_id
        if cid in p4_games and not p4_games[cid].is_over():
            await interaction.response.send_message("Une partie est déjà en cours dans ce salon ! Termine-la d'abord.", ephemeral=True)
            return
        game = P4Game(interaction.user, None)
        p4_games[cid] = game
        embed = game.embed()
        embed.set_footer(text="Joue avec /p4col 1-7 pour placer ton pion !")
        await interaction.response.send_message(embed=embed)

    @tree.command(name="p4defi", description="⚔️ Défier quelqu'un au Puissance 4")
    async def p4defi(interaction: discord.Interaction):
        cid = interaction.channel_id
        if cid in p4_challenges:
            await interaction.response.send_message("Il y a déjà un défi en attente dans ce salon !", ephemeral=True)
            return
        p4_challenges[cid] = interaction.user
        embed = discord.Embed(
            title="⚔️ Défi Puissance 4 !",
            description=f"**{interaction.user.display_name}** lance un défi !\nUtilise `/p4accept` pour accepter !",
            color=0xe74c3c
        )
        await interaction.response.send_message(embed=embed)

    @tree.command(name="p4accept", description="✅ Accepter le défi Puissance 4 en cours")
    async def p4accept(interaction: discord.Interaction):
        cid = interaction.channel_id
        challenger = p4_challenges.get(cid)
        if not challenger:
            await interaction.response.send_message("Aucun défi en attente dans ce salon !", ephemeral=True)
            return
        if interaction.user.id == challenger.id:
            await interaction.response.send_message("Tu ne peux pas accepter ton propre défi !", ephemeral=True)
            return
        del p4_challenges[cid]
        game = P4Game(challenger, interaction.user)
        p4_games[cid] = game
        embed = game.embed()
        embed.set_footer(text="Jouez avec /p4col 1-7 pour placer vos pions !")
        await interaction.response.send_message(embed=embed)

    @tree.command(name="p4col", description="🔴 Placer un pion dans la colonne choisie")
    @app_commands.describe(colonne="Numéro de colonne (1 à 7)")
    @app_commands.choices(colonne=[app_commands.Choice(name=str(i), value=i) for i in range(1,8)])
    async def p4col(interaction: discord.Interaction, colonne: app_commands.Choice[int]):
        cid = interaction.channel_id
        game = p4_games.get(cid)
        if not game or game.is_over():
            await interaction.response.send_message("Aucune partie en cours ! Lance `/p4` ou `/p4accept`.", ephemeral=True)
            return
        uid = interaction.user.id
        if game.current == 1 and uid != game.p1.id:
            await interaction.response.send_message(f"Ce n'est pas ton tour ! C'est au tour de 🔴 {game.p1.display_name}", ephemeral=True)
            return
        if game.current == 2 and game.p2 and uid != game.p2.id:
            await interaction.response.send_message(f"Ce n'est pas ton tour ! C'est au tour de 🟡 {game.p2.display_name}", ephemeral=True)
            return

        col = colonne.value - 1
        if not game.drop(col):
            await interaction.response.send_message("Colonne pleine ! Choisis une autre.", ephemeral=True)
            return

        if not game.p2 and not game.is_over():
            game.bot_move()
        elif game.p2 and not game.is_over():
            game.next_turn()

        if game.is_over():
            if game.winner == 1:
                db.add_points(str(game.p1.id), 25)
            elif game.winner == 2 and game.p2:
                db.add_points(str(game.p2.id), 25)
            del p4_games[cid]

        embed = game.embed()
        if not game.is_over():
            embed.set_footer(text="Jouez avec /p4col 1-7 !")
        await interaction.response.send_message(embed=embed)

    @tree.command(name="site", description="🌐 Accéder au site web")
    async def site(interaction: discord.Interaction):
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="🌐 Ouvrir le site",
            url="https://DragonKnYghT.github.io/vacances-bot/web/index.html",
            style=discord.ButtonStyle.link
        ))
        await interaction.response.send_message(
            "🏰 **Serveur Vacances — Site Web**\nConsulte tes points, la boutique, le skill tree et la pixel map !",
            view=view,
            ephemeral=True
        )
