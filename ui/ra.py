from cuia import modeloGLTF
from pygfx import *
import pygfx as gfx
from PIL import Image
import numpy as np
import math
from cuia import *

from PIL import Image

from scipy.spatial.transform import Rotation as R
from scipy.spatial.transform import Rotation as SciRot


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
    avatar = modeloGLTF("ui/assets/silueta.glb")
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



def crear_modelo_icono(imagen_cv):
    if imagen_cv is None:
        raise ValueError("Imagen vacía")

    if imagen_cv.shape[2] == 3:
        imagen_cv = cv2.cvtColor(imagen_cv, cv2.COLOR_BGR2RGBA)
    elif imagen_cv.shape[2] == 4:
        imagen_cv = cv2.cvtColor(imagen_cv, cv2.COLOR_BGRA2RGBA)
    else:
        raise ValueError("Formato de imagen no soportado")

    # Normalizar a valores [0, 1]
    datos = imagen_cv.astype(np.float32) / 255.0  # (H, W, 4)

    # Crear textura correctamente con datos
    tex = gfx.Texture(data=datos, dim=2)

    # Crear material transparente
    material = gfx.MeshBasicMaterial(map=tex)
    material.transparent = True  # ✅ importante: se activa después

    # Calcular dimensiones proporcionales
    ancho = 0.2
    alto = ancho * (imagen_cv.shape[0] / imagen_cv.shape[1])
    geometria = gfx.plane_geometry(ancho, alto)

    # Crear malla final
    return gfx.Mesh(geometria, material)

def calcular_posicion_icono(centro, radio, indice, total):
    """
    Calcula la posición de un icono en un círculo.
    `total`: número total de iconos.
    """
    if total == 0:
        return np.array(centro, dtype=np.float32)

    angulo = 2 * np.pi * indice / total
    cx, cy, cz = centro

    # General 3D (plano XY con rotación en Z)
    x = cx + radio * np.cos(angulo)
    y = cy + radio * np.sin(angulo)
    z = cz

    return np.array([x, y, z], dtype=np.float32)

def orientar_icono_hacia(icono_modelo, origen, destino):
    dir_vector = destino - origen
    norm = np.linalg.norm(dir_vector)

    if norm < 1e-6:
        return  # No hay dirección válida

    dir_vector /= norm

    z_base = np.array([0, 0, 1], dtype=np.float32)  # dirección "frontal" del icono
    axis = np.cross(z_base, dir_vector)
    angle = np.arccos(np.clip(np.dot(z_base, dir_vector), -1.0, 1.0))

    if np.linalg.norm(axis) < 1e-6:
        if np.dot(z_base, dir_vector) < 0:
            quat = SciRot.from_euler('y', 180, degrees=True).as_quat()
            icono_modelo.local.rotation = tuple(quat)
        return

    axis /= np.linalg.norm(axis)
    rot = SciRot.from_rotvec(axis * angle)
    icono_modelo.local.rotation = tuple(rot.as_quat())
    

import traceback


def agregar_iconos_redes(escena, lista_iconos, centro, radio=0.8):
    iconos = []
    t_inicio = time.time()
    total = len(lista_iconos)

    for i, info in enumerate(lista_iconos):
        try:
            icono_bytes = info["icono"]
            np_arr = np.frombuffer(icono_bytes, np.uint8)
            imagen = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)
            if imagen is None:
                print(f"[ERROR icono] No se pudo decodificar icono de {info['red_social']}")
                continue

            icono_modelo = crear_modelo_icono(imagen)
            icono_modelo.nombre_red = info["red_social"]

            # Posición con desplazamiento sinusoidal en eje Y
            t = time.time() - t_inicio
            y_fluct = 0.05 * np.sin(t + i)

            posicion = calcular_posicion_icono(centro, radio, i, total)
            posicion[1] += y_fluct

            icono_modelo.local.position = posicion
            
            rot_quat = escena.avatar.model_obj.local.rotation  # ya está en quaternion
            icono_modelo.local.rotation = rot_quat
            escena.agregar_modelo(icono_modelo)
            iconos.append(icono_modelo)

        except Exception as e:
            print("[ERROR icono]", info)
            traceback.print_exc()

    return iconos