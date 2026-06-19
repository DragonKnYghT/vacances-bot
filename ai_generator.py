"""
Générateur de contenu pour les activités du bot — VERSION SANS IA.

Les serveurs Gemini étant régulièrement saturés (erreurs 429/RESOURCE_EXHAUSTED
qui empêchaient l'envoi du message du jour pendant plusieurs jours), ce module
a été réécrit pour piocher dans des banques de contenu pré-écrites et stockées
en dur, plutôt que d'appeler une API externe.

Avantages :
- Aucune dépendance réseau → ne tombe jamais en panne
- Aucun coût / quota à gérer
- Temps de réponse instantané

Pour enrichir le contenu, il suffit d'ajouter des entrées dans les listes
BANK_* ci-dessous — aucune autre modification n'est nécessaire.
"""

import random

# ──────────────────────────────────────────
#  ANTI-RÉPÉTITION
#  Mémorise les derniers indices tirés par type d'activité pour éviter
#  de retomber tout de suite sur le même contenu (reset une fois le pool épuisé).
# ──────────────────────────────────────────

_recent_picks = {}


def _pick(bank, key):
    """Tire un élément au hasard dans `bank`, en évitant les derniers tirés."""
    if not bank:
        raise ValueError(f"Banque de contenu vide pour la clé '{key}'")

    used = _recent_picks.setdefault(key, [])
    available = [i for i in range(len(bank)) if i not in used]

    if not available:
        # Pool épuisé → on recommence un cycle frais
        used.clear()
        available = list(range(len(bank)))

    idx = random.choice(available)
    used.append(idx)
    # Garde un historique borné (évite que la liste grossisse indéfiniment)
    if len(used) > len(bank):
        used.pop(0)

    return bank[idx]


# ──────────────────────────────────────────
#  BANQUE — MAIS... (X€ ou Y€ mais...)
# ──────────────────────────────────────────

BANK_MAIS = [
    {"montant_petit": "10€", "montant_grand": "200€", "mais": "tu dois porter des chaussettes dans les sandales pendant 1 mois", "contexte": "Le confort avant tout, non ?"},
    {"montant_petit": "5€", "montant_grand": "150€", "mais": "tu dois envoyer un message vocal de 30 secondes chantant en faux à chaque réveil", "contexte": "Le réveil le plus mélodieux du serveur."},
    {"montant_petit": "20€", "montant_grand": "500€", "mais": "tu dois manger uniquement des aliments de couleur orange pendant une semaine", "contexte": "Carotte, mandarine... et c'est tout."},
    {"montant_petit": "15€", "montant_grand": "300€", "mais": "ton pseudo Discord doit rester 'Je sens le fromage' pendant 2 semaines", "contexte": "L'odeur ne suit pas le pseudo, normalement."},
    {"montant_petit": "8€", "montant_grand": "180€", "mais": "tu dois parler comme un robot pendant toutes tes prochaines parties en vocal", "contexte": "BEEP BOOP, argent reçu."},
    {"montant_petit": "12€", "montant_grand": "250€", "mais": "tu dois liker tous les messages du salon général pendant 24h, sans exception", "contexte": "Même les messages les plus tristes."},
    {"montant_petit": "25€", "montant_grand": "600€", "mais": "tu ne peux plus utiliser le mot 'oui' pendant une semaine entière", "contexte": "'Ouais', 'Affirmatif', tout sauf 'oui'."},
    {"montant_petit": "10€", "montant_grand": "220€", "mais": "tu dois mettre une photo de patate en avatar Discord pendant 3 jours", "contexte": "La patate, future tendance de 2026."},
    {"montant_petit": "18€", "montant_grand": "400€", "mais": "tu dois répondre à chaque message par une question, façon thérapeute, pendant 48h", "contexte": "Et comment ça te fait sentir, cet argent ?"},
    {"montant_petit": "30€", "montant_grand": "700€", "mais": "tu dois faire 50 pompes à chaque fois que quelqu'un dit 'GG' dans un vocal", "contexte": "Prépare tes bras."},
    {"montant_petit": "6€", "montant_grand": "140€", "mais": "tu dois écrire tous tes messages en alternant MAJUSCULE et minuscule pendant 24h", "contexte": "lA pOnCtUaTiOn DeS ChAmPiOnS."},
    {"montant_petit": "22€", "montant_grand": "480€", "mais": "tu dois utiliser uniquement des emojis pour communiquer pendant 1 heure en vocal", "contexte": "Le langage des signes version Discord."},
    {"montant_petit": "14€", "montant_grand": "320€", "mais": "tu dois appeler tout le monde 'mon capitaine' pendant 3 jours", "contexte": "Respect militaire obligatoire."},
    {"montant_petit": "9€", "montant_grand": "190€", "mais": "tu dois changer ton pseudo en 'Roi/Reine des Limaces' pendant une semaine", "contexte": "La royauté gluante t'attend."},
    {"montant_petit": "16€", "montant_grand": "360€", "mais": "tu dois finir chaque phrase par 'comme dirait ma grand-mère' pendant 2 jours", "contexte": "La sagesse ancestrale au service du serveur."},
]

