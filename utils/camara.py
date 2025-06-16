import numpy as np
import cv2

import numpy as np
cameraMatrix = np.array([[1.45138270e+03, 0.00000000e+00, 9.66833116e+02],
       [0.00000000e+00, 1.44648417e+03, 5.42420160e+02],
       [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
distCoeffs = np.zeros((5, 1))  # ← sin distorsión


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

