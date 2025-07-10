import cv2
import numpy as np
import cuia
import importlib.util

def ejecutar_ar_con_modelo(path_modelo, escala_modelo):

    # Obtener resolución de la cámara
    cam = 0
    bk = cuia.bestBackend(cam)
    webcam = cv2.VideoCapture(cam, bk)
    ancho = int(webcam.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto = int(webcam.get(cv2.CAP_PROP_FRAME_HEIGHT))
    webcam.release()

    # Cargar calibración de cámara desde archivo externo (o usar valores por defecto si falla)
    try:
        path_calibracion = "calibracion/camara.py"
        spec = importlib.util.spec_from_file_location("camara", path_calibracion)
        camara = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(camara)
        cameraMatrix = camara.cameraMatrix
        distCoeffs = camara.distCoeffs
        print("✅ Calibración cargada correctamente desde calibracion/camara.py")
    except Exception as e:
        print(f"⚠️ No se pudo cargar calibración: {e}")
        print("⛔ Usando parámetros por defecto")
        cameraMatrix = np.array([[1000, 0, ancho / 2],
                                 [0, 1000, alto / 2],
                                 [0, 0, 1]], dtype=np.float32)
        distCoeffs = np.zeros((5, 1), dtype=np.float32)

    # Cargar el modelo 3D y aplicar escala, rotación y ajuste de posición
    modelo = cuia.modeloGLTF(path_modelo)
    modelo.escalar(escala_modelo)
    modelo.flotar()
    modelo.rotar((np.pi / 2, 0, 0))  # Gira 90º para que se muestre de pie sobre el marcador

    # Correcciones personalizadas de posición para algunos modelos concretos
    if "silla_madera_vintage" in path_modelo:
        modelo.trasladar((-0.25, -0.25, 0))
    elif "sofa_rojo" in path_modelo:
        modelo.trasladar((0, 0, 0))
    elif "silla_madera_moderna" in path_modelo:
        modelo.trasladar((0, 0, 0.)) 
    elif "mesa_con_silla" in path_modelo:
        modelo.trasladar((0, 0, 0))  
    elif "plantas_decorativas" in path_modelo:
        modelo.trasladar((0, 0, 0))  
    elif "mesa_minimalista" in path_modelo:
        modelo.trasladar((0, 0, 0))  

    # Animar el modelo si tiene animaciones
    anims = modelo.animaciones()
    if anims:
        modelo.animar(anims[0])  # Lanza la primera animación disponible

    # Convierte pose de OpenCV (rvec, tvec) a matriz de transformación de pygfx
    def fromOpencvToPygfx(rvec, tvec):
        pose = np.eye(4)
        pose[0:3, 3] = tvec.T
        pose[0:3, 0:3] = cv2.Rodrigues(rvec)[0]
        pose[1:3] *= -1  # Ajuste de orientación a sistema de coordenadas pygfx
        pose = np.linalg.inv(pose)
        return pose

    # Calcula campo de visión (FOV) a partir de la matriz de cámara y resolución
    def fov(cameraMatrix, ancho, alto):
        f = cameraMatrix[1, 1] if ancho > alto else cameraMatrix[0, 0]
        fov_rad = 2 * np.arctan((alto if ancho > alto else ancho) / (2 * f))
        return np.rad2deg(fov_rad)

    # Inicializa la escena con la cámara virtual y agrega el modelo y luces
    escena = cuia.escenaPYGFX(fov(cameraMatrix, ancho, alto), ancho, alto)
    escena.agregar_modelo(modelo)
    escena.ilumina_modelo(modelo)
    escena.iluminar()

    # Inicializa la captura de vídeo
    ar = cuia.myVideo(cam, bk)

    # Crea el detector de marcadores ArUco
    diccionario = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    detector = cv2.aruco.ArucoDetector(diccionario)

    # Detección de pose: calcula posición y orientación del marcador
    def detectarPose(frame, tam):
        bboxs, ids, rechazados = detector.detectMarkers(frame)
        print("IDs detectados:", ids)
        print("Bounding boxes:", bboxs)

        if ids is not None:
            objPoints = np.array([[-tam / 2.0, tam / 2.0, 0.0],
                                  [tam / 2.0, tam / 2.0, 0.0],
                                  [tam / 2.0, -tam / 2.0, 0.0],
                                  [-tam / 2.0, -tam / 2.0, 0.0]])
            resultado = {}
            for i in range(len(ids)):
                ret, rvec, tvec = cv2.solvePnP(objPoints, bboxs[i], cameraMatrix, distCoeffs)
                if ret:
                    resultado[ids[i][0]] = (rvec, tvec, bboxs[i])
            return True, resultado
        return False, None

    # Renderizado final: mezcla el modelo 3D sobre la imagen de la webcam
    def realidadMixta(frame):
        ret, pose = detectarPose(frame, 0.20)
        frame_copy = frame.copy()

        if ret and pose:
            primer_id = list(pose.keys())[0]
            rvec, tvec, bbox = pose[primer_id]

            print("✅ Marcador detectado:", primer_id)
            cv2.aruco.drawDetectedMarkers(frame_copy, [bbox], np.array([primer_id]))

            M = fromOpencvToPygfx(rvec, tvec)
            escena.actualizar_camara(M)
            imagen_render = escena.render()
            imagen_render_bgr = cv2.cvtColor(imagen_render, cv2.COLOR_RGBA2BGRA)
            resultado = cuia.alphaBlending(imagen_render_bgr, frame_copy)
        else:
            resultado = frame
        return resultado

    ar.process = realidadMixta

    # Ejecuta el bucle principal de la aplicación (ventana abierta hasta que se pulse espacio)
    try:
        ar.play("Realidad Aumentada ArUco con GLTF", key=ord(' '))
    finally:
        ar.release()