# ──────────────────────────────────────────
#  BANQUE — BLIND TEST
# ──────────────────────────────────────────

BANK_BLINDTEST = [
    {"paroles": "Je voulais juste te dire que sans toi\nMa vie n'aurait pas la même saveur\nOn a traversé les pires moments\nEt on est encore là, debout", "titre": "Formidable", "artiste": "Stromae", "source": None, "annee": "2013", "indice_bonus": "Le clip se passe dans un bar et l'artiste joue un homme ivre."},
    {"paroles": "On s'est connu, on s'est plu\nPeut-être qu'on s'est reconnu\nJe ne t'ai jamais oublié", "titre": "La Vie en Rose", "artiste": "Édith Piaf", "source": None, "annee": "1947", "indice_bonus": "Un classique français connu dans le monde entier."},
    {"paroles": "Tout le monde te dit que c'est qu'un jeu\nMais moi je sais que c'est mortel\nQuand on aime, on ne compte pas", "titre": "Mistral Gagnant", "artiste": "Renaud", "source": None, "annee": "1985", "indice_bonus": "La chanson évoque des bonbons d'enfance."},
    {"paroles": "I'm walking on sunshine, whoa\nAnd don't it feel good\nHey, alright now", "titre": "Walking on Sunshine", "artiste": "Katrina and the Waves", "source": None, "annee": "1985", "indice_bonus": "Souvent utilisée dans les pubs et les comédies romantiques."},
    {"paroles": "Caroline, ça balance pas mal à Nanterre\nEntre les blocs et les barres", "titre": "Tous les mêmes", "artiste": "Stromae", "source": None, "annee": "2013", "indice_bonus": "Une chanson sur les relations homme-femme avec deux personnages dans le clip."},
    {"paroles": "On se ressemble tellement\nQu'on s'est vus l'un dans l'autre\nEt c'est pas innocent", "titre": "Je te promets", "artiste": "Johnny Hallyday", "source": None, "annee": "1985", "indice_bonus": "Une chanson d'amour du Taulier."},
    {"paroles": "Alors on danse, alors on danse", "titre": "Alors on danse", "artiste": "Stromae", "source": None, "annee": "2009", "indice_bonus": "Le premier gros succès international de l'artiste."},
    {"paroles": "Papaoutai, où t'es papaoutai\nOù t'es", "titre": "Papaoutai", "artiste": "Stromae", "source": None, "annee": "2013", "indice_bonus": "Le clip montre une statue de père dans un salon."},
    {"paroles": "Le requin profite de la nuit\nIl tourne, il sonde, il rode", "titre": "Le Requin", "artiste": "Vianney", "source": None, "annee": "2017", "indice_bonus": "Une chanson sur la peur et l'anxiété, métaphore animale."},
    {"paroles": "On me dit que la mer est belle\nMais quand on est marin\nEst-ce qu'on peut juger", "titre": "Bella Ciao", "artiste": "Traditionnel", "source": "La Casa de Papel", "annee": "2017", "indice_bonus": "Chant de résistance italien popularisé par une série Netflix."},
    {"paroles": "Don't stop believin'\nHold on to that feeling", "titre": "Don't Stop Believin'", "artiste": "Journey", "source": None, "annee": "1981", "indice_bonus": "Un hymne du rock américain repris dans de nombreuses séries."},
    {"paroles": "Aux Champs-Élysées, aux Champs-Élysées\nAu soleil, sous la pluie, à midi ou à minuit", "titre": "Les Champs-Élysées", "artiste": "Joe Dassin", "source": None, "annee": "1969", "indice_bonus": "Un classique chanté dans les mariages et fêtes françaises."},
    {"paroles": "We will, we will rock you\nRock you", "titre": "We Will Rock You", "artiste": "Queen", "source": None, "annee": "1977", "indice_bonus": "Chanté dans tous les stades du monde."},
    {"paroles": "Tombé du ciel comme une étoile filante\nTu m'as ébloui sans crier gare", "titre": "Comme des enfants", "artiste": "Coeur de Pirate", "source": None, "annee": "2008", "indice_bonus": "Un titre québécois devenu hit en France."},
    {"paroles": "Vous m'avez demandé de chanter pour la fête\nMais moi je n'ai dans la tête que des mots tristes", "titre": "La Javanaise", "artiste": "Serge Gainsbourg", "source": None, "annee": "1962", "indice_bonus": "Écrite pour Juliette Gréco."},
]

