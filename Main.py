# ============================================================
#  Main.py — point d'entrée de J.A.R.V.I.S
# ============================================================
#
#  Au lancement (mode vocal), Main ouvre le HUD dans une fenêtre
#  (pywebview) et fait tourner l'écoute dans un thread d'arrière-plan.
#  Les deux communiquent : la boucle vocale "pousse" ce qu'elle entend
#  et ce que JARVIS répond vers le HUD, via fenetre.evaluate_js(...).
#
#  Règle d'or de pywebview : l'interface DOIT occuper le thread
#  principal. C'est donc la boucle vocale qui part dans un thread.
# ============================================================

import argparse
import os
import sys
import threading

from Brain import Commands
from Brain.Commands import traiter_commande as handle_command


STOP_COMMANDS = {
    "arrete", "arrête", "stop", "quit", "exit",
    "ferme", "ferme jarvis", "arrete jarvis", "arrête jarvis",
}

# Mot d'activation. Vosk peut mal entendre un prénom anglais : on accepte des variantes.
# Important : de la PLUS LONGUE à la plus courte (sinon "jarvis" attrape "jarvisse").
MOTS_CLE = ["jarvisse", "jarviss", "jarvis", "jervis"]


def trouver_mot_cle(phrase):
    """Renvoie (position, longueur) du mot-clé dans la phrase, ou (-1, 0) si absent."""
    bas = phrase.lower()
    for mot in MOTS_CLE:
        i = bas.find(mot)
        if i != -1:
            return i, len(mot)
    return -1, 0


# Référence vers la fenêtre du HUD (remplie au lancement). Reste None en mode texte.
fenetre = None


# ------------------------------------------------------------
#  Communication avec le HUD
# ------------------------------------------------------------
def _js_escape(texte):
    """Protège un texte pour l'insérer dans une chaîne JavaScript entre apostrophes."""
    return (texte or "").replace("\\", "\\\\").replace("'", "\\'") \
                        .replace("\n", " ").replace("\r", " ")


def hud(code_js):
    """Exécute du JavaScript dans le HUD. Sans effet si le HUD n'est pas ouvert (mode texte)."""
    if fenetre is not None:
        try:
            fenetre.evaluate_js(code_js)
        except Exception:
            pass


# ------------------------------------------------------------
#  Parole / traitement d'une commande
# ------------------------------------------------------------
def speak_terminal(text):
    print(f"Jarvis : {text}")


def safe_speak(text, voice_speaker=None):
    print(f"Jarvis : {text}")
    if voice_speaker is None:
        return
    try:
        voice_speaker(text)
    except Exception as exc:
        print(f"[voix indisponible] {exc}")


def process_command(text, voice_speaker=None):
    command = (text or "").strip()
    if not command:
        return True

    if command.lower() in STOP_COMMANDS:
        safe_speak("Arrêt de Jarvis.", voice_speaker)
        return False

    print(f"Toi : {command}")
    hud(f"vousDire('{_js_escape(command)}')")
    hud("setEtat('reflexion')")

    try:
        response = handle_command(command, parler_fn=voice_speaker or speak_terminal)
    except Exception as exc:
        response = f"Erreur pendant la commande : {exc}"

    if response:
        hud(f"jarvisDire('{_js_escape(response)}')")
        safe_speak(response, voice_speaker)

    return True


# ------------------------------------------------------------
#  Mode texte (clavier) — pour tester sans micro ni HUD
# ------------------------------------------------------------
def run_text_mode():
    print("=== JARVIS - mode texte ===")
    print("Tape une commande, ou 'exit' pour quitter.")
    running = True
    while running:
        try:
            running = process_command(input("> "))
        except (KeyboardInterrupt, EOFError):
            print()
            running = False


# ------------------------------------------------------------
#  Boucle vocale — tourne dans un thread, à côté du HUD
# ------------------------------------------------------------
def boucle_vocale():
    print("=== JARVIS - mode vocal ===")
    try:
        from Brain.voice import ecouter, parler, user
    except Exception as exc:
        print(f"Impossible de lancer le micro/la voix : {exc}")
        return

    # Salutation dès le lancement
    safe_speak(f"Bonjour {user}. Dites mon nom quand vous avez besoin de moi.", parler)
    hud(f"jarvisDire('Bonjour {_js_escape(user)}. Dites « Jarvis » pour m\\'activer.')")

    running = True
    while running:
        try:
            # 1) En veille : on attend d'entendre le mot-clé.
            hud("setEtat('veille')")
            phrase = ecouter()
            position, longueur = trouver_mot_cle(phrase or "")
            if position == -1:
                continue                       # pas de "Jarvis" -> on ignore

            # 2) Mot-clé entendu : on prend ce qui suit comme commande.
            commande = phrase[position + longueur:].strip(" ,.!?")
            hud("setEtat('ecoute')")

            # 3) Si l'utilisateur a juste dit "Jarvis", on attend la commande.
            if not commande:
                safe_speak("Oui ?", parler)
                commande = ecouter()

            running = process_command(commande, voice_speaker=parler)
        except KeyboardInterrupt:
            running = False
        except Exception as exc:
            print(f"Erreur micro : {exc}")
            print("Je relance l'écoute.")

    safe_speak("À bientôt.", parler)
    # On ferme la fenêtre proprement à la sortie
    if fenetre is not None:
        try:
            fenetre.destroy()
        except Exception:
            pass


