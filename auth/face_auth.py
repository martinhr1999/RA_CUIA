# auth/face_auth.py

import os
import sqlite3
import numpy as np
import face_recognition
import cv2
from voice.voice_listener import *
from markers.marker_detector import detectar_marcador
from db.bd import guardar_usuario


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db"))
os.makedirs(BASE_DIR, exist_ok=True)  # ← crea la carpeta si no existe

DB_PATH = os.path.join(BASE_DIR, "usuarios.db")


def cargar_usuarios_registrados():
    """
    Carga los usuarios registrados desde la base de datos SQLite.
    Devuelve una lista de diccionarios con 'nombre' y 'cod' (np.array).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT nombre, codificacion FROM usuarios")
    filas = cursor.fetchall()
    conn.close()

    conocidos = []
    for nombre, cod_bytes in filas:
        cod = np.frombuffer(cod_bytes, dtype=np.float64)  # ← importante: usa float64
        conocidos.append({"nombre": nombre, "cod": cod})

    return conocidos

def reconocer_usuario(desconocida_rgb):
    """
    Compara la cara en la imagen desconocida con las caras conocidas.
    Devuelve el nombre si hay coincidencia, o None.
    """
    conocidos = cargar_usuarios_registrados()
    ubicaciones = face_recognition.face_locations(desconocida_rgb)
    cod_desconocidas = face_recognition.face_encodings(desconocida_rgb, ubicaciones)

    cod_conocidos = [c["cod"] for c in conocidos]

    for i, cod in enumerate(cod_desconocidas):
        resultado = face_recognition.compare_faces(cod_conocidos, cod)
        for j in range(len(resultado)):
            if resultado[j]:
                return conocidos[j]["nombre"]
    return None


def registrar_usuario_basico(nombre="usuario_test"):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara.")
        return

    print("🧠 Muestra tu cara claramente y pulsa [ESPACIO] para registrar.")
    print("Pulsa [ESC] para cancelar.")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        cv2.imshow("Registro Facial", frame)
        key = cv2.waitKey(1)

        if key == 27:  # ESC
            print("🟥 Registro cancelado.")
            break

        elif key == 32:  # Espacio
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            codificaciones = face_recognition.face_encodings(rgb)
            if codificaciones:
                cod = codificaciones[0]
                guardar_usuario(nombre, cod)
                print(f"✅ Usuario '{nombre}' registrado correctamente.")
                break
            else:
                print("❌ No se detectó ninguna cara. Intenta de nuevo.")

    cap.release()
    cv2.destroyWindow("Registro Facial")