# ──────────────────────────────────────────
#  BANQUE — ROI DU SERVEUR (indices)
# ──────────────────────────────────────────

BANK_ROI_INDICES = [
    "Le Roi a déjà changé son pseudo Discord plus de 5 fois.",
    "Le Roi possède au moins un rôle personnalisé sur ce serveur.",
    "Le Roi se connecte le plus souvent en fin de journée.",
    "Le Roi a tendance à utiliser beaucoup d'emojis dans ses messages.",
    "Le Roi a déjà participé à toutes les activités hebdomadaires sans exception.",
    "Le Roi préfère les vocaux aux messages écrits.",
    "Le Roi a un avatar avec une couleur dominante facilement reconnaissable.",
    "Le Roi est plutôt du genre silencieux mais toujours présent.",
    "Le Roi a déjà gagné un mini-jeu sur ce serveur au moins une fois.",
    "Le Roi n'est membre de ce serveur que depuis quelques mois.",
    "Le Roi utilise souvent des abréviations dans ses messages.",
    "Le Roi a un horaire de connexion plutôt régulier, presque prévisible.",
    "Le Roi aime taquiner les autres membres avec humour.",
    "Le Roi a probablement déjà gagné des points cette semaine.",
    "Le Roi se trouve dans la moitié 'active' du classement général.",
]

# ──────────────────────────────────────────
#  BANQUE — SONDAGE ABSURDE
# ──────────────────────────────────────────

BANK_SONDAGE = [
    {"question": "Si tu devais perdre un sens pour le reste de ta vie, lequel sacrifies-tu ?", "options": ["L'odorat", "Le goût", "Le toucher", "L'ouïe"], "emojis": ["🔴", "🟡", "🟢", "🔵"]},
    {"question": "Tu dois combattre 100 canards de la taille d'un poney ou 1 poney de la taille de 100 canards ?", "options": ["100 canards géants", "1 poney géant", "Je fuis", "Je négocie avec eux"], "emojis": ["🔴", "🟡", "🟢", "🔵"]},
    {"question": "Quel super-pouvoir inutile choisirais-tu ?", "options": ["Parler aux plantes", "Toujours savoir l'heure sans montre", "Ne jamais avoir froid aux pieds", "Deviner le mot de passe wifi"], "emojis": ["🔴", "🟡", "🟢", "🔵"]},
    {"question": "Si les animaux pouvaient parler, lequel serait le plus impoli ?", "options": ["Le chat", "Le perroquet", "La chèvre", "Le pigeon"], "emojis": ["🔴", "🟡", "🟢", "🔵"]},
    {"question": "Tu dois manger la même chose tous les jours pendant un an, tu choisis quoi ?", "options": ["Pizza", "Pâtes", "Riz", "Frites"], "emojis": ["🔴", "🟡", "🟢", "🔵"]},
    {"question": "Quelle invention inutile aimerais-tu posséder ?", "options": ["Une fourchette à spaghetti automatique", "Un parapluie qui prédit le temps", "Des chaussettes qui ne se perdent jamais", "Un réveil qui se cache au lieu de sonner"], "emojis": ["🔴", "🟡", "🟢", "🔵"]},
    {"question": "Si ton ombre prenait vie, que ferait-elle en premier ?", "options": ["Te suivre comme avant", "Te trahir", "Partir en voyage", "Demander un salaire"], "emojis": ["🔴", "🟡", "🟢", "🔵"]},
    {"question": "Tu dois choisir un cri de guerre pour toute ta vie, lequel ?", "options": ["Un miaulement", "Un 'OUI' très fort", "Un sifflement aigu", "Le silence total mais menaçant"], "emojis": ["🔴", "🟡", "🟢", "🔵"]},
    {"question": "Quel est le pire endroit pour recevoir un appel important ?", "options": ["Aux toilettes", "Sous la douche", "En plein sommeil", "Pendant un examen"], "emojis": ["🔴", "🟡", "🟢", "🔵"]},
    {"question": "Si tu devais vivre dans un jeu vidéo, lequel choisirais-tu ?", "options": ["Minecraft", "Animal Crossing", "GTA", "Les Sims"], "emojis": ["🔴", "🟡", "🟢", "🔵"]},
    {"question": "Quelle activité du quotidien transformerais-tu en sport olympique ?", "options": ["Dormir", "Faire la queue", "Chercher ses clés", "Râler"], "emojis": ["🔴", "🟡", "🟢", "🔵"]},
    {"question": "Tu peux échanger ton pouce contre un super-pouvoir, tu acceptes ?", "options": ["Oui, sans hésiter", "Non, jamais", "Seulement si c'est utile", "Je négocie d'abord"], "emojis": ["🔴", "🟡", "🟢", "🔵"]},
]

