# ============================================================
#  Commands.py — cerveau des commandes de J.A.R.V.I.S
# ============================================================

import os
import re
import subprocess
import urllib.parse
import webbrowser
from datetime import datetime
from difflib import SequenceMatcher
from zoneinfo import ZoneInfo

import requests

from Interface.Globe.serveur_globe import demarrer_serveur, cacher_position, montrer_position
from Brain import lumieres
import config

# On lance le serveur du globe (dans un thread). À n'appeler qu'ICI.
demarrer_serveur()

# ---- Réglages généraux (lus depuis config.py) ----
username      = config.USERNAME
OPENWEATHER_API_KEY = config.OPENWEATHER_API_KEY
VILLE         = config.VILLE
OLLAMA_MODELE = config.OLLAMA_MODELE

mode_actuel = None  # mémorise le mode courant

# ---- Mémoire de conversation de l'IA ----
historique   = []
MAX_ECHANGES = 6

# Pont vers l'interface (HUD)
interface = None


def relier_interface(fonction):
    """Permet à Main de donner à Commands un moyen de parler au HUD."""
    global interface
    interface = fonction


# ============================================================
#  DICTIONNAIRES D'APPLICATIONS  (lus depuis config.py)
# ============================================================

Launchers_de_jeu = config.LAUNCHERS_JEU
Jeux             = config.JEUX
AI               = config.AI
Musique          = config.MUSIQUE
Reseaux_sociaux  = config.RESEAUX_SOCIAUX
Travail          = config.TRAVAIL

DISCORD = config.DISCORD
NETFLIX = config.NETFLIX
VSCODE  = config.VSCODE


# ============================================================
#  MODES  (ce qu'on ouvre, ce qu'on ferme, le message)
# ============================================================

APPS_MODE = {
    "travail": list(Travail.values()),
    "jeu": list(Launchers_de_jeu.values()) + [DISCORD, Musique["deezer"]],
    "cinéma": [NETFLIX],
    "codage": [VSCODE, AI["claude"], Musique["deezer"]],
}

PROCESSUS_A_FERMER = {
    "travail": ["soffice.exe", "soffice.bin"],
    "jeu": ["EpicGamesLauncher.exe", "steam.exe", "RiotClient.exe", "Discord.exe",
            "VALORANT.exe", "LeagueClient.exe", "RocketLeague.exe"],
    "cinéma": [],
    "codage": ["Code.exe"],
}

MESSAGES_MODE = {
    "travail": "Mode travail activé. Je ne vous dérangerai plus que pour les tâches importantes.",
    "jeu": "Mode jeu activé. Amusez-vous bien !",
    "cinéma": "Mode cinéma activé. Installez-vous confortablement !",
    "codage": "Mode codage activé. Bonne session de programmation !",
}


