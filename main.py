import cv2
import numpy as np
import os
import json
import multiprocessing
import time
import warnings
from scipy.spatial.transform import Rotation as R
from auth.face_auth import *
from voice.voice_listener import AsistenteVoz
from voice.intent_processor import *
from markers.marker_detector import *
from utils.audio import *
from cuia import *
from ui.overlay import *
from ui.ra import *
from utils.camara import cameraMatrix, distCoeffs
from db.bd import *
from estado import estado
import webbrowser

pygfx_activo = True
ultimo_marcador = None
ultima_matriz = None


texto_reconocido = None
tiempo_mensaje = 0
escena = None

def actualizar_texto_voz(texto):
    global texto_reconocido, tiempo_mensaje
    texto_reconocido = texto
    tiempo_mensaje = time.time()

def detener_modos(reset_sesion=False):
    if estado.get("ra_activa"):
        estado["ra_activa"] = False
        print("[RA] Desactivada por voz")
    if asistente.escuchando:
        asistente.detener()
        print("[VOZ] Desactivada por voz")
    if reset_sesion:
        estado["nombre"] = None
        estado["modo_reconocimiento"] = False
        print("[INFO] Sesión cerrada por comando de voz.")

asistente = AsistenteVoz()

asistente.set_callback(actualizar_texto_voz, detener_modos)

def obtener_botones_visibles():
    botones = {
        "salir": ((50, 340), (350, 390), "Salir"),
        "logout": ((50, 270), (350, 320), "Cerrar Sesion")
    }

    if estado["nombre"] and estado["marcador_detectado"]:
        
        botones.update({
            "voz": ((50, 60), (350, 110), "Reconocer Voz"),
            "ra": ((50, 130), (350, 180), "Iniciar RA"),
            "actualizar_marcador": ((50, 200), (350, 250), "Actualizar Marcador"),  # ⬅️ Añadir esta línea
        })
    elif estado ["nombre"] and estado["marcador_detectado"] is None:
        botones.update({"marcador": ((50, 200), (350, 250), "Reconocer Marcador"),})


    else:
        botones["facial"] = ((50, 60), (350, 110), "Iniciar Sesion")

    return botones

def dibujar_botones(frame):
    
    botones = obtener_botones_visibles()
    for key, ((x1, y1), (x2, y2), texto) in botones.items():
        hover = (key == estado["hover"])

        # Colores y estilo
        color_normal = (100, 150, 240)
        color_hover = (60, 180, 75)
        color_texto = (255, 255, 255)
        sombra = (50, 50, 50)

        # Fondo del botón
        color_fondo = color_hover if hover else color_normal
        cv2.rectangle(frame, (x1, y1), (x2, y2), color_fondo, cv2.FILLED)

        # Borde más oscuro (efecto 3D)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (color_fondo[0]-30, color_fondo[1]-30, color_fondo[2]-30), 2)

        # Texto centrado con sombra
        fuente = cv2.FONT_HERSHEY_SIMPLEX
        escala = 0.7
        grosor = 2
        (text_w, text_h), _ = cv2.getTextSize(texto, fuente, escala, grosor)
        text_x = x1 + (x2 - x1 - text_w) // 2
        text_y = y1 + (y2 - y1 + text_h) // 2

        # Sombra del texto
        cv2.putText(frame, texto, (text_x + 2, text_y + 2), fuente, escala, sombra, grosor + 1, cv2.LINE_AA)
        # Texto blanco encima
        cv2.putText(frame, texto, (text_x, text_y), fuente, escala, color_texto, grosor, cv2.LINE_AA)

def manejar_click(x, y):
    botones = obtener_botones_visibles()
    for key, ((x1, y1), (x2, y2), _) in botones.items():
        if x1 <= x <= x2 and y1 <= y <= y2:
            return key
    return None

