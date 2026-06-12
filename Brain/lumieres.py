# ============================================================
#  lumieres.py — pilotage des ampoules / LED Tapo
#
#  À remplir : Email, Mdp, et les IP dans AMPOULES.
#  Install : pip install tapo
#
#  Librairie : https://github.com/mihai-dinculescu/tapo
#  Important : dans l'appli Tapo, active "Compatibilité tierce"
#              (réglages > compte) sinon Python sera refusé.
# ============================================================

import asyncio
import colorsys

from tapo import ApiClient

# ---- À REMPLIR (ton compte TP-Link / appli Tapo) ----
Email = "TON_EMAIL@MAIL.COM"
Mdp   = "TON_MOT_DE_PASSE"

# ---- Tes appareils : nom -> (IP locale fixée dans la box, type) ----
#   type : "l530" = ampoule couleur E27
#          "l920" ou "l930" = bandeau LED
#          "p100" = prise connectée (on/off seulement)
AMPOULES = {
    "chambre":     ("192.168.1.50", "l530"),
    "bureau":      ("192.168.1.51", "l530"),
    "leds bureau": ("192.168.1.52", "l920"),
    "leds lit":    ("192.168.1.53", "l920"),
}

# ---- Couleurs : nom -> (R, G, B) ----
COULEURS = {
    "blanc":   (255, 255, 255),
    "rouge":   (255, 0, 0),
    "bleu":    (0, 0, 255),
    "cyan":    (0, 255, 255),
    "magenta": (255, 0, 255),
    "orange":  (255, 165, 0),
    "vert":    (0, 255, 0),
    "violet":  (160, 60, 255),
    "rose":    (255, 100, 180),
}

# ---- Couleurs liées aux modes (synchro automatique) ----
COULEURS_MODES = {
    "aucun":   "rouge",
    "travail": "orange",
    "jeu":     "violet",
    "codage":  "cyan",
    "cinéma":  "rose",
}

LUMINOSITE = 100   # toujours à fond


# ============================================================
#  Fonctions internes (async, cachées)
# ============================================================

def _rgb_vers_hs(r, g, b):
    """Convertit RGB en (teinte 0-360, saturation 1-100) pour Tapo."""
    h, s, _ = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return round(h * 360), max(1, round(s * 100))


async def _connecter(nom):
    """Se connecte à l'appareil 'nom' avec la bonne méthode selon son type."""
    ip, type_appareil = AMPOULES[nom]
    client = ApiClient(Email, Mdp)
    return await getattr(client, type_appareil)(ip)


async def _allumer(nom, couleur_nom=None):
    appareil = await _connecter(nom)
    await appareil.on()
    _, type_appareil = AMPOULES[nom]
    # Les prises P100 n'ont ni couleur ni luminosité
    if type_appareil == "p100":
        return
    await appareil.set_brightness(LUMINOSITE)
    if couleur_nom and couleur_nom in COULEURS:
        r, g, b = COULEURS[couleur_nom]
        if r == g == b:    # blanc -> température de couleur
            await appareil.set_color_temperature(4000)
        else:
            teinte, saturation = _rgb_vers_hs(r, g, b)
            await appareil.set_hue_saturation(teinte, saturation)


async def _eteindre(nom):
    appareil = await _connecter(nom)
    await appareil.off()


# ============================================================
#  Fonctions publiques (synchrones) — à appeler depuis Commands.py
# ============================================================

def allumer(nom, couleur=None):
    """Allume une ampoule (luminosité 100 %), avec une couleur optionnelle."""
    try:
        asyncio.run(_allumer(nom, couleur))
    except Exception as e:
        print(f"[lumière] Erreur {nom} : {e}")


def eteindre(nom):
    """Éteint une ampoule."""
    try:
        asyncio.run(_eteindre(nom))
    except Exception as e:
        print(f"[lumière] Erreur {nom} : {e}")


def couleur(nom, nom_couleur):
    """Change la couleur d'une ampoule (l'allume si elle était éteinte)."""
    allumer(nom, nom_couleur)


def allumer_tout(couleur_nom=None):
    """Allume toutes les ampoules (même couleur optionnelle)."""
    for nom in AMPOULES:
        allumer(nom, couleur_nom)


def eteindre_tout():
    """Éteint toutes les ampoules."""
    for nom in AMPOULES:
        eteindre(nom)


def appliquer_mode(mode):
    """Synchro : met toutes les lumières à la couleur du mode."""
    couleur_nom = COULEURS_MODES.get(mode)
    if couleur_nom:
        allumer_tout(couleur_nom)