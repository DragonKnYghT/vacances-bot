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
from ai_generator import generate_activity_content
from data_manager import DataManager
 
db = DataManager()
 
THEMES_CHAMPION = [
    "Culture générale", "Histoire", "Science", "Sport",
    "Cinéma", "Musique", "Géographie", "Cuisine",
    "Animaux", "Technologies", "Célébrités", "Art"
]
 
# ──────────────────────────────────────────
#  MENU PRINCIPAL
# ──────────────────────────────────────────
 
class MenuPrincipal(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
 
    @discord.ui.button(label="🎰 Machine à sous", style=discord.ButtonStyle.green, row=0)
    async def machine_sous(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = MachineASous(interaction.user)
        embed = discord.Embed(
            title="🎰 Machine à Sous",
            description=(
                "**Mise : 10 pts fictifs**\n\n"
                "🟢🟢🟢 = +200 pts | 💎💎💎 = +150 | 7️⃣7️⃣7️⃣ = +120\n"
                "⭐⭐⭐ = +100 | 🍇🍇🍇 = +50 | 🍊🍊🍊 = +40\n"
                "🍋🍋🍋 = +30 | 🍒🍒🍒 = +20\n"
                "**2 symboles identiques = +5 pts** 🎲"
            ),
            color=0xf1c40f
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
 
    @discord.ui.button(label="🧠 Question Champion", style=discord.ButtonStyle.blurple, row=0)
    async def question_champion(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ChoisirThemeChampion(interaction.user)
        embed = discord.Embed(
            title="🧠 Question pour un Champion",
            description="Choisis un thème et un mode de jeu !",
            color=0x3498db
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
 
    @discord.ui.button(label="💰 Qui veut gagner ?", style=discord.ButtonStyle.blurple, row=0)
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
            embed.set_footer(text="✅ Bonne réponse = +20 pts | ❌ Mauvaise = -5 pts")
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur génération : {e}", ephemeral=True)
 
    @discord.ui.button(label="🔴 Puissance 4", style=discord.ButtonStyle.red, row=1)
    async def puissance4(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ChoisirModeP4(interaction.user)
        embed = discord.Embed(
            title="🔴 Puissance 4",
            description=f"**{interaction.user.display_name}** veut jouer !",
            color=0xe74c3c
        )
        embed.add_field(name="Options", value="Joue contre le bot, ou lance un défi public !", inline=False)
        await interaction.response.send_message(embed=embed, view=view)
 
    @discord.ui.button(label="🌐 Site Web", style=discord.ButtonStyle.grey, disabled=True, row=1)
    async def site_web(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚧 Bientôt disponible !", ephemeral=True)
 
 
# ──────────────────────────────────────────
#  MACHINE À SOUS
# ──────────────────────────────────────────
 
SYMBOLES = ["🍒", "🍋", "🍊", "🍇", "⭐", "7️⃣", "💎", "🟢"]
GAINS_TRIPLE = {
    "🟢": 200, "💎": 150, "7️⃣": 120, "⭐": 100,
    "🍇": 50, "🍊": 40, "🍋": 30, "🍒": 20
}
 
def calcule_gain(rouleaux: list) -> tuple:
    mise = 10
    a, b, c = rouleaux
    if a == b == c:
        gain = GAINS_TRIPLE.get(a, 20)
        return gain - mise, f"TRIPLE {a} ! +{gain} pts 🎉"
    if a == b or b == c or a == c:
        symbole = a if a == b else (b if b == c else a)
        return 5 - mise, f"Double {symbole} ! +5 pts 🎲"
    return -mise, "Rien... 😢 -10 pts"
 
class MachineASous(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user
        self.parties = 0
 
    @discord.ui.button(label="🎰 Jouer (-10 pts)", style=discord.ButtonStyle.green)
    async def jouer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Ce n'est pas ton jeu !", ephemeral=True)
            return
        rouleaux = [random.choice(SYMBOLES) for _ in range(3)]
        gain_net, description = calcule_gain(rouleaux)
        result = db.add_points(str(interaction.user.id), gain_net)
        self.parties += 1
        embed = discord.Embed(
            title="🎰 Machine à Sous",
            description=f"## {rouleaux[0]}  {rouleaux[1]}  {rouleaux[2]}\n**{description}**",
            color=0x2ecc71 if gain_net >= 0 else 0xe74c3c
        )
        sign = "+" if gain_net >= 0 else ""
        embed.add_field(name="Résultat", value=f"{sign}{gain_net} pts", inline=True)
        embed.add_field(name="Total", value=f"{result['total']} pts fictifs", inline=True)
        embed.set_footer(text=f"Parties : {self.parties} | 2 symboles = +5 pts | 3 symboles = jackpot !")
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
        self.theme = None
        self.mode = None
 
        theme_select = discord.ui.Select(
            placeholder="1️⃣ Choisis un thème...",
            options=[discord.SelectOption(label=t, value=t) for t in THEMES_CHAMPION],
            custom_id=f"theme_{uuid.uuid4().hex[:8]}"
        )
        theme_select.callback = self.theme_choisi
        self.add_item(theme_select)
 
        mode_select = discord.ui.Select(
            placeholder="2️⃣ Choisis un mode...",
            options=[
                discord.SelectOption(label="🎯 Solo", value="solo", description="Réponse privée pour toi seul"),
                discord.SelectOption(label="⚔️ Versus", value="versus", description="Public, le plus rapide gagne le bonus"),
                discord.SelectOption(label="🤝 Coop", value="coop", description="Public, tout le monde gagne des points"),
            ],
            custom_id=f"mode_{uuid.uuid4().hex[:8]}"
        )
        mode_select.callback = self.mode_choisi
        self.add_item(mode_select)
 
    async def theme_choisi(self, interaction: discord.Interaction):
        self.theme = interaction.data["values"][0]
        await interaction.response.defer()
        await self.lancer_si_pret(interaction)
 
    async def mode_choisi(self, interaction: discord.Interaction):
        self.mode = interaction.data["values"][0]
        await interaction.response.defer()
        await self.lancer_si_pret(interaction)
 
    async def lancer_si_pret(self, interaction: discord.Interaction):
        if not (self.theme and self.mode):
            return
        await interaction.edit_original_response(content="⏳ Génération...", embed=None, view=None)
        try:
            content = await generate_activity_content("champion_question", self.theme)
            content["theme"] = self.theme
            view = QuizChampion(interaction.user, content, self.mode)
            embed = build_champion_embed(content, self.mode)
 
            if self.mode in ("versus", "coop"):
                await interaction.edit_original_response(content="✅ Question lancée en public !", embed=None, view=None)
                await interaction.channel.send(embed=embed, view=view)
            else:
                await interaction.edit_original_response(content=None, embed=embed, view=view)
        except Exception as e:
            await interaction.edit_original_response(content=f"❌ Erreur : {e}", view=None)
 
def build_champion_embed(content: dict, mode: str) -> discord.Embed:
    mode_labels = {"solo": "Solo 🎯", "versus": "Versus ⚔️", "coop": "Coop 🤝"}
    mode_desc = {
        "solo": "Réponds en privé !",
        "versus": "⚡ Le plus rapide à trouver gagne un bonus !",
        "coop": "🤝 Tout le monde peut répondre et gagner des points !"
    }
    embed = discord.Embed(
        title=f"🧠 Question pour un Champion — {mode_labels.get(mode, mode)}",
        description=f"## {content['question']}\n*{mode_desc.get(mode, '')}*",
        color=0x3498db
    )
    embed.add_field(name="Niveau", value=content.get("niveau", "?"), inline=True)
    embed.add_field(name="Thème", value=content.get("theme", "Général"), inline=True)
    embed.set_footer(text="Clique sur la bonne réponse !")
    return embed
 
class QuizChampion(discord.ui.View):
    def __init__(self, user, content: dict, mode: str):
        super().__init__(timeout=60)
        self.user = user
        self.content = content
        self.mode = mode
        self.repondu = set()
        self.premier = None
        propositions = content.get("propositions", [])
        bonne = content.get("bonne_reponse", 0)
        lettres = ["A", "B", "C", "D"]
        uid = uuid.uuid4().hex[:6]
        for i, prop in enumerate(propositions):
            btn = discord.ui.Button(
                label=f"{lettres[i]}. {prop[:50]}",
                style=discord.ButtonStyle.blurple,
                custom_id=f"champ_{uid}_{i}"
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
            est_premier = self.premier is None and est_bonne
            if est_premier:
                self.premier = uid
 
            if self.mode == "versus":
                pts = 30 if (est_bonne and est_premier) else (10 if est_bonne else -5)
            elif self.mode == "coop":
                # En coop tout le monde gagne pareil, pas de bonus premier
                pts = 20 if est_bonne else 0
            else:
                pts = 30 if est_bonne else -5
 
            result = db.add_points(uid, pts)
            bonne_rep = self.content["propositions"][self.content["bonne_reponse"]]
            anecdote = self.content.get("anecdote", "")
            sign = "+" if pts >= 0 else ""
 
            if est_bonne:
                msg = f"✅ **Bonne réponse !** {sign}{pts} pts"
                if self.mode == "versus" and est_premier:
                    msg += " 🏆 **Premier ! Bonus x1.5 !**"
                msg += f"\n📚 {anecdote}"
            else:
                if self.mode == "coop":
                    msg = f"❌ **Raté !** La réponse était : **{bonne_rep}**\n0 pts (pas de pénalité en coop)\n📚 {anecdote}"
                else:
                    msg = f"❌ **Raté !** La réponse était : **{bonne_rep}**\n{sign}{pts} pts\n📚 {anecdote}"
 
            await interaction.response.send_message(f"{msg}\n💰 Total : {result['total']} pts", ephemeral=True)
        return callback
 
 
# ──────────────────────────────────────────
#  QUI VEUT GAGNER DES PIÈCES
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
        uid = uuid.uuid4().hex[:6]
        for i, prop in enumerate(propositions):
            btn = discord.ui.Button(
                label=f"{lettres[i]}. {prop[:50]}",
                style=discord.ButtonStyle.blurple,
                custom_id=f"qvg_{uid}_{i}"
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
            sign = "+" if pts >= 0 else ""
            if est_bonne:
                msg = f"✅ **Bonne réponse !** {sign}{pts} pts\n📚 {anecdote}"
            else:
                msg = f"❌ **Raté !** La réponse était : **{bonne_rep}**\n{sign}{pts} pts"
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"{msg}\n💰 Total : {result['total']} pts", ephemeral=True)
        return callback
 
 
# ──────────────────────────────────────────
#  PUISSANCE 4
# ──────────────────────────────────────────
 
class ChoisirModeP4(discord.ui.View):
    def __init__(self, challenger):
        super().__init__(timeout=60)
        self.challenger = challenger
 
    @discord.ui.button(label="🤖 Jouer contre le Bot", style=discord.ButtonStyle.green)
    async def vs_bot(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.challenger.id:
            await interaction.response.send_message("Ce n'est pas ton défi !", ephemeral=True)
            return
        game = Puissance4Game(self.challenger, None)
        view = Puissance4View(game)
        await interaction.response.edit_message(embed=game.build_embed(), view=view)
 
    @discord.ui.button(label="⚔️ Défier un joueur", style=discord.ButtonStyle.blurple)
    async def vs_joueur(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.challenger.id:
            await interaction.response.send_message("Ce n'est pas ton défi !", ephemeral=True)
            return
        view = AttendreChallengeP4(self.challenger)
        embed = discord.Embed(
            title="⚔️ Défi Puissance 4 !",
            description=f"**{self.challenger.display_name}** lance un défi !\nN'importe qui peut cliquer sur **Accepter** pour jouer !",
            color=0xe74c3c
        )
        await interaction.response.edit_message(embed=embed, view=view)
 
class AttendreChallengeP4(discord.ui.View):
    def __init__(self, challenger):
        super().__init__(timeout=120)
        self.challenger = challenger
        self.accepted = False
 
    @discord.ui.button(label="✅ Accepter le défi !", style=discord.ButtonStyle.green)
    async def accepter(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.challenger.id:
            await interaction.response.send_message("Tu ne peux pas accepter ton propre défi !", ephemeral=True)
            return
        if self.accepted:
            await interaction.response.send_message("Ce défi a déjà été accepté !", ephemeral=True)
            return
        self.accepted = True
        game = Puissance4Game(self.challenger, interaction.user)
        view = Puissance4View(game)
        await interaction.response.edit_message(embed=game.build_embed(), view=view)
 
class Puissance4Game:
    ROWS = 6
    COLS = 7
    EMPTY = "⬛"
    P1 = "🔴"
    P2 = "🟡"
 
    def __init__(self, p1, p2):
        self.board = [[self.EMPTY] * self.COLS for _ in range(self.ROWS)]
        self.p1 = p1
        self.p2 = p2
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
        for dr, dc in [(0,1),(1,0),(1,1),(1,-1)]:
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
        p2_name = self.p2.display_name if self.p2 else "🤖 Bot"
        if self.winner:
            winner_name = self.p1.display_name if self.winner == 1 else p2_name
            title = f"🏆 {winner_name} a gagné !"
            color = 0x2ecc71
        elif self.moves >= self.ROWS * self.COLS:
            title = "🤝 Match nul !"
            color = 0x95a5a6
        else:
            turn_name = self.p1.display_name if self.current == 1 else p2_name
            turn_piece = self.P1 if self.current == 1 else self.P2
            title = f"{turn_piece} Tour de {turn_name}"
            color = 0x3498db
        embed = discord.Embed(title=title, description=board_str, color=color)
        embed.set_footer(text=f"🔴 {self.p1.display_name} vs 🟡 {p2_name}")
        return embed
 
class Puissance4View(discord.ui.View):
    def __init__(self, game: Puissance4Game):
        super().__init__(timeout=300)
        self.game = game
        uid = uuid.uuid4().hex[:6]
        for col in range(7):
            btn = discord.ui.Button(
                label=str(col + 1),
                style=discord.ButtonStyle.grey,
                custom_id=f"p4_{uid}_{col}",
                row=0
            )
            btn.callback = self.make_col_callback(col)
            self.add_item(btn)
 
    def make_col_callback(self, col: int):
        async def callback(interaction: discord.Interaction):
            game = self.game
            # Vérifier le bon joueur
            if game.current == 1 and interaction.user.id != game.p1.id:
                await interaction.response.send_message("Ce n'est pas ton tour ! 🔴", ephemeral=True)
                return
            if game.current == 2 and game.p2 and interaction.user.id != game.p2.id:
                await interaction.response.send_message("Ce n'est pas ton tour ! 🟡", ephemeral=True)
                return
            if game.winner or game.moves >= game.ROWS * game.COLS:
                await interaction.response.send_message("La partie est terminée !", ephemeral=True)
                return
            placed = game.drop(col)
            if not placed:
                await interaction.response.send_message("Colonne pleine ! Choisis une autre.", ephemeral=True)
                return
            # Tour suivant
            if not game.p2 and not game.winner:
                game.bot_move()
            elif game.p2 and not game.winner:
                game.current = 2 if game.current == 1 else 1
 
            if game.winner or game.moves >= game.ROWS * game.COLS:
                for child in self.children:
                    child.disabled = True
                if game.winner == 1:
                    db.add_points(str(game.p1.id), 25)
                elif game.winner == 2 and game.p2:
                    db.add_points(str(game.p2.id), 25)
 
            await interaction.response.edit_message(embed=game.build_embed(), view=self)
        return callback
 
 
# ──────────────────────────────────────────
#  SETUP /menu
# ──────────────────────────────────────────
 
def setup_menu_command(tree, bot):
    @tree.command(name="menu", description="Ouvre le menu des mini-jeux permanents 🎮")
    async def menu(interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 Menu des Mini-Jeux",
            description="Choisis un jeu pour t'amuser !",
            color=0x7289da
        )
        embed.add_field(name="🎰 Machine à sous", value="Solo — 2 symboles = +5 pts, 3 = jackpot !", inline=True)
        embed.add_field(name="🧠 Question Champion", value="Solo / Versus / Coop — Choix du thème", inline=True)
        embed.add_field(name="💰 Qui veut gagner ?", value="Solo — Quiz 4 choix, +20 pts si correct", inline=True)
        embed.add_field(name="🔴 Puissance 4", value="vs Bot ou vs un joueur en direct !", inline=True)
        embed.add_field(name="🌐 Site Web", value="Bientôt disponible...", inline=True)
        embed.set_footer(text="Points fictifs → pièces DraftBot à la fin des vacances !")
        await interaction.response.send_message(embed=embed, view=MenuPrincipal())
