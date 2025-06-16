# utils/audio.py

import pyttsx3

# utils/audio.py

import pyttsx3
import threading

# Inicializamos el motor una vez
_engine = pyttsx3.init()
_engine.setProperty("rate", 160)  # Velocidad por defecto

# Buscar voces disponibles
_voices = _engine.getProperty("voices")
_voz_actual = None  # Guardamos la voz seleccionada si se usa


def decir(texto):
    """
    Reproduce texto por voz (bloqueante).
    """
    try:
        _engine.say(texto)
        _engine.runAndWait()
    except Exception as e:
        print(f"[ERROR] al hablar: {e}")


def decir_async(texto):
    """
    Reproduce texto por voz en segundo plano (no bloquea la ejecución principal).
    """
    hilo = threading.Thread(target=decir, args=(texto,))
    hilo.start()


def ajustar_volumen(nivel):
    """
    Ajusta el volumen (0.0 a 1.0).
    """
    nivel = max(0.0, min(1.0, nivel))
    _engine.setProperty("volume", nivel)


def usar_voz(nombre_parcial):
    """
    Selecciona una voz instalada que contenga el texto dado (ej: 'spanish', 'hispan').
    """
    global _voz_actual
    for voz in _voices:
        if nombre_parcial.lower() in voz.name.lower():
            _engine.setProperty("voice", voz.id)
            _voz_actual = voz
            print(f"[INFO] Voz seleccionada: {voz.name}")
            return
    print("[WARN] No se encontró una voz que coincida con:", nombre_parcial)