def fermer_processus(noms):
    """Ferme une liste de programmes par leur nom .exe."""
    for nom in noms:
        subprocess.run(["taskkill", "/F", "/IM", nom],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def activer_mode(nouveau_mode):
    """Ferme les applis du mode précédent, puis ouvre celles du nouveau."""
    global mode_actuel
    if mode_actuel in PROCESSUS_A_FERMER:
        fermer_processus(PROCESSUS_A_FERMER[mode_actuel])
    for chemin in APPS_MODE[nouveau_mode]:
        try:
            os.startfile(chemin)
        except Exception as e:
            print(f"Impossible d'ouvrir {chemin} : {e}")
    mode_actuel = nouveau_mode
    if interface:
        interface(f"setMode('{nouveau_mode}')")   # colore le HUD selon le mode
    # Synchro lumières : toute la pièce change de couleur avec le mode
    try:
        lumieres.appliquer_mode(nouveau_mode)
    except Exception as e:
        print(f"[lumières mode] {e}")
    return MESSAGES_MODE[nouveau_mode]


# ============================================================
#  FONCTIONS DE BASE
# ============================================================

def dire_heure():
    return datetime.now().strftime("Il est %H heures %M.")


# Villes connues -> fuseau horaire IANA (clés en minuscules : la commande l'est aussi).
# Pour en ajouter une : "nom en minuscule": "Zone/Ville".
FUSEAUX = {
    "toulon":      "Europe/Paris",
    "paris":       "Europe/Paris",
    "reykjavik":   "Atlantic/Reykjavik",
    "queenstown":  "Pacific/Auckland",
    "new york":    "America/New_York",
    "tokyo":       "Asia/Tokyo",
    "londres":     "Europe/London",
    "los angeles": "America/Los_Angeles",
    "sydney":      "Australia/Sydney",
}


def heure_ville(commande):
    """Si une ville connue est citée, renvoie (nom, 'HH heures MM'). Sinon None."""
    for ville, tz in FUSEAUX.items():
        if ville in commande:
            heure = datetime.now(ZoneInfo(tz)).strftime("%H heures %M")
            return ville, heure
    return None


def dire_date():
    return datetime.now().strftime("Nous sommes le %d/%m/%Y.")


def get_weather(ville=None):
    v = ville or VILLE
    url = (f"https://api.openweathermap.org/data/2.5/weather"
           f"?q={v}&appid={OPENWEATHER_API_KEY}&units=metric&lang=fr")
    try:
        data = requests.get(url, timeout=5).json()
        if data.get("cod") != 200:
            return "Je n'ai pas pu récupérer la météo."
        desc = data["weather"][0]["description"]
        temp = round(data["main"]["temp"])
        feels = round(data["main"]["feels_like"])
        hum = data["main"]["humidity"]
        wind = round(data["wind"]["speed"] * 3.6)
        return (f"À {v} il fait {temp}°C, ressenti {feels}°C, {desc}. "
                f"Humidité {hum}%, vent {wind} km/h.")
    except Exception as e:
        return f"Impossible de récupérer la météo pour l'instant : {e}"


def fuzzy_match(mot, cible, seuil=0.6):
    """True si 'mot' ressemble assez à 'cible' (reconnaissance vocale imparfaite)."""
    return SequenceMatcher(None, mot, cible).ratio() >= seuil


def chercher_sur_google(terme):
    url = f"https://www.google.com/search?q={urllib.parse.quote(terme)}"
    webbrowser.open(url)
    return f"Voici les résultats pour {terme} sur Google."


def demander_ia(question):
    """Pose une question à l'IA locale (Ollama), avec mémoire et contexte."""
    global historique
    try:
        # 1) on construit la liste des messages : système + historique + nouvelle question
        messages = [{"role": "system", "content": construire_prompt_systeme()}]
        messages += historique
        messages.append({"role": "user", "content": question})

        # 2) on interroge Ollama
        r = requests.post("http://localhost:11434/api/chat", json={
            "model": OLLAMA_MODELE,
            "messages": messages,
            "stream": False,
            "keep_alive": "30m",
            "options": {"temperature": 0.7, "num_ctx": 2048},
        }, timeout=120)

        reponse = nettoyer_reponse(r.json()["message"]["content"])

        # 3) on mémorise l'échange, puis on ne garde que les plus récents
        historique.append({"role": "user", "content": question})
        historique.append({"role": "assistant", "content": reponse})
        historique = historique[-(MAX_ECHANGES * 2):]

        return reponse
    except Exception as e:
        return f"L'IA n'est pas disponible : {e}"


# Noms français des jours/mois (évite les soucis de locale sous Windows)
_JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
_MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
         "août", "septembre", "octobre", "novembre", "décembre"]


def construire_prompt_systeme():
    """Prompt système contextualisé : qui, quand, où, quel mode."""
    n = datetime.now()
    date_fr = f"{_JOURS[n.weekday()]} {n.day} {_MOIS[n.month - 1]} {n.year}"
    mode = mode_actuel if mode_actuel else "aucun"
    return (
        f"Tu es JARVIS, l'assistant vocal personnel de {username}. "
        "Tu réponds toujours en français, sur un ton naturel, poli et un peu complice. "
        "Tes réponses sont COURTES (1 à 3 phrases) car elles sont lues à voix haute : "
        "jamais de listes, d'astérisques, de mise en forme ni d'emoji. "
        "Si tu ne sais pas, dis-le simplement plutôt que d'inventer. "
        f"Contexte : nous sommes {date_fr}, il est {n.strftime('%H heures %M')}. "
        f"{username} se trouve à {VILLE}. Mode actif : {mode}."
    )


