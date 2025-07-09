#!/bin/bash

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "[❌ ERROR] No se encuentra el entorno virtual 'venv/'."
    exit 1
fi

echo "[INFO] Activando entorno virtual..."

source venv/bin/activate


echo "[INFO] Forzando entorno gráfico (X11)..."
export QT_QPA_PLATFORM=xcb

echo "[INFO] Ejecutando main.py..."
#python test.py
python main.py
