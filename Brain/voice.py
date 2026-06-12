# ============================================================
#  voice.py — écoute (Vosk) et voix (TTS) de J.A.R.V.I.S
# ============================================================

import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import sys
import json
import time
import queue
import asyncio
import subprocess

import sounddevice as sd
import pygame
from vosk import Model, KaldiRecognizer, SetLogLevel

user = "Gabin"

# ---- TTS optionnel : ElevenLabs ----
try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import save as save_elevenlabs_audio
except ImportError:
    ElevenLabs = None
    save_elevenlabs_audio = None

TTS_ENGINE = os.getenv("TTS_ENGINE", "edge").strip().lower()
VOICE_OUTPUT_PATH = "voice.mp3"

EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "fr-FR-HenriNeural").strip() or "fr-FR-HenriNeural"
EDGE_TTS_RATE = os.getenv("EDGE_TTS_RATE", "+0%").strip() or "+0%"
EDGE_TTS_VOLUME = os.getenv("EDGE_TTS_VOLUME", "+0%").strip() or "+0%"
EDGE_TTS_PITCH = os.getenv("EDGE_TTS_PITCH", "+0Hz").strip() or "+0Hz"

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
DEFAULT_ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
JARVIS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_ELEVENLABS_VOICE_ID).strip() or DEFAULT_ELEVENLABS_VOICE_ID

client = ElevenLabs(api_key=ELEVENLABS_API_KEY) if ElevenLabs and ELEVENLABS_API_KEY else None


def _paid_plan_required(exc):
    detail = str(exc)
    return "paid_plan_required" in detail or "Free users cannot use library voices" in detail


def _generer_audio_elevenlabs(text, voice_id):
    return client.text_to_speech.convert(text=text, voice_id=voice_id)


def _generer_audio_edge(text, output_path):
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError("edge-tts n'est pas installe. Lance : python -m pip install edge-tts") from exc

    async def _save_audio():
        communicate = edge_tts.Communicate(
            text, EDGE_TTS_VOICE,
            rate=EDGE_TTS_RATE, volume=EDGE_TTS_VOLUME, pitch=EDGE_TTS_PITCH,
        )
        await communicate.save(output_path)

    asyncio.run(_save_audio())


def _jouer_audio(output_path):
    pygame.mixer.init()
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
    except Exception:
        pass
    pygame.mixer.music.load(output_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    pygame.mixer.music.stop()
    pygame.mixer.music.unload()


def stopper_parole():
    """Coupe immédiatement la parole en cours (la boucle d'attente dans parler() s'arrête)."""
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass


def _parler_windows(text):
    escaped = text.replace("'", "''")
    command = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Speak('{0}')"
    ).format(escaped)
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def parler(text):
    if TTS_ENGINE == "windows":
        _parler_windows(text)
        return

    if TTS_ENGINE != "elevenlabs":
        try:
            _generer_audio_edge(text, VOICE_OUTPUT_PATH)
            _jouer_audio(VOICE_OUTPUT_PATH)
            return
        except Exception as exc:
            print(f"[Edge TTS indisponible] {exc}")
            _parler_windows(text)
            return

    try:
        if client is None:
            raise RuntimeError("ELEVENLABS_API_KEY n'est pas configurée.")
        try:
            audio = _generer_audio_elevenlabs(text, JARVIS_VOICE_ID)
        except Exception as exc:
            if _paid_plan_required(exc) and JARVIS_VOICE_ID != DEFAULT_ELEVENLABS_VOICE_ID:
                print("[ElevenLabs] Voix non autorisee, essai de la voix par defaut.")
                audio = _generer_audio_elevenlabs(text, DEFAULT_ELEVENLABS_VOICE_ID)
            else:
                raise
        pygame.mixer.init()
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass
        save_elevenlabs_audio(audio, VOICE_OUTPUT_PATH)
        pygame.mixer.music.load(VOICE_OUTPUT_PATH)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
    except Exception as exc:
        if _paid_plan_required(exc):
            print("[ElevenLabs indisponible] La voix configuree necessite un plan payant.")
        else:
            print(f"[ElevenLabs indisponible] {exc}")
        _parler_windows(text)


# ============================================================
#  RECONNAISSANCE VOCALE (Vosk)
# ============================================================

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS                                   # cas d'un .exe PyInstaller
    except Exception:
        # voice.py est dans Brain/, on remonte d'un niveau pour atteindre la racine
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# Pour plus de précision : remplace par "Model/vosk-model-fr-0.22"
MODEL_PATH = resource_path("Model/vosk-model-small-fr-0.22")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Modèle vocal non trouvé : {MODEL_PATH}")

SetLogLevel(-1)
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, 16000)

audio_queue = queue.Queue()


def callback(indata, frames, info, status):
    audio_queue.put(bytes(indata))


def vider_audio_queue():
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
        except queue.Empty:
            break


# Le micro reste ouvert en permanence (ouvert une seule fois)
_stream = None


def _demarrer_micro():
    global _stream
    if _stream is None:
        _stream = sd.RawInputStream(
            samplerate=16000, blocksize=8000, dtype='int16',
            channels=1, callback=callback,
        )
        _stream.start()


def ecouter():
    """Écoute en continu et renvoie la prochaine phrase reconnue (sans mot-clé)."""
    _demarrer_micro()
    vider_audio_queue()        # on ignore ce que JARVIS vient de dire lui-même
    recognizer.Reset()
    print("Je vous écoute...")
    while True:
        data = audio_queue.get()
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            texte = result.get("text", "").lower().strip()
            if texte:
                print("👤 :", texte)
                recognizer.Reset()
                return texte