# ──────────────────────────────────────────
#  BANQUE — DILEMME IMPOSSIBLE
# ──────────────────────────────────────────

BANK_DILEMME = [
    {"question": "Tu dois choisir entre [vivre 200 ans mais seul] OU [vivre 80 ans entouré de tous ceux que tu aimes] ?", "option_a": "200 ans, mais totalement seul, sans jamais revoir personne", "option_b": "80 ans, une vie normale, mais entouré jusqu'au dernier jour", "twist": "Dans les deux cas, tu gardes tous tes souvenirs intacts."},
    {"question": "Tu dois choisir entre [ne plus jamais manger de sucré] OU [ne plus jamais manger de salé] ?", "option_a": "Plus aucun sucre, gâteau, bonbon ou dessert de ta vie", "option_b": "Plus aucun sel, plat salé ou snack salé de ta vie", "twist": "L'eau plate compte comme 'neutre', tu peux toujours en boire."},
    {"question": "Tu dois choisir entre [être toujours en retard de 10 minutes] OU [être toujours en avance de 30 minutes] ?", "option_a": "Tu arrives systématiquement 10 minutes après l'heure prévue", "option_b": "Tu arrives systématiquement 30 minutes avant l'heure prévue", "twist": "Impossible de changer d'avis une fois le choix fait, c'est pour la vie."},
    {"question": "Tu dois choisir entre [lire dans les pensées des autres] OU [que personne ne puisse jamais te mentir] ?", "option_a": "Tu entends les pensées de tous ceux qui t'entourent, en permanence", "option_b": "Personne ne peut te mentir, mais tu n'entends jamais leurs pensées", "twist": "Le pouvoir est irréversible et visible par tous ceux qui le découvrent."},
    {"question": "Tu dois choisir entre [refaire la même journée pour toujours] OU [vieillir 10 ans en une nuit] ?", "option_a": "Chaque jour est exactement le même, en boucle, pour toujours", "option_b": "Tu te réveilles demain avec 10 ans de plus d'un coup", "twist": "Dans le premier cas, tu gardes la mémoire de chaque répétition."},
    {"question": "Tu dois choisir entre [ne plus jamais utiliser internet] OU [ne plus jamais sortir de chez toi] ?", "option_a": "Plus aucun accès à internet, jamais, nulle part", "option_b": "Tu ne peux plus jamais sortir de ton domicile", "twist": "Les livraisons et visites de proches restent autorisées."},
    {"question": "Tu dois choisir entre [être riche mais détesté de tous] OU [être pauvre mais aimé de tous] ?", "option_a": "Une fortune illimitée, mais tout le monde te déteste sincèrement", "option_b": "Tu n'as presque rien, mais tout le monde t'aime profondément", "twist": "La richesse ou l'amour ne peuvent jamais être 'rachetés' par la suite."},
    {"question": "Tu dois choisir entre [perdre tous tes souvenirs d'enfance] OU [ne plus jamais créer de nouveaux souvenirs] ?", "option_a": "Tous tes souvenirs avant 18 ans disparaissent immédiatement", "option_b": "À partir de maintenant, tu ne mémorises plus rien de nouveau", "twist": "Les compétences déjà acquises restent intactes dans les deux cas."},
    {"question": "Tu dois choisir entre [avoir toujours raison mais perdre tous tes amis] OU [avoir souvent tort mais les garder tous] ?", "option_a": "Tu as systématiquement raison dans chaque débat, mais tu perds tous tes amis un par un", "option_b": "Tu te trompes souvent, mais tu gardes toutes tes relations intactes", "twist": "Le monde entier sait que tu as 'toujours raison' dans le premier cas, ce qui dérange tout le monde."},
    {"question": "Tu dois choisir entre [voyager dans le futur une seule fois] OU [voyager dans le passé autant de fois que tu veux, sans rien changer] ?", "option_a": "Un seul aller simple vers le futur, sans retour possible", "option_b": "Visiter le passé à volonté, mais en simple observateur invisible", "twist": "Dans le futur, tu ne peux choisir ni la date ni l'endroit où tu arrives."},
]

