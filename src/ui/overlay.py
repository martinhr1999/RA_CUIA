import cuia
from cuia import escenaPYGFX, modeloGLTF, matrizDeTransformacion
import cv2
import numpy as np
import pygfx as gfx
import wgpu
from PIL import Image, ImageDraw, ImageFont
import time

# Tamaño de la cámara virtual
WIDTH = 640
HEIGHT = 480

# Inicializar escena y modelo solo una vez
escena = escenaPYGFX(fov=45, ancho=WIDTH, alto=HEIGHT)
escena.iluminar()

modelo = modeloGLTF("ui/assets/avatar.glb")
modelo.escalar(0.1)
modelo.flotar()
escena.agregar_modelo(modelo)
escena.ilumina_modelo(modelo)

# Panel flotante global
panel_flotante = None
panel_timestamp = None

def crear_texto_3d(texto, posicion=(0, 1.2, 0), color=(255, 255, 255), fondo=(30, 30, 30), tam=64):
    global panel_flotante, panel_timestamp

    if panel_flotante:
        escena.scene.remove(panel_flotante)

    from PIL import Image, ImageDraw, ImageFont
    import wgpu

    ancho, alto = 512, 128
    imagen = Image.new("RGB", (ancho, alto), fondo)
    draw = ImageDraw.Draw(imagen)
    font = ImageFont.truetype("DejaVuSans.ttf", tam)

    w, h = draw.textsize(texto, font=font)
    draw.text(((ancho - w) // 2, (alto - h) // 2), texto, font=font, fill=color)

    datos_np = np.asarray(imagen).astype(np.uint8)

    tex = gfx.Texture(data=datos_np, dim=2, size=datos_np.shape[:2][::-1], format=wgpu.TextureFormat.rgba8unorm_srgb)
    material = gfx.MeshBasicMaterial(map=tex)

    plano = gfx.Mesh(gfx.PlaneGeometry(2, 0.5), material)
    plano.local.position = posicion
    plano.user_data = {"billboard": True}

    escena.scene.add(plano)
    panel_flotante = plano
    panel_timestamp = time.time()  # Guardamos el tiempo actual


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
            panel_flotante.local.rotation = (0, angle, 0)

            # Flotación
            float_y = np.sin(t * 2) * 0.03
            panel_flotante.local.position = (0, 1.2 + float_y, 0)

    # Desvanecimiento después de 3 segundos
    elapsed = t - panel_timestamp
    if elapsed > 3:
        ocultar_panel()

