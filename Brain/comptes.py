# ============================================================
#  comptes.py — petite gestion de comptes locale pour JARVIS
#  Les mots de passe ne sont JAMAIS stockés en clair : on garde
#  seulement un "hash" (empreinte) + un "sel" aléatoire par compte.
# ============================================================

import hashlib
import json
import os

# comptes.json à la racine du projet (un cran au-dessus de Brain/)
FICHIER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "comptes.json")


def _charger():
    if os.path.exists(FICHIER):
        try:
            with open(FICHIER, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _sauver(comptes):
    with open(FICHIER, "w", encoding="utf-8") as f:
        json.dump(comptes, f, ensure_ascii=False, indent=2)


def _hacher(mdp, sel):
    return hashlib.sha256((sel + mdp).encode("utf-8")).hexdigest()


def creer_compte(nom, mdp):
    nom = (nom or "").strip().lower()
    if not nom or not mdp:
        return {"ok": False, "message": "Identifiant et mot de passe requis."}
    comptes = _charger()
    if nom in comptes:
        return {"ok": False, "message": "Ce compte existe déjà."}
    sel = os.urandom(8).hex()
    comptes[nom] = {"sel": sel, "hash": _hacher(mdp, sel)}
    _sauver(comptes)
    return {"ok": True, "message": "Compte créé."}


def connexion(nom, mdp):
    nom = (nom or "").strip().lower()
    comptes = _charger()
    compte = comptes.get(nom)
    if not compte:
        return {"ok": False, "message": "Compte introuvable."}
    if _hacher(mdp, compte["sel"]) != compte["hash"]:
        return {"ok": False, "message": "Mot de passe incorrect."}
    return {"ok": True, "message": "Connexion réussie."}