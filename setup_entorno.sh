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
pip install --upgrade pip setuptools wheel

echo "[INFO] Instalando dependencias Python..."

pip install numpy==1.24.4 \
            opencv-contrib-python==4.7.0.72 \
            face-recognition==1.3.0 \
            SpeechRecognition==3.9.0 \
            PyAudio==0.2.13 \
            matplotlib==3.7.1 \
            pygfx==0.9.0 \
            "wgpu>=0.19.0,<0.22.0" \
            pylinalg==0.6.7 \
            gltflib==1.0.13 \
            imageio==2.31.1 \
            click==8.1.3


echo ""
echo "[✅ COMPLETADO] El entorno ha sido creado correctamente con Python 3.11."
    source venv/bin/activate
    pip uninstall opencv-python opencv-contrib-python
    pip install opencv-contrib-python
    pip install pyttsx3
    pip install pyaudio
    pip install gTTS playsound
    pip install pygobject
  

