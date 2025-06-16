import threading
import time
import speech_recognition as sr
from voice.intent_processor import interpretar_comando
from ui.overlay import crear_texto_3d, ocultar_panel
from utils.audio import decir_async
import webbrowser
import json



class AsistenteVoz:
    def __init__(self):
        self.escuchando = False
        self._thread = None
        self.mostrar_texto_callback = None
        self.salir_callback = None
        self.recognizer = sr.Recognizer()
        self.mic = None
        self.recognizer.energy_threshold = 200
        self.recognizer.dynamic_energy_threshold = True

    def set_callback(self, funcion, salir_func=None):
        self.mostrar_texto_callback = funcion
        self.salir_callback = salir_func

    def _callback(self, recognizer, audio):
        try:
            with open("voz_debug.wav", "wb") as f:
                f.write(audio.get_wav_data())

            texto = recognizer.recognize_google(audio, language="es-ES")
            print(f"[VOZ] Has dicho: {texto}")

            usuario = "martin" # Puedes sustituir esto por estado["nombre"] si lo tienes

            with open("src/ui/perfiles.json", "r") as f:
                perfiles = json.load(f)

            redes = perfiles.get(usuario, {}).get("redes", {})

            if self.mostrar_texto_callback:
                self.mostrar_texto_callback(texto)
            crear_texto_3d(texto)

            accion = interpretar_comando(texto)

            if accion == "mostrar_linkedin":
                crear_texto_3d("LinkedIn: " + redes.get("LinkedIn", "No disponible"))
                decir_async("Aquí tienes tu perfil de LinkedIn.")
            elif accion == "mostrar_perfil":
                crear_texto_3d(f"{usuario}\nPerfil detectado.\nRedes: {', '.join(redes.keys())}")
                decir_async(f"Mostrando tu perfil. Puedes decir: {', '.join(redes.keys())} para abrir una red social.")
            elif accion == "cerrar":
                ocultar_panel()
                decir_async("Cerrando panel.")
            elif accion == "cerrar_sesion":
                if self.salir_callback:
                    self.salir_callback(reset_sesion=True)
            elif accion == "salir":
                if self.salir_callback:
                    self.salir_callback(reset_sesion=False)
            else:
                for red, url in redes.items():
                    if red.lower() in texto.lower():
                        decir_async(f"Abriendo {red}")
                        webbrowser.open_new(url)
                        return
                decir_async("No entendí ese comando.")

        except sr.UnknownValueError:
            print("[VOZ] No se entendió el audio.")
        except sr.RequestError as e:
            print(f"[VOZ] Error al conectar con el servicio de reconocimiento: {e}")
        except Exception as e:
            print("[ERROR VOZ]:", e)

    def encontrar_microfono_disponible(self):
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            try:
                with sr.Microphone(device_index=index) as test_source:
                    self.recognizer.adjust_for_ambient_noise(test_source, duration=0.5)
                    print(f"[INFO VOZ] Usando micrófono: {index} - {name}")
                    return index
            except Exception:
                continue
        print("[ERROR VOZ] No se encontró un micrófono funcional.")
        return None

    def iniciar(self):
        if self.escuchando:
            print("[VOZ] Ya está escuchando.")
            return

        mic_index = self.encontrar_microfono_disponible()
        if mic_index is None:
            print("[ERROR VOZ] No se pudo iniciar reconocimiento.")
            return

        self.mic = sr.Microphone(device_index=mic_index)
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source)
            print("[VOZ] Calibración de ruido completada.")

        self._thread = self.recognizer.listen_in_background(self.mic, self._callback)
        self.escuchando = True
        print("[INFO VOZ] Reconocimiento continuo activado.")

    def detener(self):
        if self.escuchando and self._thread:
            self._thread()
            self.escuchando = False
            print("[INFO VOZ] Reconocimiento continuo detenido.")
