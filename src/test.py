
import cv2
import numpy as np

cameraMatrix = np.array([[1312.67859, 0.0, 964.637845], [0.0, 1308.9774, 541.434512], [0.0, 0.0, 1.0]], dtype=np.float32)
distCoeffs = np.zeros((5, 1))  # ← sin distorsión

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ No se pudo abrir la cámara")
    exit()

ret, frame = cap.read()
if not ret:
    print("❌ No se pudo capturar frame")
    exit()

h, w = frame.shape[:2]
new_camera_matrix, _ = cv2.getOptimalNewCameraMatrix(cameraMatrix, distCoeffs, (w, h), 1, (w, h))

while True:
    ret, frame = cap.read()
    if not ret:
        break

    corregido = cv2.undistort(frame, cameraMatrix, distCoeffs, None, new_camera_matrix)

    combinado = cv2.hconcat([frame, corregido])
    cv2.imshow("Original (izq) vs Corregido (der)", combinado)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
