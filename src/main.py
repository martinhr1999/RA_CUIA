import cv2
import numpy as np
import os
import json
import multiprocessing
import time
import warnings
from scipy.spatial.transform import Rotation as R
from auth.face_auth import cargar_usuarios_registrados, reconocer_usuario
from voice.voice_listener import AsistenteVoz
from voice.intent_processor import interpretar_comando
from markers.marker_detector import detectar_marcador
from utils.audio import decir, decir_async
from cuia import matrizDeTransformacion, modeloGLTF, escenaPYGFX
from ui.overlay import *
from ui.overlay import actualizar_texto_flotante
from ui.ra import *
from cuia import alphaBlending
from utils.camara import cameraMatrix, distCoeffs



warnings.filterwarnings("ignore", category=UserWarning)

pygfx_activo = True
ultimo_marcador = None
ultima_matriz = None

estado = {
    "nombre": None,
    "hover": None,
    "ra_activa": False,
    "refrescar": False,
    "modo_reconocimiento": False
}

texto_reconocido = None
tiempo_mensaje = 0

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


# Cargar perfiles
try:
    with open("src/ui/perfiles.json", "r", encoding="utf-8") as f:
        perfiles = json.load(f)
except:
    perfiles = {}

def obtener_botones_visibles():
    botones = {
        "salir": ((50, 270), (350, 320), "Salir")
    }
    if estado["nombre"]:
        botones.update({
            "voz": ((50, 60), (350, 110), "Reconocer Voz"),
            "ra": ((50, 130), (350, 180), "Iniciar RA"),
            "logout": ((50, 200), (350, 250), "Cerrar Sesión")
        })
    else:
        botones["facial"] = ((50, 60), (350, 110), "Iniciar Sesión")
    return botones