def mouse_event(event, x, y, flags, param):
    global webcam
    estado["hover"] = manejar_click(x, y)

    if event == cv2.EVENT_LBUTTONDOWN:
        # Detectar clic sobre objetos de la escena
        accion = manejar_click(x, y)

        if accion == "facial":
            estado["modo_reconocimiento"] = True

        elif accion == "marcador":
            print("[INFO] Esperando escaneo de marcador...")

            for _ in range(50):
                ret, frame_temp = webcam.read()
                if not ret:
                    continue

                id_detectado, _, _, _ = detectar_marcador(frame_temp, return_corners=True)
                if id_detectado is not None:
                    perfil = obtener_perfil_por_marcador(id_detectado)
                    if perfil:
                        estado["marcador_detectado"] = {
                            "id": id_detectado,
                            "nombre": perfil["nombre"]
                        }
                        print(f"[INFO] Marcador reconocido: {perfil['nombre']} (ID {id_detectado})")
                        decir_async(f"Marcador reconocido: {perfil['nombre']}")
                    else:
                        print(f"[WARN] Marcador {id_detectado} no registrado.")
                        decir_async("Marcador no reconocido.")
                    break
        elif accion == "actualizar_marcador":
            print("[INFO] Escaneando nuevo marcador para actualizar ID...")

            for _ in range(50):
                ret, frame_temp = webcam.read()
                if not ret:
                    continue

                id_detectado, _, _, _ = detectar_marcador(frame_temp, return_corners=True)
                if id_detectado is not None:
                    estado["marcador_id"] = id_detectado
                    estado["marcador_detectado"] = {
                        "id": id_detectado,
                        "nombre": buscar_usuario_por_marcador(id_detectado) or "Desconocido"
                    }
                    print(f"[INFO] Nuevo marcador detectado: ID {id_detectado}")
                    decir_async(f"Nuevo marcador detectado: {id_detectado}")
                    break
            else:
                print("[WARN] No se detectó marcador.")
                decir_async("No se detectó ningún marcador.")

                
        elif accion == "voz":
            if not asistente.escuchando:
                asistente.iniciar()
                print("[VOZ] Activada")
                decir_async("Asistente de voz activado. Puedes hablar ahora.") 
            else:
                asistente.detener()
                print("[VOZ] Desactivada")

        elif accion == "ra":
            estado["ra_activa"] = not estado["ra_activa"]
            print("[RA] Activada" if estado["ra_activa"] else "[RA] Desactivada")

        elif accion == "logout":
            estado["nombre"] = None
            estado["marcador_detectado"] = None
            estado["ra_activa"] = False
            print("[INFO] Sesión cerrada.")

        elif accion == "salir":
            print("[INFO] Saliendo de la aplicación.")
            cv2.destroyAllWindows()
            exit()

def detectar_orientacion(normal):
    z = normal / np.linalg.norm(normal)
    if abs(z[1]) > 0.8:
        return "horizontal" if z[1] < 0 else "horizontal_invertido"
    elif abs(z[2]) > 0.8:
        return "vertical" if z[2] < 0 else "vertical_invertido"
    else:
        return "inclinado"



def mostrar_avatar_con_marcador(escena, frame, rvec, tvec, perfil, panel):
    try:
        # Crear avatar si no existe
        if not hasattr(escena, "avatar") or escena.avatar is None:
            avatar = crear_avatar()
            escena.agregar_modelo(avatar)
            escena.ilumina_modelo(avatar)
            escena.avatar = avatar
            escena.avatar.flotar()
        else:
            avatar = escena.avatar

        # Escalar según distancia a cámara
        distancia = np.linalg.norm(tvec)
        escala = max(0.04, min(0.07, distancia * 0.4))
        avatar.escalar(escala)

        # Convertir pose a matriz homogénea
        matriz = pose_to_matrix(rvec, tvec)

        # Rotación: eje Z (marcador) → eje Y (modelo)
        R_corr = R.from_euler('x', -90, degrees=True).as_matrix()
        rotacion = matriz.matrix[:3, :3] @ R_corr

        # Rotación extra para mirar hacia cámara
        R_flip = R.from_euler('y', 180, degrees=True).as_matrix()
        rotacion = rotacion @ R_flip

        # Posición = centro del marcador + 5 cm hacia arriba (eje Y local del modelo)
        posicion = matriz.matrix[:3, 3] + rotacion[:, 1] * 0.05

        # Aplicar posición y rotación al avatar
        avatar.trasladar(posicion)
        avatar.model_obj.local.rotation = tuple(R.from_matrix(rotacion).as_quat())
        avatar.model_obj.visible = True

        # Cámara mira al avatar
        escena.camera.look_at(posicion)

        # Redes sociales
        redes = obtener_redes_comunes()
        if hasattr(escena, "iconos_activos"):
            for icono in escena.iconos_activos:
                escena.scene.remove(icono)
            escena.iconos_activos.clear()
        else:
            escena.iconos_activos = []

        lista_iconos = [
            {"red_social": red, "icono": icono_bytes}
            for red, icono_bytes in redes.items()
        ]

        centro = matriz.matrix[:3, 3].tolist()
        iconos_nuevos = agregar_iconos_redes(escena, lista_iconos, centro, radio=0.35)
        escena.iconos_activos = iconos_nuevos

        # Render final
        render_3d = escena.render()
        panel = alphaBlending(render_3d, panel, 0, 0)

        return panel

    except Exception as e:
        print("[❌ ERROR mostrar_avatar_con_marcador]:", e)
        return panel


