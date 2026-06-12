# ============================================================
#  serveur_globe.py — le "tableau blanc" partagé entre Python et la page web
# ============================================================

import os
import threading

from flask import Flask, jsonify, send_file

app = Flask(__name__)

# Chemin relatif : Earth3D.html est dans le même dossier que ce fichier
GLOBE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Earth3D.html")

# État partagé : la page le consulte toutes les 0,4 s
etat = {"position": False}


@app.route("/")
def page():
    return send_file(GLOBE)          # sert le globe


@app.route("/etat")
def lire_etat():
    return jsonify(etat)             # la page lit ça en continu


def demarrer_serveur():
    """Lance le serveur dans un thread, pour ne pas bloquer l'assistant."""
    threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=5000,
                               debug=False, use_reloader=False),
        daemon=True,
    ).start()


# Fonctions appelées par l'assistant
def montrer_position():
    etat["position"] = True


def cacher_position():
    etat["position"] = False