# voice/intent_processor.py

def interpretar_comando(texto):
    texto = texto.lower()

    if "linkedin" in texto:
        return "mostrar_linkedin"
    elif "perfil" in texto:
        return "mostrar_perfil"
    elif "cerrar" in texto and "sesión" in texto:
        return "cerrar_sesion"
    elif "cerrar" in texto:
        return "cerrar"
    elif "salir" in texto:
        return "salir"
    return "desconocido"