def interfaz():
    global pygfx_activo
    global escena, estado
    global webcam

    print("[INFO] Iniciando interfaz principal...")
    cv2.namedWindow("Control_RA")
    cv2.setMouseCallback("Control_RA", mouse_event)

    iconos_visibles = []

    try:
        escena = escenaPYGFX(fov=120, ancho=1000, alto=1000)
        escena.iluminar(3.0)

        # 🔁 Compartir escena con overlay
        import ui.overlay
        ui.overlay.escena = escena

    except Exception as e:
        print(f"[ERROR] pygfx desactivado: {e}")
        pygfx_activo = False

    webcam = cv2.VideoCapture(0)
    if not webcam.isOpened():
        print("❌ No se pudo abrir la cámara")
        return

    _, frame = webcam.read()
    if frame is None:
        print("❌ No se pudo capturar frame inicial")
        return

    while True:
        ret, frame = webcam.read()
        if not ret:
            print("❌ No se pudo capturar frame")
            break

        panel = frame.copy()
        dibujar_botones(panel)

        # 🔹 RECONOCIMIENTO FACIAL O POR MARCADOR
        if estado.get("modo_reconocimiento"):
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            nombre = reconocer_usuario(rgb)
            #nombre ='martin'
            if not nombre:
                id_marcador, _, _, _ = detectar_marcador(frame, return_corners=True)
                print(f"[INFO] Marcador detectado: {id_marcador}")
                if id_marcador is not None:
                    nombre = buscar_usuario_por_marcador(id_marcador)
                    if nombre:
                        print(f"[INFO] Reconocido por marcador: {nombre}")
                        decir(f"Hola {nombre}, has iniciado sesión con tu marcador.")

            if nombre:
                estado["nombre"] = nombre
                estado["refrescar"] = True
            estado["modo_reconocimiento"] = False
            decir_async("Escanea el marcador que deseas reconocer.")  # Instrucción para el usuario

        if estado.get("refrescar"):
            estado["refrescar"] = False

        # 🔹 REALIDAD AUMENTADA (si está activa y hay usuario)
        perfil = None
        rvec, tvec = None, None


        if estado.get("marcador_id") and estado.get("ra_activa"):
            marcador_esperado = estado["marcador_id"]
            perfil = obtener_perfil_por_marcador(marcador_esperado)

            id_detectado, rvec, tvec, _ = detectar_marcador(frame, return_corners=True)

            if id_detectado == marcador_esperado and perfil and rvec is not None and tvec is not None:
                panel = mostrar_avatar_con_marcador(escena, frame, rvec, tvec, perfil, panel)
            elif id_detectado is None:
                # Si se pierde el marcador, ocultar avatar
                if hasattr(escena, "avatar"):
                    escena.avatar.model_obj.visible = False

        # 🔁 ACTUALIZAR Y RENDERIZAR PANEL FLOTANTE
        from ui.overlay import actualizar_texto_flotante, panel_flotante

        actualizar_texto_flotante()

        if escena and panel_flotante:
            try:
                render = escena.render()
                if render.shape[2] == 4:
                    render = render[:, :, :3]
                render_bgr = render[:, :, ::-1]
                render_resized = cv2.resize(render_bgr, (panel.shape[1], panel.shape[0]))
                panel = cv2.addWeighted(panel, 1.0, render_resized, 0.6, 0)
            except Exception as e:
                print("[ERROR renderizando texto flotante]", e)

        # Mostrar ventana final
        cv2.imshow("Control_RA", panel)
        tecla = cv2.waitKey(1)
        if tecla == 27:
            break

    webcam.release()
    cv2.destroyAllWindows()



if __name__ == "__main__":
    while True:
        interfaz()
