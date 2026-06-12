# J.A.R.V.I.S — Guide d'installation

Assistant vocal personnel avec interface futuriste, IA locale, contrôle de lumières et bien plus.

---

## Structure du projet

```
1.JARVIS/
├── Main.py              → point d'entrée, lancer avec : python Main.py
├── config.py            ← ⚠️ SEUL FICHIER À MODIFIER (tes chemins/applis)
├── README.md            → ce guide
├── requirements.txt     → dépendances Python
├── comptes.json         → se crée tout seul à la 1re inscription
│
├── Brain/               → le cerveau (le code Python)
│   ├── Commands.py      → toutes les commandes vocales
│   ├── voice.py         → micro + voix
│   ├── lumieres.py      → ampoules Tapo
│   ├── comptes.py       → login
│   └── stats.py         → températures CPU/GPU
│
├── Interface/           → tout ce qui s'affiche
│   ├── jarvis_hud.html  → l'interface visuelle
│   └── Globe/
│       ├── Earth3D.html → globe 3D
│       └── serveur_globe.py
│
└── Model/               → modèle de reconnaissance vocale (à télécharger)
    └── vosk-model-small-fr-0.22/
```

---

## Étape 1 — Python

Installe **Python 3.12** (pas la 3.14, elle est encore en beta) :
→ https://www.python.org/downloads/release/python-31210/
→ Prends « Windows installer (64-bit) »
→ ⚠️ **Coche ABSOLUMENT « Add Python to PATH »** avant de cliquer Installer

Vérifie ensuite dans un terminal :
```
python --version
```
Doit afficher `Python 3.12.x`.

---

## Étape 2 — Dépendances Python

Dans le dossier du projet, ouvre un terminal et lance :
```
pip install -r requirements.txt
```

---

## Étape 3 — Modèle de reconnaissance vocale (Vosk)

1. Télécharge le modèle français **vosk-model-small-fr-0.22** ici :
   → https://alphacephei.com/vosk/models
2. Dézippe-le
3. Place le dossier `vosk-model-small-fr-0.22` dans le dossier `Model/` du projet

Structure finale :
```
Model/
└── vosk-model-small-fr-0.22/
    ├── am/
    ├── conf/
    └── ...
```

⚠️ Attention : ne pas avoir un double dossier (`Model/vosk-model-small-fr-0.22/vosk-model-small-fr-0.22/`)

---

## Étape 4 — Ollama (IA locale)

1. Télécharge et installe Ollama : https://ollama.com
2. Une fois installé, ouvre un terminal et télécharge le modèle :
   ```
   ollama pull qwen2.5:3b
   ```
3. Pour vérifier que l'IA répond :
   ```
   ollama run qwen2.5:3b "dis bonjour en une phrase"
   ```
4. Ollama doit tourner en arrière-plan quand tu utilises JARVIS.
   Vérifie sur : http://localhost:11434 → doit afficher « Ollama is running »

---

## Étape 5 — LibreHardwareMonitor (températures CPU)

Pour afficher la température du CPU sur le HUD :

1. Télécharge **LibreHardwareMonitor** :
   → https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases
   → Prends le dernier `.zip`
2. Dézippe où tu veux
3. Lance `LibreHardwareMonitor.exe` en **clic droit → Exécuter en tant qu'administrateur**
4. Laisse-le tourner en fond (réduit dans la barre des tâches)

Optionnel : dans ses Options, active « Run On Windows Startup » + « Minimize On Close »
pour qu'il se lance automatiquement et reste discret.

---

## Étape 6 — Clé API météo (OpenWeather)

1. Crée un compte gratuit sur https://openweathermap.org
2. Va dans « API Keys » et copie ta clé
3. Dans `config.py`, remplace la valeur de `OPENWEATHER_API_KEY`

---

## Étape 7 — Configurer config.py ⚠️

**C'est l'étape la plus importante.** Ouvre `config.py` et remplis :

```python
USERNAME = "TonPrénom"       # ton prénom (JARVIS te l'utilisera)
VILLE = "TaVille"            # ta ville (pour la météo)
WIN_USER = "tonUser"         # ton nom d'utilisateur Windows
                             # → ouvre un terminal et tape : echo %USERNAME%
```

Tous les chemins des applications utilisent `{USER}` qui sera remplacé
automatiquement par ta valeur de `WIN_USER`. Si une appli est à un autre
endroit chez toi, mets le bon chemin.

---

## Étape 8 — Lumières Tapo (optionnel)

Si tu as des ampoules TP-Link Tapo :

1. Installe l'appli **Tapo** sur ton téléphone
2. Crée un compte TP-Link et configure tes ampoules
3. Dans l'appli : Profil → ton email → Tapo Lab → active **Third-Party Compatibility**
4. Dans ta box/routeur, fixe une IP locale permanente pour chaque ampoule (DHCP Reservation)
5. Dans `Brain/lumieres.py`, remplis :
   ```python
   Email = "ton.email@gmail.com"
   Mdp   = "tonMotDePasse"
   AMPOULES = {
       "salon": ("192.168.1.XX", "l530"),   # l530 = ampoule couleur
   }
   ```

---

## Lancer JARVIS

```
python Main.py
```

Un écran de connexion s'affiche. La première fois, clique sur
« Pas de compte ? Créer un compte », choisis un identifiant et mot de passe.

Pour tester en mode texte (sans micro) :
```
python Main.py --text
```

---

## Commandes vocales disponibles

Active JARVIS en disant **« Jarvis »**, puis ta commande :

| Commande | Résultat |
|---|---|
| « Jarvis, quelle heure est-il ? » | Heure locale |
| « Jarvis, heure à Tokyo » | Heure à Tokyo |
| « Jarvis, quelle météo ? » | Météo de ta ville |
| « Jarvis, mode jeu » | Ouvre les jeux + change les couleurs |
| « Jarvis, mode travail » | Ouvre les applis de travail |
| « Jarvis, mode cinéma » | Ouvre Netflix |
| « Jarvis, allume la lumière en rouge » | Lumière rouge |
| « Jarvis, éteins tout » | Éteint toutes les lumières |
| « Jarvis, oublie tout » | Remet l'IA à zéro |
| « Jarvis, arrête » | Ferme JARVIS |

---

## Problèmes fréquents

**« python est introuvable »**
→ Tu as oublié de cocher « Add Python to PATH » lors de l'installation.
→ Réinstalle Python 3.12 et coche la case.

**L'IA ne répond pas**
→ Ollama n'est pas lancé. Vérifie http://localhost:11434

**Le micro ne s'active pas**
→ Le modèle Vosk n'est pas dans le bon dossier.
→ Vérifie : `Model/vosk-model-small-fr-0.22/` doit exister.

**CPU affiche « -- »**
→ LibreHardwareMonitor n'est pas lancé en administrateur.

**Erreur 403 sur les lumières**
→ Active « Third-Party Compatibility » dans l'appli Tapo.