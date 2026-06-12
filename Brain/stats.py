# ============================================================
#  stats.py — températures CPU et GPU
#   - CPU : via LibreHardwareMonitor (doit tourner EN ADMIN en fond),
#           qui publie ses capteurs sur le WMI "root/LibreHardwareMonitor".
#   - GPU : via nvidia-smi (livré avec les pilotes NVIDIA).
#  Chaque fonction renvoie un entier (°C) ou None si indisponible.
# ============================================================

import subprocess

_wmi_lhm = None   # connexion WMI réutilisée d'un appel à l'autre


def temp_gpu():
    """Température du GPU NVIDIA, en °C, via nvidia-smi."""
    try:
        sortie = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        ligne = sortie.stdout.strip().splitlines()[0].strip()
        return int(ligne)
    except Exception:
        return None


def temp_cpu():
    """Température du CPU, en °C, lue depuis LibreHardwareMonitor (WMI).

    Prérequis : LibreHardwareMonitor lancé EN ADMINISTRATEUR et resté en fond.
    Important : appeler depuis un thread où pythoncom.CoInitialize() a été fait.
    """
    global _wmi_lhm
    try:
        import wmi
        if _wmi_lhm is None:
            _wmi_lhm = wmi.WMI(namespace="root/LibreHardwareMonitor")

        candidats = []
        for capteur in _wmi_lhm.Sensor():
            if capteur.SensorType == "Temperature" and "CPU" in (capteur.Name or ""):
                candidats.append((capteur.Name, capteur.Value))

        # On privilégie "CPU Package" ; sinon, la plus chaude des valeurs trouvées.
        for nom, valeur in candidats:
            if "Package" in nom and valeur is not None:
                return round(valeur)
        valeurs = [v for _, v in candidats if v is not None]
        return round(max(valeurs)) if valeurs else None
    except Exception:
        _wmi_lhm = None     # on forcera une reconnexion au prochain essai
        return None