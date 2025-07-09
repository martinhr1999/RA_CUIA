# voice/intent_processor.py

def interpretar_comando(texto):
    texto = texto.lower()

    if "linkedin" in texto:
        return "mostrar_linkedin"
    if "instagram" in texto:
        return "mostrar_instagram"
    if "facebook" in texto:
        return "mostrar_facebook"
    if "twitter" in texto:
        return "mostrar_twitter"
    if "youtube" in texto: 
        return "mostrar_youtube"
    if "tiktok" in texto:
        return "mostrar_tiktok"
    if "whatsapp" in texto:
        return "mostrar_whatsapp"
    if "snapchat" in texto:
        return "mostrar_snapchat"
    elif "perfil" in texto:
        return "mostrar_perfil"
    elif "redes" in texto:
        return "mis_redes"
    elif "cerrar" in texto and "sesión" in texto:
        return "cerrar_sesion"
    elif "cerrar" in texto:
        return "cerrar"
    elif "salir" in texto:
        return "salir"
    return "desconocido"