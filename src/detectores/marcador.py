import cv2
import numpy as np

# Configuración del diccionario ArUco
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
detector_params = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(aruco_dict, detector_params)

def detectar_marcador(frame, return_corners=False):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_1000)
    detector = cv2.aruco.ArucoDetector(aruco_dict)
    corners, ids, _ = detector.detectMarkers(gray)

    if ids is not None:
        id_detectado = ids[0][0]
        rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(corners, 0.05, cameraMatrix, distCoeffs)
        if return_corners:
            return id_detectado, rvec[0][0], tvec[0][0], corners
        return id_detectado, rvec[0][0], tvec[0][0]
    
    if return_corners:
        return None, None, None, None
    return None, None, None
