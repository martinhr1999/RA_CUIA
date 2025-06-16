# utils/audio.py

from gtts import gTTS
from playsound import playsound
import os
import tempfile
import threading

def decir(texto):
    """
    Reproduce texto por voz usando Google Text-to-Speech (bloqueante).
    """
    try:
        tts = gTTS(text=texto, lang='es')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tts.save(f.name)
            playsound(f.name)
        os.remove(f.name)
    except Exception as e:
        print(f"[ERROR] al hablar con gTTS: {e}")

def decir_async(texto):
    """
    Reproduce texto por voz en segundo plano (no bloquea la ejecución).
    """
    hilo = threading.Thread(target=decir, args=(texto,))
    hilo.start()

# Puedes añadir más funciones aquí si necesitas volumen, selección de idioma, etc.
