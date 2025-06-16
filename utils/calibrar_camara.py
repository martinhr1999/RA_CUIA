
import cv2
import numpy as np
import cv2.aruco as aruco
import os

# Parámetros del tablero Charuco
squaresX = 5      # Número de cuadros horizontales
squaresY = 7      # Número de cuadros verticales
squareLength = 0.04  # en metros
markerLength = 0.02  # en metros

# Crear diccionario y tablero
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_5X5_1000)
board = aruco.CharucoBoard_create(squaresX, squaresY, squareLength, markerLength, aruco_dict)

# Detector
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, parameters)

all_corners = []
all_ids = []
img_size = None

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ No se pudo abrir la cámara")
    exit()

print("📷 Pulsa ESPACIO para capturar una imagen válida. ESC para terminar.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = detector.detectMarkers(gray)

    if len(corners) > 0:
        _, charuco_corners, charuco_ids = aruco.interpolateCornersCharuco(corners, ids, gray, board)
        aruco.drawDetectedCornersCharuco(frame, charuco_corners, charuco_ids)

    cv2.putText(frame, "ESPACIO = Capturar  |  ESC = Salir", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow("Captura para calibrar", frame)

    key = cv2.waitKey(1)
    if key == 27:  # ESC
        break
    elif key == 32 and len(corners) > 0 and charuco_ids is not None and len(charuco_ids) > 4:
        print(f"[+] Imagen capturada con {len(charuco_ids)} esquinas.")
        all_corners.append(charuco_corners)
        all_ids.append(charuco_ids)
        img_size = gray.shape[::-1]

cap.release()
cv2.destroyAllWindows()

if len(all_corners) < 5:
    print("❌ No hay suficientes capturas válidas.")
    exit()

print("🧠 Calculando calibración...")

ret, cameraMatrix, distCoeffs, rvecs, tvecs = aruco.calibrateCameraCharuco(
    all_corners, all_ids, board, img_size, None, None)

print("✅ Calibración completada.")
print("📌 Error RMS:", ret)
print("Matriz de cámara:")
print(cameraMatrix)
print("Coeficientes de distorsión:")
print(distCoeffs)

# Guardar en archivo
with open("camara.py", "w") as f:
    f.write("import numpy as np\n\n")
    f.write(f"cameraMatrix = np.array({cameraMatrix.tolist()})\n")
    f.write(f"distCoeffs = np.array({distCoeffs.tolist()})\n")
print("💾 Parámetros guardados en camara.py")
