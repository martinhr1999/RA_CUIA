#!/bin/bash

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "[❌ ERROR] No se encuentra el entorno virtual 'venv/'."
    exit 1
fi

echo "[INFO] Activando entorno virtual..."
source venv/bin/activate
    pip uninstall opencv-python opencv-contrib-python
    pip install opencv-contrib-python
    pip install pyttsx3
    pip install pyaudio
    pip install gTTS playsound
    pip install pygobject
    pip install pygfx
    pip install scipy

  






echo "[INFO] Forzando entorno gráfico (X11)..."
export QT_QPA_PLATFORM=xcb

echo "[INFO] Ejecutando src/main.py..."
python src/main.py