def nettoyer_reponse(texte):
    """Retire la mise en forme Markdown pour une lecture vocale propre."""
    texte = re.sub(r"(?m)^\s*[-*•]+\s+", "", texte)      # puces "- " "* " "• " en début de ligne
    texte = re.sub(r"[*_`#>]+", "", texte)               # **gras** *ital* `code` # > ...
    texte = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", texte)     # [texte](lien) -> texte
    texte = re.sub(r"\s+", " ", texte)                   # espaces/sauts multiples
    return texte.strip()


def reinitialiser_memoire():
    """Vide la mémoire de conversation (nouvelle discussion)."""
    global historique
    historique = []
    return "C'est noté, je repars de zéro."


# ============================================================
#  OUVERTURE D'APPLICATIONS
# ============================================================

def ouvrir_depuis(dico, cmd):
    """Cherche une appli du dictionnaire dans la commande et l'ouvre."""
    for nom, chemin in dico.items():
        if nom in cmd:                       # cmd est déjà en minuscules
            try:
                os.startfile(chemin)
                return f"Ouverture de {nom}."
            except Exception as e:
                return f"Impossible d'ouvrir {nom} : {e}"
    return None


def trouver_chemin_spotify():
    for chemin in config.SPOTIFY_CHEMINS:
        if os.path.exists(chemin):
            return chemin
    return None


def ouvrir_spotify():
    """Ouvre Spotify de plusieurs façons jusqu'à ce que l'une marche."""
    chemin = trouver_chemin_spotify()
    if chemin:
        try:
            os.startfile(chemin)
            return "Ouverture de Spotify."
        except Exception as e:
            print(f"Erreur avec le chemin direct : {e}")
    try:
        os.startfile("spotify://")
        return "Ouverture de Spotify."
    except Exception:
        pass
    try:
        subprocess.Popen(["start", "spotify"], shell=True)
        return "Lancement de Spotify..."
    except Exception:
        pass
    try:
        import winreg
        hkey = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"spotify\shell\open\command")
        path, _ = winreg.QueryValueEx(hkey, "")
        if path:
            subprocess.Popen(path.split('"')[1])
            return "Ouverture de Spotify."
    except Exception:
        pass
    return "Spotify introuvable. Vérifiez l'installation."


def ouvrir_globe():
    cacher_position()
    subprocess.Popen([config.CHROME, "--app=http://127.0.0.1:5000/"])
    return "J'ouvre le système de navigation."


def afficher_position():
    montrer_position()                 # le globe déjà ouvert l'affichera tout seul
    return "J'affiche votre position."


def ouvrir_netflix():
    os.startfile(NETFLIX)
    return "Ouverture de Netflix."


# ============================================================
#  LUMIÈRES — fonctions d'aide pour le dispatch vocal
# ============================================================

def _trouver_couleur(cmd):
    """Cherche un nom de couleur connu dans la phrase. Renvoie le nom ou None."""
    for nom in lumieres.COULEURS:
        if nom in cmd:
            return nom
    return None


def _trouver_appareil(cmd):
    """Cherche un nom d'ampoule/LED connu dans la phrase. Renvoie le nom ou None."""
    # On essaie d'abord les noms les plus longs (pour que "leds bureau" matche avant "bureau")
    for nom in sorted(lumieres.AMPOULES, key=len, reverse=True):
        if nom in cmd:
            return nom
    return None


def _gerer_lumiere(cmd):
    """Gère les commandes du type 'allume/éteins la chambre en rouge'."""
    appareil = _trouver_appareil(cmd)
    couleur_nom = _trouver_couleur(cmd)
    eteindre = "éteins" in cmd or "eteins" in cmd or "coupe" in cmd

    if not appareil:
        # Pas d'appareil précis → on applique à tout
        if eteindre:
            lumieres.eteindre_tout()
            return "Lumières éteintes."
        lumieres.allumer_tout(couleur_nom)
        if couleur_nom:
            return f"Lumières en {couleur_nom}."
        return "Lumières allumées."

    if eteindre:
        lumieres.eteindre(appareil)
        return f"{appareil.title()} éteinte."

    lumieres.allumer(appareil, couleur_nom)
    if couleur_nom:
        return f"{appareil.title()} allumée en {couleur_nom}."
    return f"{appareil.title()} allumée."