# ──────────────────────────────────────────
#  BANQUE — 2 VÉRITÉS 1 MENSONGE (invitation)
# ──────────────────────────────────────────

BANK_TVM_INVITE = [
    {"invitation": "C'est l'heure du mensonge organisé ! Soumets tes 2 vérités et 1 mensonge, et voyons qui se fera avoir.", "exemples": ["J'ai déjà mangé un escargot vivant", "J'ai rencontré une célébrité dans un supermarché"]},
    {"invitation": "Prépare ton meilleur bluff : 2 vérités, 1 mensonge bien ficelé, et tout le monde doit deviner !", "exemples": ["J'ai un jumeau", "J'ai peur des pigeons"]},
    {"invitation": "Le jeu du mensonge revient ! Sois créatif, le but est que personne ne devine ton mensonge.", "exemples": ["Je n'ai jamais vu la mer", "J'ai cassé 3 téléphones cette année"]},
    {"invitation": "Aujourd'hui, on ment avec style. 2 vérités, 1 mensonge, et que le meilleur menteur gagne !", "exemples": ["J'ai déjà fait du parachute", "Je collectionne les capsules de bouteilles"]},
]

# ──────────────────────────────────────────
#  BANQUE — RECETTE IMPOSSIBLE
# ──────────────────────────────────────────

BANK_RECETTE = [
    {"titre_mystere": "Le Mystère du Chef Perdu", "ingredients": [
        {"nom": "pâtes", "quantite": "200g", "niveau": "normal"},
        {"nom": "Nutella", "quantite": "3 cuillères", "niveau": "wtf"},
        {"nom": "dentifrice à la menthe", "quantite": "1 noisette", "niveau": "impossible"},
    ], "contrainte": "Le plat doit être mangé les yeux fermés."},
    {"titre_mystere": "L'Énigme du Frigo Vide", "ingredients": [
        {"nom": "riz", "quantite": "150g", "niveau": "normal"},
        {"nom": "ketchup", "quantite": "4 cuillères", "niveau": "wtf"},
        {"nom": "chaussette propre coupée en lamelles (factice)", "quantite": "1 paire", "niveau": "impossible"},
    ], "contrainte": "La préparation ne doit pas dépasser 3 minutes."},
    {"titre_mystere": "Le Secret du Marmiton Fou", "ingredients": [
        {"nom": "poulet", "quantite": "300g", "niveau": "normal"},
        {"nom": "bonbons Haribo fondus", "quantite": "1 poignée", "niveau": "wtf"},
        {"nom": "sable de plage comestible (imaginaire)", "quantite": "1 pincée", "niveau": "impossible"},
    ], "contrainte": "Le plat doit avoir un nom en anglais, peu importe la langue d'origine."},
    {"titre_mystere": "La Recette du Chaos Culinaire", "ingredients": [
        {"nom": "fromage", "quantite": "100g", "niveau": "normal"},
        {"nom": "céréales au chocolat", "quantite": "2 poignées", "niveau": "wtf"},
        {"nom": "larme de crocodile (au choix : sauce piquante)", "quantite": "3 gouttes", "niveau": "impossible"},
    ], "contrainte": "Le plat doit être présenté comme un dessert, même si ce n'en est clairement pas un."},
    {"titre_mystere": "L'Affaire du Plat Maudit", "ingredients": [
        {"nom": "oeufs", "quantite": "3", "niveau": "normal"},
        {"nom": "chips écrasées", "quantite": "1 sachet", "niveau": "wtf"},
        {"nom": "essence de licorne (paillettes comestibles)", "quantite": "1 pincée", "niveau": "impossible"},
    ], "contrainte": "Le nom du plat doit rimer avec un prénom d'un membre du serveur."},
]

# ──────────────────────────────────────────
#  BANQUE — OLYMPIADES (épreuves)
# ──────────────────────────────────────────

