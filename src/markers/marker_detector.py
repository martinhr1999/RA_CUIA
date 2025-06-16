import cv2
import numpy as np
import cv2.aruco as aruco
from utils.camara import cameraMatrix, distCoeffs  # ← usa tu calibración real

# Diccionario ArUco 5x5 con 1000 marcadores (coincide con tu SVG)
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_5X5_1000)
detector = aruco.ArucoDetector(aruco_dict)

def detectar_marcador(frame, return_corners=False):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    corners, ids, _ = detector.detectMarkers(gray)

    if ids is not None and len(ids) > 0:
        id_detectado = int(ids[0][0])

        # Estimar pose
        rvec, tvec, _ = aruco.estimatePoseSingleMarkers(corners, 0.13, cameraMatrix, distCoeffs)

        rvec = rvec[0][0] if rvec.ndim == 3 else rvec[0]
        tvec = tvec[0][0] if tvec.ndim == 3 else tvec[0]

        if return_corners:
            return id_detectado, rvec, tvec, corners
        return id_detectado, rvec, tvec

    if return_corners:
        return None, None, None, None
    return None, None, None
