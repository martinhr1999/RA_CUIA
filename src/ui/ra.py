from cuia import modeloGLTF
from pygfx import *
import pygfx as gfx
from PIL import Image
import numpy as np
import math
from cuia import *

from PIL import Image

from scipy.spatial.transform import Rotation as R

def crear_silueta_con_nombre(nombre, posicion=[0, 0, 0]):
    silueta = modeloGLTF("src/ui/silueta.glb")
    silueta.escalar(0.03)
    silueta.trasladar(posicion)

    # Crear texto flotante
    material_texto = TextMaterial(color="white")
    texto = Text(material=material_texto, text=nombre)

    # Posicionar y escalar usando .world (funciona en más versiones)
    texto.world.position = [posicion[0], posicion[1] + 0.07, posicion[2]]
    texto.world.scale = [0.02, 0.02, 0.02]

    return silueta, texto
from cuia import modeloGLTF

def crear_avatar():
    avatar = modeloGLTF("src/ui/silueta.glb")
    avatar.escalar(0.3)
    avatar.trasladar([0, 0, -2])
    avatar.flotar()
    return avatar

def crear_icono_red_social(ruta_imagen, posicion):
    img = Image.open(ruta_imagen).convert("RGBA")
    tex_data = np.array(img)
    texture = gfx.Texture(tex_data, dim=2)
    material = gfx.MeshBasicMaterial(map=texture)

    plano = gfx.plane_geometry(0.3, 0.3)  # ✅ corregido
    malla = gfx.Mesh(plano, material)
    malla.local.position = posicion
    return malla




def agregar_iconos_redes(escena, rutas_iconos, centro=(0, 0, 0), radio=0.5, orientacion="vertical"):
    iconos = []
    n = len(rutas_iconos)
    
    if n == 1:
        angulos = [0]  # al frente
    else:
        angulos = [-np.pi/2 + i * (np.pi / (n - 1)) for i in range(n)]  # semicircular

    for i, (ruta, angulo) in enumerate(zip(rutas_iconos, angulos)):
        try:
            imagen = Image.open(ruta).convert("RGBA")
            tex_data = np.array(imagen).astype(np.uint8)
            tex = Texture(tex_data, dim=2)
            material = MeshBasicMaterial(map=tex)
            geometry = plane_geometry(1, 1)
            icono = Mesh(geometry, material)

            # Escala visible
            icono.local.scale = (0.3, 0.3, 0.3)

            # Posición frontal semicircular respecto al marcador
            radio_expandido = radio + 0.3  # aumenta separación general

            x = centro[0] + radio_expandido * np.cos(angulo)
            y = centro[1] + 0.7  # altura sobre el marcador
            z = centro[2] + radio_expandido * np.sin(angulo) - 0.3  # más hacia la cámara
            icono.local.position = (x, y, z)

            # Rotación según orientación del marcador
            if orientacion == "vertical":
                rot = R.from_euler('x', 0, degrees=True)
            elif orientacion == "vertical_invertido":
                rot = R.from_euler('x', 180, degrees=True)
            elif orientacion == "horizontal":
                rot = R.from_euler('x', -90, degrees=True)
            elif orientacion == "horizontal_invertido":
                rot = R.from_euler('x', 90, degrees=True)
            else:
                rot = R.identity()

            # Mirar hacia el usuario
            rot = rot * R.from_euler('y', 180, degrees=True)
            icono.local.rotation = tuple(rot.as_quat())

            escena.scene.add(icono)
            iconos.append(icono)

        except Exception as e:
            print(f"[ERROR icono] {ruta}: {e}")

    return iconos
