# ============================================================
#  config.py — TOUT CE QUI EST SPÉCIFIQUE À TA MACHINE
#
#  C'est le SEUL fichier à modifier pour adapter JARVIS
#  à un nouvel ordinateur ou un nouvel utilisateur.
#  Les autres fichiers (.py) n'ont pas besoin d'être touchés.
# ============================================================

import os

# ---- Ton prénom (affiché au lancement) ----
USERNAME = "Ton prenom / username"

# ---- Ta ville (pour la météo) ----
VILLE = "Ta Ville"

# ---- Clé API OpenWeather (météo) ----
# Gratuite sur https://openweathermap.org/api
OPENWEATHER_API_KEY = "TA_CLE_API_OPENWEATHER"

# ---- Modèle IA local (Ollama) ----
# Vérifie avec : ollama ps -> doit afficher "100% GPU"
# Conseils selon ta carte graphique :
#   4 Go VRAM  -> "qwen2.5:3b"   (rapide + bon en français)
#   6 Go VRAM  -> "mistral:7b"   (plus intelligent)
#   8 Go VRAM  -> "llama3.1:8b"  (le meilleur)
OLLAMA_MODELE = "qwen2.5:3b"    """Cest moi jte dis, jte conseil de prendre llama3.1:8b vu ton pc il tournera bien et l'ia sera vraiment puissante """ 

# ---- Nom d'utilisateur Windows ----
# Ouvre un terminal et tape : echo %USERNAME%
WIN_USER = "lerou"

# ============================================================
#  CHEMINS DES APPLICATIONS
#  Pour chaque appli, mets le chemin vers son .exe ou son .lnk
#  Si tu n'as pas une appli, laisse le chemin tel quel
#  (ça ne plantera pas, juste la commande ne fera rien).
# ============================================================

def _u(chemin):
    """Remplace {USER} par ton nom d'utilisateur Windows."""
    return chemin.replace("{USER}", WIN_USER)


# --- Jeux ---
LAUNCHERS_JEU = {
    "epic games": r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
    "steam":      r"C:\Program Files (x86)\Steam\steam.exe",
    "riot games": r"C:\Program Files (x86)\Riot Games\Riot Client\RiotClient.exe",
}

JEUX = {
    "fortnite":           r"C:\Program Files (x86)\Epic Games\Fortnite\FortniteGame\Binaries\Win64\FortniteClient-Win64-Shipping.exe",
    "valorant":           r"C:\Program Files (x86)\Riot Games\VALORANT\live\VALORANT.exe",
    "teamfight tactics":  r"C:\Program Files (x86)\Riot Games\Teamfight Tactics\live\TeamfightTactics.exe",
    "rocket league":      r"C:\Program Files (x86)\Steam\steamapps\common\rocketleague\rocketleague.exe",
    "league of legends":  r"C:\Program Files (x86)\Riot Games\League of Legends\LeagueClient.exe",
}

# --- IA ---
AI = {
    "chatgpt": _u(r"C:\Users\{USER}\Desktop\ChatGPT - Raccourci.lnk"),
    "claude":  _u(r"C:\Users\{USER}\Desktop\Claude - Raccourci.lnk"),
    "grok":    _u(r"C:\Users\{USER}\Desktop\Grok - Raccourci.lnk"),
    "ollama":  _u(r"C:\Users\{USER}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Ollama.lnk"),
}

# --- Musique ---
MUSIQUE = {
    "spotify":     _u(r"C:\Users\{USER}\AppData\Roaming\Spotify\Spotify.exe"),
    "deezer":      _u(r"C:\Users\{USER}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Applications Chrome\Deezer.lnk"),
    "apple music": _u(r"C:\Users\{USER}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Applications Chrome\Apple Music.lnk"),
}

# --- Réseaux sociaux ---
RESEAUX_SOCIAUX = {
    "instagram": _u(r"C:\Users\{USER}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Applications Chrome\Instagram.lnk"),
    "snapchat":  _u(r"C:\Users\{USER}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Applications Chrome\Snapchat.lnk"),
    "tiktok":    _u(r"C:\Users\{USER}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Applications Chrome\TikTok.lnk"),
}

# --- Travail ---
TRAVAIL = {
    "pronote":      _u(r"C:\Users\{USER}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Applications Chrome\Pronote.lnk"),
    "claude":       _u(r"C:\Users\{USER}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Applications Chrome\Claude.lnk"),
    "deezer":       _u(r"C:\Users\{USER}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Applications Chrome\Deezer.lnk"),
    "libre office": r"C:\Program Files\LibreOffice\program\soffice.exe",
}

# --- Raccourcis seuls ---
DISCORD = _u(r"C:\Users\{USER}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Discord Inc\Discord.lnk")
NETFLIX = _u(r"C:\Users\{USER}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Applications Chrome\Netflix.lnk")
VSCODE  = _u(r"C:\Users\{USER}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Applications Chrome\Visual Studio Code.lnk")

# --- Spotify (chemins de fallback) ---
SPOTIFY_CHEMINS = [
    _u(r"C:\Users\{USER}\AppData\Roaming\Spotify\Spotify.exe"),
    r"C:\Program Files\Spotify\Spotify.exe",
    r"C:\Program Files (x86)\Spotify\Spotify.exe",
    _u(r"C:\Users\{USER}\AppData\Local\Microsoft\WindowsApps\Spotify.exe"),
]

# --- Chrome (pour le globe) ---
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"