# Empêche de lancer la boucle vocale deux fois (après connexion).
voix_demarree = False


# ------------------------------------------------------------
#  Pont JS -> Python : ce que le HUD peut appeler
#  (depuis le HUD : window.pywebview.api.<methode>(...))
# ------------------------------------------------------------
class PontJS:
    def connexion(self, nom, mdp):
        """Vérifie un compte existant. Renvoie {ok, message} au HUD."""
        from Brain import comptes
        return comptes.connexion(nom, mdp)

    def creer_compte(self, nom, mdp):
        """Crée un nouveau compte. Renvoie {ok, message} au HUD."""
        from Brain import comptes
        return comptes.creer_compte(nom, mdp)

    def demarrer(self):
        """Appelé après une connexion réussie : lance l'écoute vocale."""
        global voix_demarree
        if not voix_demarree:
            voix_demarree = True
            threading.Thread(target=boucle_vocale, daemon=True).start()
        return True

    def stop_parole(self):
        """Coupe la parole en cours quand on clique sur le bouton du HUD."""
        try:
            from Brain.voice import stopper_parole
            stopper_parole()
        except Exception as exc:
            print(f"[stop parole] {exc}")
        return True


# ------------------------------------------------------------
#  Températures CPU / GPU poussées vers le HUD
# ------------------------------------------------------------
def boucle_stats():
    """Toutes les 3 s, lit les températures et les envoie au HUD."""
    try:
        import pythoncom          # nécessaire pour lire le WMI dans un thread
        pythoncom.CoInitialize()
    except Exception:
        pass
    import time
    from Brain import stats
    while True:
        cpu = stats.temp_cpu()
        gpu = stats.temp_gpu()
        cpu_txt = f"{cpu}\u00b0C" if cpu is not None else "--"
        gpu_txt = f"{gpu}\u00b0C" if gpu is not None else "--"
        hud(f"setStats('{cpu_txt}', '{gpu_txt}')")
        time.sleep(3)


# ------------------------------------------------------------
#  Lancement avec l'interface HUD
# ------------------------------------------------------------
def lancer_avec_hud():
    global fenetre
    try:
        import webview
    except ImportError:
        print("pywebview n'est pas installé.  ->  pip install pywebview")
        print("Démarrage en mode vocal SANS interface.")
        boucle_vocale()
        return

    chemin_hud = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Interface", "Interface.html")

    # Choix de l'écran : le 2e s'il existe, sinon le principal.
    # Si ce n'est pas le bon, regarde la liste affichée et change l'index [1].
    ecrans = webview.screens
    print(f"Écrans détectés : {len(ecrans)} -> {ecrans}")
    ecran = ecrans[1] if len(ecrans) > 1 else ecrans[0]

    fenetre = webview.create_window(
        "J.A.R.V.I.S",
        chemin_hud,
        js_api=PontJS(),          # login, démarrage voix, stop parole
        fullscreen=True,          # plein écran total
        screen=ecran,             # sur le 2e moniteur
        width=1280,
        height=820,
    )
    # On donne à Commands un moyen de parler au HUD (ex: changer la couleur du mode).
    Commands.relier_interface(hud)
    # Les températures tournent tout de suite (thread d'arrière-plan).
    threading.Thread(target=boucle_stats, daemon=True).start()
    # L'écoute vocale, elle, NE démarre qu'après connexion (PontJS.demarrer).
    webview.start()


# ------------------------------------------------------------
#  Point d'entrée
# ------------------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(description="Assistant Jarvis.")
    parser.add_argument("--text", action="store_true", help="utiliser le clavier au lieu du micro (sans HUD)")
    parser.add_argument("--once", help="executer une seule commande puis quitter")
    args = parser.parse_args(argv)

    if args.once:
        process_command(args.once)
        return 0

    if args.text:
        run_text_mode()
    else:
        lancer_avec_hud()

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))