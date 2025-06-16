# auth/face_auth.py

import face_recognition
import cv2
import os

USERS_PATH = "src/auth/user_data"

def cargar_usuarios_registrados():
    """
    Carga las imágenes de usuarios registrados y devuelve una lista de diccionarios:
    { "nombre": ..., "cod": ... }
    """
    conocidos = []
    for archivo in os.listdir(USERS_PATH):
        if archivo.endswith(".jpg") or archivo.endswith(".png"):
            ruta = os.path.join(USERS_PATH, archivo)
            imagen = face_recognition.load_image_file(ruta)
            codificaciones = face_recognition.face_encodings(imagen)

            if codificaciones:
                nombre = os.path.splitext(archivo)[0]
                conocidos.append({"nombre": nombre, "cod": codificaciones[0]})
    return conocidos

def reconocer_usuario(desconocida_rgb, conocidos):
    """
    Compara la cara en la imagen desconocida con las caras conocidas.
    Devuelve el nombre si hay coincidencia, o None.
    """
    ubicaciones = face_recognition.face_locations(desconocida_rgb)
    cod_desconocidas = face_recognition.face_encodings(desconocida_rgb, ubicaciones)

    cod_conocidos = [c["cod"] for c in conocidos]

    for i, cod in enumerate(cod_desconocidas):
        resultado = face_recognition.compare_faces(cod_conocidos, cod)
        for j in range(len(resultado)):
            if resultado[j]:
                return conocidos[j]["nombre"]
    return None

def capturar_y_reconocer():
    """
    Captura imagen de webcam y trata de autenticar al usuario.
    """
    conocidos = cargar_usuarios_registrados()
    cap = cv2.VideoCapture(0)
    nombre_ventana = "Reconocimiento Facial"
    cv2.namedWindow(nombre_ventana)
    print("🎥 Capturando imagen... Pulsa 'Espacio' para capturar, 'ESC' para salir.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if nombre_ventana == "Control_RA":
            cv2.imshow(nombre_ventana, frame)
        key = cv2.waitKey(1)

        if key == 27:  # ESC
            break
        elif key == 32:  # Espacio
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            nombre = reconocer_usuario(rgb, conocidos)
            cap.release()
            cv2.destroyWindow(nombre_ventana)
            return nombre

    cap.release()
    cv2.destroyWindow(nombre_ventana)
    return None
