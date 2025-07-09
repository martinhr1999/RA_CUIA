import threading
import time
import speech_recognition as sr
from voice.intent_processor import interpretar_comando
from ui.overlay import  ocultar_panel
from utils.audio import decir_async
import webbrowser
from db.bd import *
from estado import estado  # Asegúrate de que este módulo esté correctamente implementado

import tkinter as tk
import threading
from PIL import Image, ImageTk
import io

def mostrar_ventana_texto(texto, iconos=None, titulo="Información"):
    def lanzar():
        ventana = tk.Tk()
        ventana.title(titulo)

        # Tamaño más compacto
        ventana.geometry("500x300")

        # Centrar la ventana en pantalla
        ventana.update_idletasks()
        w = 500
        h = 300
        ws = ventana.winfo_screenwidth()
        hs = ventana.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        ventana.geometry(f'{w}x{h}+{x}+{y}')

        # Mostrar iconos más grandes (64x64)
        if iconos:
            marco_iconos = tk.Frame(ventana)
            marco_iconos.pack(pady=10)
            for red, icono_bytes in iconos.items():
                try:
                    imagen = Image.open(io.BytesIO(icono_bytes)).resize((64, 64))
                    img_tk = ImageTk.PhotoImage(imagen)
                    label = tk.Label(marco_iconos, image=img_tk)
                    label.image = img_tk
                    label.pack(side=tk.LEFT, padx=10)
                except Exception as e:
                    print(f"[WARNING] No se pudo cargar icono de {red}: {e}")

        # Cuadro de texto más pequeño
        texto_widget = tk.Text(ventana, height=6, wrap=tk.WORD, font=("Courier", 11))
        texto_widget.pack(expand=False, fill=tk.BOTH, padx=10, pady=5)
        texto_widget.insert(tk.END, texto)
        texto_widget.config(state=tk.DISABLED)

        # Botón cerrar
        boton_cerrar = tk.Button(ventana, text="Cerrar", command=ventana.destroy)
        boton_cerrar.pack(pady=10)

        ventana.mainloop()

    threading.Thread(target=lanzar, daemon=True).start()


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
            #texto = recognizer.recognize_google(audio, language="es-ES")
            
            texto= 'perfil' # Para pruebas, puedes comentar esta línea y descomentar la anterio
            print(f"[VOZ] Has dicho: {texto}")

            marcador_info = estado.get("marcador_detectado")

            if marcador_info:
                marcador_id = marcador_info["id"]
                redes = obtener_redes_comunes()  # <- debes tener esta función
                usuario = marcador_info["nombre"]
            else:
                redes = {}
                usuario = "Desconocido"
            

            accion = interpretar_comando(texto)

            if accion == "mostrar_linkedin" :
                url = redes.get("LinkedIn")
                if url:
                    mostrar_ventana_texto(f"LinkedIn:\n{url}")
                    decir_async("Aquí tienes tu perfil de LinkedIn.")
                    
                    webbrowser.open('https://es.linkedin.com/')
                else:
                    mostrar_ventana_texto("LinkedIn no disponible.")
                    decir_async("No tienes un perfil de LinkedIn asociado.")

            elif accion == "mostrar_instagram":
                url = redes.get("Instagram")
                if url:
                    #mostrar_ventana_texto(f"Instagram:\n{url}")
                    dir_web='https://www.instagram.com/'
                    #dir_web=dir_web.decode()
                    decir_async("Aquí tienes tu perfil de Instagram.")
                    webbrowser.open(dir_web)
                else:
                    mostrar_ventana_texto("Instagram no disponible.")
                    decir_async("No tienes un perfil de Instagram asociado.")
            elif accion == "mostrar_facebook":
                url =redes.get("Facebook")
                if url:
                    dir_web='https://www.facebook.com/'
                    #mostrar_ventana_texto(f"Facebook:\n{url}")
                    #dir_web=dir_web.decode()
                    decir_async("Aquí tienes tu perfil de Facebook.")
                    webbrowser.open(dir_web)
                else:
                    mostrar_ventana_texto("Facebook no disponible.")
                    decir_async("No tienes un perfil de Facebook asociado.")
            elif accion == "mostrar_twitter":
                url = redes.get("Twitter")
                if url:
                    dir_web='https://twitter.com/'
                    #mostrar_ventana_texto(f"Twitter:\n{url}")
                    #dir_web=dir_web.decode()
                    decir_async("Aquí tienes tu perfil de Twitter.")
                    webbrowser.open(dir_web)
                else:
                    mostrar_ventana_texto("Twitter no disponible.")
                    decir_async("No tienes un perfil de Twitter asociado.")
            elif accion == "mostrar_youtube":
                url = redes.get("YouTube")
                if url:
                    dir_web='https://www.youtube.com/'
                    #mostrar_ventana_texto(f"YouTube:\n{url}")
                    #dir_web=dir_web.decode()
                    decir_async("Aquí tienes tu perfil de YouTube.")
                    webbrowser.open(dir_web)
                else:
                    mostrar_ventana_texto("YouTube no disponible.")
                    decir_async("No tienes un perfil de YouTube asociado.")
            elif accion == "mostrar_tiktok":
                url = redes.get("TikTok")
                if url:
                    dir_web='https://www.tiktok.com/'
                    #mostrar_ventana_texto(f"TikTok:\n{url}")
                    #dir_web=dir_web.decode()
                    decir_async("Aquí tienes tu perfil de TikTok.")
                    webbrowser.open(dir_web)
                else:
                    mostrar_ventana_texto("TikTok no disponible.")
                    decir_async("No tienes un perfil de TikTok asociado.")
            elif accion == "mostrar_whatsapp":
                url = redes.get("WhatsApp")
                if url:
                    dir_web='https://web.whatsapp.com/'
                    #mostrar_ventana_texto(f"WhatsApp:\n{url}")
                    #dir_web=dir_web.decode()
                    decir_async("Aquí tienes tu perfil de WhatsApp.")
                    webbrowser.open(dir_web)
                else:
                    mostrar_ventana_texto("WhatsApp no disponible.")
                    decir_async("No tienes un perfil de WhatsApp asociado.")
            elif accion == "mostrar_snapchat":
                url = redes.get("Snapchat")
                if url:
                    dir_web='https://www.snapchat.com/'
                    #mostrar_ventana_texto(f"Snapchat:\n{url}")
                    #dir_web=dir_web.decode()
                    decir_async("Aquí tienes tu perfil de Snapchat.")
                    webbrowser.open(dir_web)
                else:
                    mostrar_ventana_texto("Snapchat no disponible.")
                    decir_async("No tienes un perfil de Snapchat asociado.")
            elif accion == "mostrar_perfil" :
                nombre = usuario if isinstance(usuario, str) else usuario.get("nombre", "Usuario")

                redes = obtener_redes_comunes()
                redes_texto = "\n".join(f"{red}" for red in redes) or "Sin redes sociales"
                texto = f"Nombre: {nombre}\n\nRedes:\n{redes_texto}"

                mostrar_ventana_texto(texto, iconos=redes)
                decir_async("Mostrando el perfil. Puedes decir el nombre de una red social para abrirla.")
            
            elif accion == "mis_redes" :
                nombre = usuario if isinstance(usuario, str) else usuario.get("nombre", "Usuario")

                redes = obtener_redes()
                redes_texto = "\n".join(f"{red}" for red in redes) or "Sin redes sociales"
                texto = f"Nombre: {nombre}\n\nRedes:\n{redes_texto}"

                mostrar_ventana_texto(texto, iconos=redes)
                decir_async("Mostrando tu perfil. Puedes decir el nombre de una red social para abrirla.")
        

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
    
    def escuchar_nombre(self, timeout=5):
        """
        Escucha el nombre del usuario una sola vez (no modo continuo).
        """
        mic_index = self.encontrar_microfono_disponible()
        if mic_index is None:
            print("[ERROR VOZ] No se detectó micrófono.")
            return None

        mic = sr.Microphone(device_index=mic_index)
        with mic as source:
            print("🎙️ Esperando que digas tu nombre...")
            self.recognizer.adjust_for_ambient_noise(source)
            try:
                audio = self.recognizer.listen(source, timeout=timeout)
                texto = self.recognizer.recognize_google(audio, language="es-ES")
                print(f"[VOZ] Nombre capturado: {texto}")
                return texto
            except sr.WaitTimeoutError:
                print("[VOZ] No se detectó voz a tiempo.")
            except sr.UnknownValueError:
                print("[VOZ] No se entendió el audio.")
            except sr.RequestError as e:
                print(f"[VOZ] Error al conectar con el servicio: {e}")
        return None

