#!/bin/bash
VENV="venv"
MAIN="src/main.py"

echo "[INFO] Verificando que python3.11 esté instalado..."
if ! command -v python3.11 &> /dev/null; then
    echo "[ERROR] python3.11 no está instalado. Ejecútalo primero:"
    echo "sudo apt update && sudo apt install -y python3.11 python3.11-venv python3.11-dev"
    exit 1
fi
apt update
apt install python3.11-tk

echo "[INFO] Creando entorno virtual con Python 3.11..."
python3.11 -m venv venv

echo "[INFO] Activando entorno virtual..."
source venv/bin/activate

echo "[INFO] Actualizando pip y herramientas de compilación..."
pip install --upgrade pip
pip install "setuptools<81"
pip install wheel

echo "[INFO] Instalando dependencias Python..."
echo ""
echo "[✅ COMPLETADO] El entorno ha sido creado correctamente con Python 3.11."
    source venv/bin/activate
    
    pip install opencv-contrib-python
    pip install pyttsx3
    pip install pyaudio
    pip install gTTS playsound
    pip install pygobject
    pip install pygfx
    pip install scipy
    pip install dlib
    pip install face_recognition
    pip install gltflib

        # 🔹 Visualización y texturas
    pip install Pillow
    pip install imageio
    pip install matplotlib

    # 🔹 Audio y reconocimiento por voz
    pip install SpeechRecognition
    pip install sounddevice

    # 🔹 Otros útiles para 3D / RA / carga de modelos
    pip install trimesh
    pip install openai

    # 🔹 Por si usas transformaciones espaciales
    pip install transforms3d
    pip install --upgrade pygfx --pre