# ============================================================
#  AIGUILLAGE DES COMMANDES
# ============================================================

def traiter_commande(commande, parler_fn=None):
    cmd = commande.lower() if commande else ""
    if not cmd:
        return "Commande vide."

    # --- Infos ---
    if "heure" in cmd:
        trouve = heure_ville(cmd)
        if trouve:
            nom, heure = trouve
            if interface:
                interface(f"afficherHeure('{nom}')")   # surligne la ville dans le HUD
            return f"À {nom.title()}, il est {heure}."
        return dire_heure()
    elif "position" in cmd or "où suis" in cmd:
        return afficher_position()
    elif "globe" in cmd or "navigation" in cmd or "terre" in cmd:
        return ouvrir_globe()
    elif "date" in cmd or "quel jour" in cmd:
        return dire_date()
    elif "météo" in cmd or "quel temps" in cmd:
        return get_weather()
    elif "oublie tout" in cmd or "nouvelle conversation" in cmd or "on recommence" in cmd:
        return reinitialiser_memoire()

    # --- Modes ---
    elif "mode travail" in cmd or "au boulot" in cmd:
        return activer_mode("travail")
    elif "mode jeu" in cmd or "je veux jouer" in cmd or "on joue" in cmd:
        return activer_mode("jeu")
    elif "film" in cmd or "série" in cmd or "mode cinéma" in cmd:
        return activer_mode("cinéma")
    elif "mode codage" in cmd or "coder" in cmd:
        return activer_mode("codage")

    # --- Lumières ---
    # On vérifie qu'il y a un vrai verbe d'action pour éviter les faux positifs
    # ("dans la lumière", "une lumière" etc. ne doivent pas déclencher)
    VERBES_ALLUMER = ["allume", "mets", "met", "active", "ouvre"]
    VERBES_ETEINDRE = ["éteins", "eteins", "coupe", "ferme", "désactive", "desactive", "éteindre", "eteindre"]
    MOTS_LUMIERE = ["lumière", "lumiere", "lumières", "lumieres", "led", "leds",
                    "chambre", "bureau", "leds bureau", "leds lit"]

    a_verbe_allumer  = any(v in cmd for v in VERBES_ALLUMER)
    a_verbe_eteindre = any(v in cmd for v in VERBES_ETEINDRE)
    a_mot_lumiere    = any(m in cmd for m in MOTS_LUMIERE)
    a_tout           = "tout" in cmd

    if (a_verbe_allumer or a_verbe_eteindre) and (a_mot_lumiere or a_tout):
        # "éteins tout" / "coupe tout"
        if a_verbe_eteindre and ("tout" in cmd or not _trouver_appareil(cmd)):
            lumieres.eteindre_tout()
            return "Lumières éteintes."
        # "allume tout" / "allume les lumières"
        if a_verbe_allumer and ("tout" in cmd or not _trouver_appareil(cmd)):
            couleur_trouvee = _trouver_couleur(cmd)
            lumieres.allumer_tout(couleur_trouvee)
            return f"Lumières allumées en {couleur_trouvee}." if couleur_trouvee else "Lumières allumées."
        # Appareil précis
        return _gerer_lumiere(cmd)

    # Couleur seule sans verbe explicite : "lumière rouge", "mets en bleu"
    elif a_mot_lumiere and _trouver_couleur(cmd):
        return _gerer_lumiere(cmd)

    # --- Spotify (reconnaissance vocale imparfaite) ---
    elif any(var in cmd for var in ["spotify", "spotifaille", "spotifai", "faille"]) \
            or fuzzy_match(cmd, "spotify", 0.5):
        return ouvrir_spotify()

    # --- Recherche Google ---
    elif "recherche" in cmd or "cherche" in cmd:
        terme = (cmd.replace("recherche", "").replace("cherche", "")
                    .replace("sur google", "").replace("google", "").strip())
        return chercher_sur_google(terme) if terme else "Quel terme voulez-vous que je cherche ?"

    # --- Applications : on cherche dans tous les dictionnaires ---
    for dico in (AI, Launchers_de_jeu, Jeux, Musique, Reseaux_sociaux):
        resultat = ouvrir_depuis(dico, cmd)
        if resultat:
            return resultat

    # --- Sinon : on laisse l'IA répondre ---
    return demander_ia(commande)