def dibujar_botones(frame):
    botones = obtener_botones_visibles()
    for key, ((x1, y1), (x2, y2), texto) in botones.items():
        hover = (key == estado["hover"])
        color = (0, 200, 100) if estado.get("ra_activa") and key == "ra" else (150, 150, 255) if hover else (200, 200, 200)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
        cv2.putText(frame, texto, (x1 + 15, y2 - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (30, 30, 30), 2)

def manejar_click(x, y):
    botones = obtener_botones_visibles()
    for key, ((x1, y1), (x2, y2), _) in botones.items():
        if x1 <= x <= x2 and y1 <= y <= y2:
            return key
    return None



def mouse_event(event, x, y, flags, param):
    estado["hover"] = manejar_click(x, y)
    if event == cv2.EVENT_LBUTTONDOWN:
        accion = manejar_click(x, y)
        if accion == "facial":
            estado["modo_reconocimiento"] = True
        elif accion == "voz":
            if not asistente.escuchando:
                asistente.iniciar()
            else:
                asistente.detener()
        elif accion == "ra":
            estado["ra_activa"] = not estado["ra_activa"]
            if estado["ra_activa"]:
                asistente.iniciar()
            else:
                asistente.detener()
        elif accion == "logout":
            estado["nombre"] = None
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
    
def interfaz():
    global pygfx_activo
    cv2.namedWindow("Control_RA")
    cv2.setMouseCallback("Control_RA", mouse_event)

    escena = None
    iconos_visibles = []

    try:
        escena = escenaPYGFX(fov=120, ancho=1000, alto=1000)
        escena.iluminar(3.0)
        
    except Exception as e:
        print(f"[ERROR] pygfx desactivado: {e}")
        pygfx_activo = False

    webcam = cv2.VideoCapture(0)
    if not webcam.isOpened():
        print("❌ No se pudo abrir la cámara")
        return

    # Obtener nueva matriz óptima una vez
    ret, frame = webcam.read()
    if not ret:
        print("❌ No se pudo capturar frame inicial")
        return

    while True:
        ret, frame = webcam.read()
        if not ret:
            print("❌ No se pudo capturar frame")
            break

        # Copia segura para overlays
        panel = frame.copy()
        dibujar_botones(panel)

        # Reconocimiento facial o por marcador
        if estado.get("modo_reconocimiento"):
            conocidos = cargar_usuarios_registrados()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            nombre = reconocer_usuario(rgb, conocidos)
            if not nombre:
                id_marcador, _, _, _ = detectar_marcador(frame, return_corners=True)
                perfil = perfiles.get(str(id_marcador)) if id_marcador is not None else None
                if perfil:
                    nombre = perfil["nombre"]
                    print(f"[INFO] Reconocido por marcador: {nombre}")
                    decir(f"Hola {nombre}, has iniciado sesión con tu marcador.")
            if nombre:
                estado["nombre"] = nombre
                estado["refrescar"] = True
                decir_async(f"Has iniciado sesión correctamente, {nombre}")
            estado["modo_reconocimiento"] = False

        if estado.get("refrescar"):
            cv2.waitKey(100)
            estado["refrescar"] = False

        if escena and estado["nombre"]:
            try:
                id_marcador, rvec, tvec, corners = detectar_marcador(frame, return_corners=True)
                

                perfil = perfiles.get(str(id_marcador)) if id_marcador is not None else None

                if perfil and perfil["nombre"] == estado["nombre"]:
                    if not hasattr(escena, "avatar") or escena.avatar is None:
                        avatar = crear_avatar()
                        avatar.flotar()
                        avatar.rotar((0, np.pi, 0))
                        escena.agregar_modelo(avatar)
                        escena.ilumina_modelo(avatar)
                        escena.avatar = avatar

                    tvec_desplazado = tvec + np.array([0, 0, -0.25])
                    distancia = tvec[2]
                    escala_dinamica = max(0.05, min(0.15, distancia * 0.1))
                    escena.avatar.escalar(escala_dinamica)

                    matriz = pose_to_matrix(rvec, tvec_desplazado)

                    # Detectar orientación del marcador
                    normal = matriz.matrix[:3, 2]  # ✅ Acceso correcto

                    orientacion = detectar_orientacion(normal)
                    estado["orientacion_marcador"] = orientacion


                    # Rotación adicional según orientación
                    if orientacion == "vertical":
                        R_extra = R.from_euler('x', -180, degrees=True).as_matrix()  # ✅ Corrige orientación normal
                    elif orientacion == "vertical_invertido":
                        R_extra = np.eye(3)  # ❌ No rotamos (queda cabeza abajo)
                    elif orientacion == "horizontal":
                        R_extra = R.from_euler('x', -90, degrees=True).as_matrix()
                    elif orientacion == "horizontal_invertido":
                        R_extra = R.from_euler('x', 90, degrees=True).as_matrix()
                    else:
                        R_extra = np.eye(3)


                    # Aplicar rotación extra al modelo
                    R_orig = matriz.matrix[:3, :3]
                    matriz.matrix[:3, :3] = R_orig @ R_extra
                    # ✅ Corregir que el avatar mire hacia el usuario
                    R_face_forward = R.from_euler('y', 180, degrees=True).as_matrix()
                    matriz.matrix[:3, :3] = matriz.matrix[:3, :3] @ R_face_forward

                    # Aplicar la transformación final
                    escena.avatar_transform(matriz)

                    for icono in iconos_visibles:
                        escena.scene.remove(icono)
                    iconos_visibles.clear()

                    rutas_iconos = perfil.get("iconos", [])
                    iconos_visibles = agregar_iconos_redes(
                        escena,
                        rutas_iconos,
                        centro=tvec_desplazado.tolist(),
                        radio=0.8,
                        orientacion=orientacion  # ✅ pasas la orientación detectada
                    )

                else:
                    if hasattr(escena, "avatar") and escena.avatar:
                        escena.scene.remove(escena.avatar.model_obj)
                        escena.avatar = None
                    for icono in iconos_visibles:
                        escena.scene.remove(icono)
                    iconos_visibles.clear()

                render_3d = escena.render()
                panel = alphaBlending(render_3d, panel, 0, 0)

            except Exception as e:
                print("RA error:", e)

        cv2.imshow("Control_RA", panel)
        if cv2.waitKey(20) == 27:
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    interfaz()