import face_recognition
import cv2
import sqlite3
import numpy as np
import os
from estado import estado  # Asegúrate de que este módulo esté correctamente implementado

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db"))
os.makedirs(BASE_DIR, exist_ok=True)
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")


def inicializar_bd():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            codificacion BLOB NOT NULL,
            marcador_id INTEGER DEFAULT 0 -- cada usuario tiene un marcador distinto
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perfiles_redes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marcador_id INTEGER NOT NULL,
            red_social TEXT NOT NULL,
            info_red TEXT DEFAULT '',
            icono BLOB NOT NULL,
            FOREIGN KEY (marcador_id) REFERENCES usuarios(marcador_id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

def guardar_usuario(nombre, codificacion, marcador_id):
    cod_bytes = codificacion.tobytes()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO usuarios (nombre, codificacion, marcador_id) VALUES (?, ?, ?)", (nombre, cod_bytes, marcador_id))
    conn.commit()
    conn.close()

def guardar_red_social(marcador_id, red_social, info_red, ruta_icono):
    with open(ruta_icono, "rb") as f:
        icono_bytes = f.read()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO perfiles_redes (marcador_id, red_social,info_red, icono) VALUES (?, ?, ?,?)",
        (marcador_id, red_social,info_red, icono_bytes)
    )
    conn.commit()
    conn.close()


def cargar_usuarios():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT nombre, codificacion, marcador_id FROM usuarios")
    filas = cursor.fetchall()
    conn.close()

    usuarios = []
    for nombre, cod_bytes, marcador_id in filas:
        cod = np.frombuffer(cod_bytes, dtype=np.float64)
        usuarios.append({"nombre": nombre, "cod": cod, "marcador_id": marcador_id})
    return usuarios

def buscar_usuario_por_marcador(marcador_id):
    """
    Devuelve el nombre del usuario asociado a un marcador, si existe.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM usuarios WHERE marcador_id = ?", (marcador_id,))
    fila = cursor.fetchone()
    conn.close()

    return fila[0] if fila else None


def obtener_perfil_por_marcador(marcador_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT nombre FROM usuarios WHERE marcador_id = ?", (marcador_id,))
    fila = cursor.fetchone()
    if not fila:
        conn.close()
        return None

    nombre = fila[0]

    cursor.execute("SELECT red_social, icono FROM perfiles_redes WHERE marcador_id = ?", (marcador_id,))
    filas = cursor.fetchall()
    conn.close()

    iconos = []
    for red, icono_bytes in filas:
        iconos.append({
            "red_social": red,
            "icono": icono_bytes  # ya lo puedes usar como imagen en memoria (ej. con PIL o cv2.imdecode)
        })

    return {"nombre": nombre, "iconos": iconos}


def obtener_redes_comunes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    nombre_usuario = estado.get("nombre")  # Usuario que inició sesión
    if not nombre_usuario:
        conn.close()
        return {}

    #print(f"[DEBUG] Usuario actual en sesión: {nombre_usuario}")

    # Obtener el marcador del usuario que inició sesión
    cursor.execute("SELECT marcador_id FROM usuarios WHERE nombre = ?", (nombre_usuario,))
    fila = cursor.fetchone()
    if not fila:
        conn.close()
        return {}

    marcador_usuario = fila[0]

    # Obtener redes del usuario
    cursor.execute("SELECT red_social FROM perfiles_redes WHERE marcador_id = ?", (marcador_usuario,))
    redes_usuario_raw = cursor.fetchall()
    redes_usuario = {r[0].strip().lower() for r in redes_usuario_raw}
    #print(f"[DEBUG] Redes del usuario {nombre_usuario}: {redes_usuario}")

    marcador_detectado = estado.get("marcador_detectado")
    if isinstance(marcador_detectado, dict):
        marcador_detectado = marcador_detectado.get("id")
    if marcador_detectado is None:
        conn.close()
        return {}

    #print(f"[DEBUG] Marcador detectado: {marcador_detectado}")

    # Obtener redes del marcador detectado
    cursor.execute("SELECT red_social, icono FROM perfiles_redes WHERE marcador_id = ?", (marcador_detectado,))
    redes_marcador = cursor.fetchall()
    #print(f"[DEBUG] Redes del marcador {marcador_detectado}: {[r[0] for r in redes_marcador]}")

    conn.close()

    # Comparación insensible a mayúsculas/espacios
    redes_comunes = {
        red: icono for red, icono in redes_marcador
        if red.strip().lower() in redes_usuario
    }
    print(f"[DEBUG] Redes comunes: {list(redes_comunes.keys())}")

    return redes_comunes

def obtener_redes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    nombre_usuario = estado.get("nombre")  # Usuario que inició sesión
    if not nombre_usuario:
        conn.close()
        return {}

    # Obtener el marcador del usuario que inició sesión
    cursor.execute("SELECT marcador_id FROM usuarios WHERE nombre = ?", (nombre_usuario,))
    fila = cursor.fetchone()
    if not fila:
        conn.close()
        return {}

    marcador_usuario = fila[0]

    # Obtener redes del usuario que inició sesión
    cursor.execute("""
        SELECT red_social, icono 
        FROM perfiles_redes 
        WHERE marcador_id = ?
    """, (marcador_usuario,))
    
    # Diccionario: {red: icono_bytes}
    redes_completas = {}
    for red, icono in cursor.fetchall():
        if isinstance(icono, memoryview):  # ← SQLite devuelve BLOB como memoryview
            icono = icono.tobytes()
        redes_completas[red] = icono

    conn.close()
    return redes_completas