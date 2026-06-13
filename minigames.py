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
#  VUE PRINCIPALE — /menu
# ──────────────────────────────────────────

class MenuPrincipal(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="🎰 Machine à sous", style=discord.ButtonStyle.green)
    async def machine_sous(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = MachineASous(interaction.user)
        embed = discord.Embed(
            title="🎰 Machine à Sous",
            description="Mise : **10 pts fictifs**\nClique sur **Jouer** pour lancer les rouleaux !",
            color=0xf1c40f
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="🧠 Question pour un Champion", style=discord.ButtonStyle.blurple)
    async def question_champion(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ChoisirThemeChampion(interaction.user)
        embed = discord.Embed(
            title="🧠 Question pour un Champion",
            description="Choisis un mode de jeu !",
            color=0x3498db
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="💰 Qui veut gagner des pièces ?", style=discord.ButtonStyle.blurple)
    async def qui_veut_gagner(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            content = await generate_activity_content("quiz_question")
            view = QuizQuatreChoix(interaction.user, content)
            embed = discord.Embed(
                title="💰 Qui veut gagner des pièces ?",
                description=f"## {content['question']}",
                color=0xf1c40f
            )
            embed.set_footer(text="Bonne réponse = +20 pts fictifs | Mauvaise = -5 pts")
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur : {e}", ephemeral=True)

    @discord.ui.button(label="🔴 Puissance 4", style=discord.ButtonStyle.red)
    async def puissance4(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = DemanderAdversaire(interaction.user, "p4")
        embed = discord.Embed(
            title="🔴 Puissance 4",
            description="Mentionne ton adversaire pour commencer !",
            color=0xe74c3c
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

    @discord.ui.button(label="🌐 Site Web", style=discord.ButtonStyle.grey, disabled=True)
    async def site_web(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚧 Bientôt disponible !", ephemeral=True)


# ──────────────────────────────────────────
#  MACHINE À SOUS
# ──────────────────────────────────────────

SYMBOLES = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣", "⭐"]
GAINS = {
    ("💎", "💎", "💎"): 200,
    ("7️⃣", "7️⃣", "7️⃣"): 150,
    ("⭐", "⭐", "⭐"): 100,
    ("🍇", "🍇", "🍇"): 50,
    ("🍊", "🍊", "🍊"): 40,
    ("🍋", "🍋", "🍋"): 30,
    ("🍒", "🍒", "🍒"): 20,
}

class MachineASous(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user

    @discord.ui.button(label="🎰 Jouer (-10 pts)", style=discord.ButtonStyle.green)
    async def jouer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Ce n'est pas ton jeu !", ephemeral=True)
            return

        rouleaux = [random.choice(SYMBOLES) for _ in range(3)]
        combo = tuple(rouleaux)
        gain = GAINS.get(combo, 0) - 10

        result = db.add_points(str(interaction.user.id), gain)
        sign = "+" if gain >= 0 else ""

        embed = discord.Embed(
            title="🎰 Machine à Sous",
            description=f"## {rouleaux[0]} | {rouleaux[1]} | {rouleaux[2]}",
            color=0x2ecc71 if gain >= 0 else 0xe74c3c
        )
        if gain >= 0:
            embed.add_field(name="🎉 Gain !", value=f"+{gain + 10} pts (mise récupérée)", inline=True)
        else:
            embed.add_field(name="💸 Perdu", value="-10 pts (mise)", inline=True)
        embed.add_field(name="Total", value=f"{result['total']} pts fictifs", inline=True)
        embed.set_footer(text="Relance ou ferme !")

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="❌ Fermer", style=discord.ButtonStyle.grey)
    async def fermer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="À bientôt ! 🎰", embed=None, view=None)


# ──────────────────────────────────────────
#  QUESTION POUR UN CHAMPION
# ──────────────────────────────────────────

class ChoisirThemeChampion(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user
        select = discord.ui.Select(
            placeholder="Choisis un thème...",
            options=[discord.SelectOption(label=t, value=t) for t in THEMES_CHAMPION]
        )
        select.callback = self.theme_choisi
        self.add_item(select)
        mode_select = discord.ui.Select(
            placeholder="Mode de jeu...",
            options=[
                discord.SelectOption(label="Solo", value="solo", description="Tu joues seul"),
                discord.SelectOption(label="Versus (annonce en public)", value="versus", description="Défie quelqu'un"),
                discord.SelectOption(label="Coop (annonce en public)", value="coop", description="Jouez ensemble"),
            ]
        )
        mode_select.callback = self.mode_choisi
        self.add_item(mode_select)
        self.theme = None
        self.mode = None

    async def theme_choisi(self, interaction: discord.Interaction):
        self.theme = interaction.data["values"][0]
        await interaction.response.defer()
        await self.lancer_si_pret(interaction)

    async def mode_choisi(self, interaction: discord.Interaction):
        self.mode = interaction.data["values"][0]
        await interaction.response.defer()
        await self.lancer_si_pret(interaction)

    async def lancer_si_pret(self, interaction: discord.Interaction):
        if self.theme and self.mode:
            await interaction.edit_original_response(content="⏳ Génération de la question...", embed=None, view=None)
            try:
                content = await generate_activity_content("champion_question", self.theme)
                view = QuizChampion(interaction.user, content, self.mode)
                embed = build_champion_embed(content, self.mode)
                await interaction.edit_original_response(content=None, embed=embed, view=view)
            except Exception as e:
                await interaction.edit_original_response(content=f"❌ Erreur : {e}", view=None)

def build_champion_embed(content: dict, mode: str) -> discord.Embed:
    mode_label = {"solo": "Solo 🎯", "versus": "Versus ⚔️", "coop": "Coop 🤝"}.get(mode, mode)
    embed = discord.Embed(
        title=f"🧠 Question pour un Champion — {mode_label}",
        description=f"## {content['question']}",
        color=0x3498db
    )
    embed.add_field(name="Niveau", value=content.get("niveau", "?"), inline=True)
    embed.set_footer(text="Clique sur la bonne réponse !")
    return embed

class QuizChampion(discord.ui.View):
    def __init__(self, user, content: dict, mode: str):
        super().__init__(timeout=30)
        self.user = user
        self.content = content
        self.mode = mode
        self.repondu = set()
        propositions = content.get("propositions", [])
        bonne = content.get("bonne_reponse", 0)
        lettres = ["A", "B", "C", "D"]
        for i, prop in enumerate(propositions):
            btn = discord.ui.Button(
                label=f"{lettres[i]}. {prop[:50]}",
                style=discord.ButtonStyle.blurple,
                custom_id=f"rep_{i}"
            )
            btn.callback = self.make_callback(i, i == bonne)
            self.add_item(btn)

    def make_callback(self, index: int, est_bonne: bool):
        async def callback(interaction: discord.Interaction):
            uid = str(interaction.user.id)
            if self.mode == "solo" and interaction.user.id != self.user.id:
                await interaction.response.send_message("Ce n'est pas ton quiz !", ephemeral=True)
                return
            if uid in self.repondu:
                await interaction.response.send_message("Tu as déjà répondu !", ephemeral=True)
                return
            self.repondu.add(uid)
            pts = 30 if est_bonne else -5
            result = db.add_points(uid, pts)
            anecdote = self.content.get("anecdote", "")
            bonne_rep = self.content["propositions"][self.content["bonne_reponse"]]
            if est_bonne:
                msg = f"✅ **Bonne réponse !** +30 pts fictifs\n📚 {anecdote}"
            else:
                msg = f"❌ **Raté !** La réponse était : **{bonne_rep}**\n-5 pts fictifs\n📚 {anecdote}"
            await interaction.response.send_message(f"{msg}\n💰 Total : {result['total']} pts", ephemeral=True)
        return callback


# ──────────────────────────────────────────
#  QUI VEUT GAGNER DES PIÈCES (4 boutons)
# ──────────────────────────────────────────

class QuizQuatreChoix(discord.ui.View):
    def __init__(self, user, content: dict):
        super().__init__(timeout=30)
        self.user = user
        self.content = content
        self.repondu = False
        propositions = content.get("propositions", [])
        bonne = content.get("bonne_reponse", 0)
        lettres = ["A", "B", "C", "D"]
        for i, prop in enumerate(propositions):
            btn = discord.ui.Button(
                label=f"{lettres[i]}. {prop[:50]}",
                style=discord.ButtonStyle.blurple,
                custom_id=f"qvg_{i}"
            )
            btn.callback = self.make_callback(i, i == bonne)
            self.add_item(btn)

    def make_callback(self, index: int, est_bonne: bool):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("Ce n'est pas ton quiz !", ephemeral=True)
                return
            if self.repondu:
                await interaction.response.send_message("Tu as déjà répondu !", ephemeral=True)
                return
            self.repondu = True
            pts = 20 if est_bonne else -5
            result = db.add_points(str(interaction.user.id), pts)
            bonne_rep = self.content["propositions"][self.content["bonne_reponse"]]
            anecdote = self.content.get("anecdote", "")
            if est_bonne:
                msg = f"✅ **Bonne réponse !** +20 pts fictifs\n📚 {anecdote}"
            else:
                msg = f"❌ **Raté !** La réponse était : **{bonne_rep}**\n-5 pts fictifs"
            await interaction.response.send_message(f"{msg}\n💰 Total : {result['total']} pts", ephemeral=True)
            for child in self.children:
                child.disabled = True
            await interaction.edit_original_response(view=self)
        return callback


# ──────────────────────────────────────────
#  PUISSANCE 4
# ──────────────────────────────────────────

class DemanderAdversaire(discord.ui.View):
    def __init__(self, challenger, game_type):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.game_type = game_type

    @discord.ui.button(label="🎮 Lancer en solo vs Bot", style=discord.ButtonStyle.green)
    async def solo(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.challenger.id:
            await interaction.response.send_message("Ce n'est pas ton jeu !", ephemeral=True)
            return
        game = Puissance4Game(self.challenger, None)
        embed = game.build_embed()
        view = Puissance4View(game)
        await interaction.response.edit_message(content=None, embed=embed, view=view)

    @discord.ui.button(label="⚔️ Défier quelqu'un (mentionne-le ci-dessous)", style=discord.ButtonStyle.blurple, disabled=True)
    async def versus(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

class Puissance4Game:
    ROWS = 6
    COLS = 7
    EMPTY = "⬛"
    P1 = "🔴"
    P2 = "🟡"

    def __init__(self, p1, p2):
        self.board = [[self.EMPTY] * self.COLS for _ in range(self.ROWS)]
        self.p1 = p1
        self.p2 = p2  # None = bot
        self.current = 1
        self.winner = None
        self.moves = 0

    def drop(self, col: int) -> bool:
        for row in range(self.ROWS - 1, -1, -1):
            if self.board[row][col] == self.EMPTY:
                self.board[row][col] = self.P1 if self.current == 1 else self.P2
                self.moves += 1
                self.check_winner(row, col)
                return True
        return False

    def bot_move(self):
        available = [c for c in range(self.COLS) if self.board[0][c] == self.EMPTY]
        if available:
            col = random.choice(available)
            self.current = 2
            self.drop(col)
            self.current = 1

    def check_winner(self, row, col):
        piece = self.board[row][col]
        directions = [(0,1),(1,0),(1,1),(1,-1)]
        for dr, dc in directions:
            count = 1
            for d in [1, -1]:
                r, c = row + dr*d, col + dc*d
                while 0 <= r < self.ROWS and 0 <= c < self.COLS and self.board[r][c] == piece:
                    count += 1
                    r += dr*d
                    c += dc*d
            if count >= 4:
                self.winner = self.current
                return

    def build_embed(self) -> discord.Embed:
        nums = "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣"
        board_str = "\n".join(["".join(row) for row in self.board]) + "\n" + nums
        if self.winner:
            title = f"🔴 Puissance 4 — {'Tu as gagné ! 🎉' if self.winner == 1 else 'Le bot a gagné 😅'}"
            color = 0x2ecc71 if self.winner == 1 else 0xe74c3c
        elif self.moves >= self.ROWS * self.COLS:
            title = "🔴 Puissance 4 — Match nul !"
            color = 0x95a5a6
        else:
            turn = "🔴 Ton tour" if self.current == 1 else "🟡 Tour du bot"
            title = f"🔴 Puissance 4 — {turn}"
            color = 0x3498db
        embed = discord.Embed(title=title, description=board_str, color=color)
        return embed

class Puissance4View(discord.ui.View):
    def __init__(self, game: Puissance4Game):
        super().__init__(timeout=120)
        self.game = game
        for col in range(7):
            btn = discord.ui.Button(
                label=str(col + 1),
                style=discord.ButtonStyle.grey,
                custom_id=f"p4_{col}",
                row=0
            )
            btn.callback = self.make_col_callback(col)
            self.add_item(btn)

    def make_col_callback(self, col: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.game.p1.id:
                await interaction.response.send_message("Ce n'est pas ton jeu !", ephemeral=True)
                return
            if self.game.winner or self.game.moves >= self.game.ROWS * self.game.COLS:
                await interaction.response.send_message("La partie est terminée !", ephemeral=True)
                return
            placed = self.game.drop(col)
            if not placed:
                await interaction.response.send_message("Colonne pleine !", ephemeral=True)
                return
            if not self.game.winner:
                self.game.bot_move()
            embed = self.game.build_embed()
            if self.game.winner or self.game.moves >= self.game.ROWS * self.game.COLS:
                for child in self.children:
                    child.disabled = True
                pts = 25 if self.game.winner == 1 else 0
                if pts:
                    db.add_points(str(interaction.user.id), pts)
            await interaction.response.edit_message(embed=embed, view=self)
        return callback


# ──────────────────────────────────────────
#  COMMANDE /menu
# ──────────────────────────────────────────

def setup_menu_command(tree, bot):
    @tree.command(name="menu", description="Ouvre le menu des mini-jeux permanents 🎮")
    async def menu(interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 Menu des Mini-Jeux",
            description="Choisis un jeu pour t'amuser !",
            color=0x7289da
        )
        embed.add_field(name="🎰 Machine à sous", value="Solo — Tente ta chance !", inline=True)
        embed.add_field(name="🧠 Question pour un Champion", value="Solo/Versus/Coop — Teste tes connaissances", inline=True)
        embed.add_field(name="💰 Qui veut gagner des pièces ?", value="Solo — Quiz 4 choix", inline=True)
        embed.add_field(name="🔴 Puissance 4", value="Solo vs Bot — Stratégie !", inline=True)
        embed.add_field(name="🌐 Site Web", value="Bientôt disponible...", inline=True)
        embed.set_footer(text="Les points fictifs seront convertis en pièces DraftBot à la fin des vacances !")
        view = MenuPrincipal()
        await interaction.response.send_message(embed=embed, view=view)