BANK_OLYMPIADE = [
    {"nom": "Le Sprint des Réactions", "emoji": "⚡", "description": "Sois le plus rapide à réagir avec le bon emoji dès qu'il apparaît. La vitesse fait tout.", "comment_participer": "Utilise /jouer dès que l'emoji cible apparaît dans le salon.", "critere_victoire": "Les 3 plus rapides gagnent des points, du premier au troisième."},
    {"nom": "Le Marathon du Vocal", "emoji": "🎙️", "description": "Reste connecté en vocal le plus longtemps possible aujourd'hui sans interruption.", "comment_participer": "Connecte-toi simplement dans un salon vocal et reste actif.", "critere_victoire": "Les points sont calculés selon le temps total passé en vocal sur la journée."},
    {"nom": "Le Quiz Éclair", "emoji": "🧠", "description": "Une série de questions rapides sur des thèmes variés, sans temps de réflexion.", "comment_participer": "Utilise /jouer suivi de ta réponse dès que la question est postée.", "critere_victoire": "1 point par bonne réponse, bonus pour la rapidité."},
    {"nom": "Le Concours de Créativité", "emoji": "🎨", "description": "Propose la réponse la plus originale et créative au défi du jour.", "comment_participer": "Utilise /jouer suivi de ta proposition.", "critere_victoire": "Les votes de la communauté déterminent le gagnant."},
    {"nom": "L'Épreuve de l'Endurance Sociale", "emoji": "💬", "description": "Envoie le plus de messages pertinents possible dans la journée, sans spam.", "comment_participer": "Participe activement aux discussions du serveur toute la journée.", "critere_victoire": "Classement basé sur le nombre de messages constructifs envoyés."},
    {"nom": "Le Défi Mémoire", "emoji": "🧩", "description": "Mémorise une séquence d'emojis postée par le bot et reproduis-la parfaitement.", "comment_participer": "Utilise /jouer suivi de la séquence mémorisée.", "critere_victoire": "Points complets pour une séquence parfaite, partiels sinon."},
]

# ──────────────────────────────────────────
#  BANQUE — QUIZ CULTURE GÉNÉRALE
# ──────────────────────────────────────────

BANK_QUIZ = [
    {"question": "Quelle est la capitale de l'Australie ?", "propositions": ["Sydney", "Melbourne", "Canberra", "Perth"], "bonne_reponse": 2, "anecdote": "Canberra a été choisie comme capitale en 1908 pour mettre fin à la rivalité entre Sydney et Melbourne."},
    {"question": "Combien d'os possède le corps humain adulte ?", "propositions": ["186", "206", "226", "246"], "bonne_reponse": 1, "anecdote": "Un nouveau-né a environ 300 os, qui fusionnent en grandissant pour atteindre 206 à l'âge adulte."},
    {"question": "Quel est le plus grand océan du monde ?", "propositions": ["Atlantique", "Indien", "Arctique", "Pacifique"], "bonne_reponse": 3, "anecdote": "L'océan Pacifique couvre environ un tiers de la surface totale de la Terre."},
    {"question": "Qui a peint la Joconde ?", "propositions": ["Michel-Ange", "Léonard de Vinci", "Raphaël", "Donatello"], "bonne_reponse": 1, "anecdote": "Le tableau est exposé au Louvre et mesure seulement 77 x 53 cm."},
    {"question": "Quelle planète est surnommée la planète rouge ?", "propositions": ["Vénus", "Jupiter", "Mars", "Saturne"], "bonne_reponse": 2, "anecdote": "La couleur rouge de Mars est due à l'oxyde de fer présent à sa surface."},
    {"question": "En quelle année a eu lieu la chute du mur de Berlin ?", "propositions": ["1987", "1989", "1991", "1993"], "bonne_reponse": 1, "anecdote": "Le mur est tombé le 9 novembre 1989, symbole de la fin de la guerre froide."},
    {"question": "Quel est l'animal terrestre le plus rapide ?", "propositions": ["Lion", "Guépard", "Antilope", "Autruche"], "bonne_reponse": 1, "anecdote": "Le guépard peut atteindre 110 km/h sur de courtes distances."},
    {"question": "Combien de cœurs possède une pieuvre ?", "propositions": ["1", "2", "3", "4"], "bonne_reponse": 2, "anecdote": "Deux cœurs pompent le sang vers les branchies, le troisième vers le reste du corps."},
    {"question": "Quel pays a inventé le ping-pong ?", "propositions": ["Chine", "Japon", "Angleterre", "États-Unis"], "bonne_reponse": 2, "anecdote": "Le ping-pong est né en Angleterre dans les années 1880 comme version miniature du tennis."},
    {"question": "Quelle est la monnaie officielle du Japon ?", "propositions": ["Won", "Yuan", "Yen", "Ringgit"], "bonne_reponse": 2, "anecdote": "Le yen a été introduit en 1871 pour remplacer le système monétaire féodal."},
    {"question": "Quel est le plus long fleuve du monde ?", "propositions": ["Amazone", "Nil", "Yangtze", "Mississippi"], "bonne_reponse": 1, "anecdote": "Le Nil et l'Amazone se disputent encore ce titre selon la méthode de mesure utilisée."},
    {"question": "Combien de temps met la lumière du Soleil pour atteindre la Terre ?", "propositions": ["8 secondes", "8 minutes", "8 heures", "8 jours"], "bonne_reponse": 1, "anecdote": "La lumière voyage à environ 300 000 km/s, et le Soleil est à 150 millions de km."},
]

