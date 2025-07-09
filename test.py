import os
import cv2
import numpy as np
from db.bd import *  # tu gestor de BD que incluye guardar_usuario e inicializar_bd
from cuia import *
from ui.ra import crear_avatar, escenaPYGFX
import face_recognition
# Inicializar la base de datos
inicializar_bd()

# Carpeta donde están las imágenes .jpg / .png
USERS_PATH = os.path.join(os.path.dirname(__file__), "db", "users")

id= [23,45]
def cargar_usuarios_registrados():
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

# Migrar usuarios a la base de datos
usuarios = cargar_usuarios_registrados()
for u in usuarios:
    if u["nombre"]== "martin":
        guardar_usuario(u["nombre"], u["cod"], 45)
    if u["nombre"]== "antonio":
        guardar_usuario(u["nombre"], u["cod"], 23)


# Asegúrate de ajustar esta ruta según tu estructura real
FACEBOOK = os.path.join(os.path.dirname(__file__), "db", "iconos", "facebook.png")
TWITTER = os.path.join(os.path.dirname(__file__), "db", "iconos", "twitter.png")
YOUTUBE = os.path.join(os.path.dirname(__file__), "db", "iconos", "youtube.png")
TIKTOK = os.path.join(os.path.dirname(__file__), "db", "iconos", "tiktok.png")
WHATSAPP = os.path.join(os.path.dirname(__file__), "db", "iconos", "whatsapp.png")
SNAPCHAT = os.path.join(os.path.dirname(__file__), "db", "iconos", "snapchat.png")
LIKEDIN = os.path.join(os.path.dirname(__file__), "db", "iconos", "linkedin.png")
INSTA = os.path.join(os.path.dirname(__file__), "db","iconos", "instagram.png")

for i in id:
    # Guardar redes sociales para cada usuario
    guardar_red_social(i, "LinkedIn", " ",WHATSAPP)
    guardar_red_social(i, "Instagram", " ",INSTA)
    guardar_red_social(i, "Facebook"," ", FACEBOOK)
    guardar_red_social(i, "Twitter", " ", TWITTER)

    if i == 23:
        guardar_red_social(i, "YouTube"," ", YOUTUBE)
        guardar_red_social(i, "TikTok"," ",  TIKTOK)
    elif i == 45:
        guardar_red_social(i, "WhatsApp"," ", LIKEDIN)
        guardar_red_social(i, "Snapchat", " ",SNAPCHAT)


# Obtener perfil


for i in id:
    perfil = obtener_perfil_por_marcador(i)
    print(f"Perfil para marcador {id}:")
    print(perfil["nombre"])
    for red in perfil["iconos"]:
        print(red["red_social"])
        # Convertir a imagen si quieres mostrar:
        imagen = cv2.imdecode(np.frombuffer(red["icono"], np.uint8), cv2.IMREAD_UNCHANGED)

