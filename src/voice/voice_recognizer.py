# voice/voice_recognizer.py

import speech_recognition as sr
import threading
import queue
import time

def escuchar_comando_en_fondo(resultado_queue):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    print("🎙️ Esperando comando de voz...")

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("🔇 Ruido calibrado. Habla ahora.")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

    try:
        texto = recognizer.recognize_google(audio, language="es-ES")
        print("🗣️ Has dicho:", texto)
        resultado_queue.put(texto)
    except Exception as e:
        print("[ERROR reconocimiento]:", e)
        resultado_queue.put(None)

def escuchar_comando():
    """
    Lanza el reconocimiento de voz y devuelve el texto reconocido (bloqueante pero no congela interfaz).
    """
    resultado = queue.Queue()
    hilo = threading.Thread(target=escuchar_comando_en_fondo, args=(resultado,))
    hilo.start()

    # Esperar resultado (máx 10s)
    for _ in range(100):
        if not resultado.empty():
            return resultado.get()
        time.sleep(0.1)
    
    return None