# ──────────────────────────────────────────
#  BANQUE — QUESTIONS CHAMPION (par thème)
#  Indexées par thème en minuscules. Une entrée "default" sert de repli
#  si le thème demandé n'a pas de banque dédiée.
# ──────────────────────────────────────────

BANK_CHAMPION_BY_THEME = {
    "default": [
        {"question": "Quel est le symbole chimique de l'or ?", "propositions": ["Or", "Au", "Ag", "Os"], "bonne_reponse": 1, "niveau": "Facile", "anecdote": "Au vient du latin 'aurum'."},
        {"question": "Quel pays a le plus de fuseaux horaires au monde ?", "propositions": ["États-Unis", "Russie", "France", "Chine"], "bonne_reponse": 2, "niveau": "Moyen", "anecdote": "Grâce à ses territoires d'outre-mer, la France compte 12 fuseaux horaires."},
        {"question": "Quelle est la vitesse de la lumière dans le vide ?", "propositions": ["300 000 km/s", "150 000 km/s", "1 000 000 km/s", "30 000 km/s"], "bonne_reponse": 0, "niveau": "Moyen", "anecdote": "Exactement 299 792 458 mètres par seconde."},
        {"question": "Combien de joueurs sur un terrain de football (par équipe) ?", "propositions": ["9", "10", "11", "12"], "bonne_reponse": 2, "niveau": "Facile", "anecdote": "Gardien inclus, ça fait 11 joueurs par équipe."},
        {"question": "Quel est le plus petit pays du monde ?", "propositions": ["Monaco", "Vatican", "Saint-Marin", "Liechtenstein"], "bonne_reponse": 1, "niveau": "Moyen", "anecdote": "Le Vatican mesure environ 0,49 km²."},
        {"question": "Quelle est la durée d'une rotation complète de la Terre ?", "propositions": ["12 heures", "24 heures", "48 heures", "365 jours"], "bonne_reponse": 1, "niveau": "Facile", "anecdote": "Plus précisément 23h56min, le jour 'solaire' arrondit à 24h."},
        {"question": "Quel est l'élément chimique le plus abondant dans l'univers ?", "propositions": ["Oxygène", "Carbone", "Hydrogène", "Hélium"], "bonne_reponse": 2, "niveau": "Difficile", "anecdote": "L'hydrogène représente environ 75% de la masse normale de l'univers."},
        {"question": "Combien de temps dure un mandat présidentiel français ?", "propositions": ["4 ans", "5 ans", "6 ans", "7 ans"], "bonne_reponse": 1, "niveau": "Facile", "anecdote": "Le mandat est passé de 7 à 5 ans en 2000."},
    ],
    "histoire": [
        {"question": "Quelle bataille a marqué la défaite finale de Napoléon ?", "propositions": ["Austerlitz", "Trafalgar", "Waterloo", "Iéna"], "bonne_reponse": 2, "niveau": "Facile", "anecdote": "La bataille de Waterloo a eu lieu en 1815 en Belgique."},
        {"question": "En quelle année a commencé la Première Guerre mondiale ?", "propositions": ["1912", "1914", "1916", "1918"], "bonne_reponse": 1, "niveau": "Facile", "anecdote": "Elle a débuté après l'assassinat de l'archiduc François-Ferdinand."},
        {"question": "Qui était le premier empereur romain ?", "propositions": ["Jules César", "Auguste", "Néron", "Trajan"], "bonne_reponse": 1, "niveau": "Moyen", "anecdote": "Auguste a régné de 27 av. J.-C. à 14 ap. J.-C."},
        {"question": "Quelle civilisation a construit Machu Picchu ?", "propositions": ["Aztèques", "Mayas", "Incas", "Olmèques"], "bonne_reponse": 2, "niveau": "Moyen", "anecdote": "Construit au XVe siècle, redécouvert en 1911."},
    ],
    "geographie": [
        {"question": "Quelle est la capitale du Canada ?", "propositions": ["Toronto", "Vancouver", "Ottawa", "Montréal"], "bonne_reponse": 2, "niveau": "Moyen", "anecdote": "Ottawa a été choisie en 1857 comme compromis entre anglophones et francophones."},
        {"question": "Quel est le point culminant d'Europe ?", "propositions": ["Mont Blanc", "Mont Elbrouz", "Cervin", "Mont Rose"], "bonne_reponse": 1, "niveau": "Difficile", "anecdote": "L'Elbrouz, en Russie, atteint 5 642 mètres."},
        {"question": "Quel désert est le plus grand du monde ?", "propositions": ["Sahara", "Antarctique", "Gobi", "Kalahari"], "bonne_reponse": 1, "niveau": "Difficile", "anecdote": "L'Antarctique est techniquement un désert polaire, le plus vaste de tous."},
    ],
    "sport": [
        {"question": "Combien de sets faut-il gagner pour remporter un match de tennis (Grand Chelem hommes) ?", "propositions": ["2", "3", "4", "5"], "bonne_reponse": 1, "niveau": "Facile", "anecdote": "Les hommes jouent en 5 sets gagnants, les femmes en 3."},
        {"question": "Quel pays a remporté le plus de Coupes du Monde de football ?", "propositions": ["Allemagne", "Argentine", "Brésil", "Italie"], "bonne_reponse": 2, "niveau": "Facile", "anecdote": "Le Brésil compte 5 titres de champion du monde."},
        {"question": "Tous les combien d'années ont lieu les Jeux Olympiques d'été ?", "propositions": ["2 ans", "3 ans", "4 ans", "5 ans"], "bonne_reponse": 2, "niveau": "Facile", "anecdote": "Sauf exceptions historiques (guerres, Covid pour le décalage de 2020)."},
    ],
}

