from cuia import myVideo
import cv2
import numpy as np

def inicializar_camara():
    cam = myVideo(0)  # usa la cámara por defecto
    if not cam.isOpened():
        raise Exception("No se pudo abrir la cámara")
    return cam

def encontrar_primera_camara_disponible():
       backends = [cv2.CAP_V4L2, cv2.CAP_GSTREAMER, cv2.CAP_ANY]
       for i in range(5):
              for backend in backends:
                     cap = cv2.VideoCapture(i, backend)
                     if cap.isOpened():
                            cap.release()
                     print(f"🎥 Available camera detected at index {i} with backend {backend}")
                     return i, backend
              cap.release()
       return None, None



cameraMatrix = np.array([[889.09906685,   0.        , 638.99038196],
       [  0.        , 885.24125141, 335.81104161],
       [  0.        ,   0.        ,   1.        ]])
distCoeffs = np.array([[ 0.24180161, -0.7027217 , -0.00906317, -0.00289352,  0.67550615]])

