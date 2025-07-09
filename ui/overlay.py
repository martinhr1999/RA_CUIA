import cuia
from cuia import escenaPYGFX, modeloGLTF, matrizDeTransformacion
import cv2
import numpy as np
import pygfx as gfx
import wgpu
from PIL import Image, ImageDraw, ImageFont
import time
import os
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
import threading

# Tamaño de la cámara virtual
WIDTH = 640
HEIGHT = 480

# Inicializar escena y modelo solo una vez
boton_cerrar = None
escena = escenaPYGFX(fov=45, ancho=WIDTH, alto=HEIGHT)
escena.iluminar()

modelo = modeloGLTF(os.path.join(os.path.dirname(__file__), "assets", "avatar.glb"))
modelo.escalar(0.1)
modelo.flotar()
escena.agregar_modelo(modelo)
escena.ilumina_modelo(modelo)

# Panel flotante global
panel_flotante = None
panel_timestamp = None

panel_flotante = None
panel_timestamp = None

def mouse_event(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        if hasattr(escena, 'panel_flotante') and escena.panel_flotante:
            intersectados = escena.renderer.pick(x, y)
            for obj in intersectados:
                if obj.user_data.get("cerrar_panel"):
                    escena.scene.remove(escena.panel_flotante)
                    escena.scene.remove(obj)
                    escena.panel_flotante = None
                    print("[INFO] Panel cerrado manualmente.")

def crear_plano(ancho=1.0, alto=1.0):
    # Vértices
    positions = np.array([
        [-ancho / 2, -alto / 2, 0],
        [ ancho / 2, -alto / 2, 0],
        [ ancho / 2,  alto / 2, 0],
        [-ancho / 2,  alto / 2, 0],
    ], dtype=np.float32)

    # Coordenadas de textura (u, v)
    texcoords = np.array([
        [0, 0],
        [1, 0],
        [1, 1],
        [0, 1],
    ], dtype=np.float32)

    indices = np.array([
        [0, 1, 2],
        [2, 3, 0],
    ], dtype=np.uint32)

    geometry = gfx.Geometry(positions=positions, indices=indices, texcoords=texcoords)
    return geometry


def mostrar_ventana_texto(texto, titulo="Información"):
    def lanzar():
        ventana = tk.Tk()
        ventana.title(titulo)
        ventana.geometry("600x400")

        texto_widget = tk.Text(ventana, wrap=tk.WORD, font=("Courier", 12))
        texto_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        texto_widget.insert(tk.END, texto)
        texto_widget.config(state=tk.DISABLED)

        boton_cerrar = tk.Button(ventana, text="Cerrar", command=ventana.destroy)
        boton_cerrar.pack(pady=10)

        ventana.mainloop()

    threading.Thread(target=lanzar, daemon=True).start()


def renderizar_avatar(panel, escena, avatar, rvec, tvec, corners, perfil):
    """
    Renderiza el avatar flotando sobre el marcador con texto e iconos si aplica.
    """
    R, _ = cv2.Rodrigues(rvec)
    matriz = np.eye(4)
    matriz[:3, :3] = R
    matriz[:3, 3] = tvec.T

    t = cv2.getTickCount() / cv2.getTickFrequency()
    matriz[1, 3] += np.sin(t * 2) * 0.05  # flotación animada

    transform = matrizDeTransformacion(matriz)
    escena.avatar.model_obj.local.matrix = transform.matrix

    # Mostrar texto sobre el avatar (reemplaza panel anterior si existe)
    crear_texto_3d(f"{perfil['nombre']}\n{perfil['rol']}")

    render = escena.render()
    if render.shape[2] == 4:
        render = render[:, :, :3]
    render_bgr = render[:, :, ::-1]
    render_resized = cv2.resize(render_bgr, (panel.shape[1], panel.shape[0]))
    return cv2.addWeighted(panel, 1.0, render_resized, 0.6, 0)

def ocultar_panel():
    global panel_flotante
    if panel_flotante:
        escena.scene.remove(panel_flotante)
        panel_flotante = None

def actualizar_texto_flotante():
    """Controla rotación del panel flotante, flotación y desvanecimiento automático"""
    global panel_flotante, panel_timestamp

    if not panel_flotante or not panel_timestamp:
        return

    t = time.time()

    if hasattr(escena, "camera") and hasattr(panel_flotante, "user_data"):
        if panel_flotante.user_data.get("billboard"):
            cam_pos = escena.camera.world.position
            obj_pos = panel_flotante.world.position
            direction = cam_pos - obj_pos
            angle = np.arctan2(direction[0], direction[2])

            # ✅ Convertir rotación Y en cuaternión (x, y, z, w)
            quat = R.from_euler('y', angle).as_quat()
            panel_flotante.local.rotation = tuple(quat)

            # ✅ Flotación animada
            float_y = np.sin(t * 2) * 0.03
            panel_flotante.local.position = (0, 1.2 + float_y, 0)

    # 🔁 Desvanecimiento automático tras 3 segundos
    elapsed = t - panel_timestamp
    if elapsed > 3:
        ocultar_panel()