# ──────────────────────────────────────────
#  FONCTION PRINCIPALE
# ──────────────────────────────────────────

async def generate_activity_content(activity_type: str, extra_context: str = "", previous_questions: list = None) -> dict:
    """
    Pioche un contenu pré-écrit pour le type d'activité demandé.

    Reste une fonction `async` (et garde la même signature que l'ancienne
    version utilisant Gemini) pour ne nécessiter aucun changement côté
    `bot.py` / `minigames.py` qui l'appellent avec `await`.
    """

    if activity_type == "mais":
        return _pick(BANK_MAIS, "mais")

    if activity_type == "blindtest":
        return _pick(BANK_BLINDTEST, "blindtest")

    if activity_type == "roi_indice":
        indice = _pick([{"indice": i} for i in BANK_ROI_INDICES], "roi_indice")
        return indice

    if activity_type == "sondage_absurde":
        return _pick(BANK_SONDAGE, "sondage_absurde")

    if activity_type == "dilemme":
        return _pick(BANK_DILEMME, "dilemme")

    if activity_type == "deux_verites_mensonge_invite":
        return _pick(BANK_TVM_INVITE, "tvm_invite")

    if activity_type == "recette":
        return _pick(BANK_RECETTE, "recette")

    if activity_type == "olympiade_epreuve":
        return _pick(BANK_OLYMPIADE, "olympiade")

    if activity_type == "quiz_question":
        return _pick(BANK_QUIZ, "quiz")

    if activity_type == "champion_question":
        # extra_context contient le thème choisi (ex: "histoire")
        theme_key = (extra_context or "").strip().lower()
        bank = BANK_CHAMPION_BY_THEME.get(theme_key, BANK_CHAMPION_BY_THEME["default"])
        cache_key = f"champion_{theme_key or 'default'}"

        # Évite de repiocher une question déjà posée dans cette manche
        if previous_questions:
            filtered = [q for q in bank if q["question"] not in previous_questions]
            if filtered:
                bank = filtered

        return _pick(bank, cache_key)

    # Repli générique si un type inconnu est demandé
    return _pick(BANK_DILEMME, "dilemme")
