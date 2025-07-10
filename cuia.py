import cv2
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
import time
import os
from wgpu.gui.offscreen import WgpuCanvas # Para el render offscreen
import pygfx as gfx
import pylinalg as la # Álgebra lineal para las transformaciones geométricas
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.transform import Rotation as R  # ✅ Añádelo al principio de tu archivo



def popup(titulo, imagen):
    if titulo == "Control_RA":
        cv2.imshow(titulo, imagen)

    while True:
        if cv2.waitKey(10) > 0:
            cv2.destroyWindow(titulo)
            break
        elif cv2.getWindowProperty(titulo, cv2.WND_PROP_VISIBLE) < 1:
            break

def plot(image, titulo=None, axis=False):
    dpi = mpl.rcParams['figure.dpi']
    if len(image.shape)==2:
        h, w = image.shape
        c = 1
    else:
        h, w, c = image.shape

    # What size does the figure need to be in inches to fit the image?
    figsize = w / float(dpi), h / float(dpi)

    # Create a figure of the right size with one axes that takes up the full figure
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes([0, 0, 1, 1])

    # Hide spines, ticks, etc.
    if not axis:
        ax.axis('off')
    if isinstance(titulo, str):
        plt.title(titulo)
    
    # Display the image.
    if c==4:
        plt.imshow( cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA) )
    elif c==1:
        plt.imshow( image, cmap='gray' )
    else:
        plt.imshow( cv2.cvtColor(image, cv2.COLOR_BGR2RGB) , aspect='equal')

def bestBackend(camid):
    backends = cv2.videoio_registry.getCameraBackends()
    bestCap = 0
    bestTime = 999
    for b in backends:
        start = time.time()
        cam = cv2.VideoCapture(camid, b)
        end = time.time()
        if cam.isOpened():
            if end-start < bestTime:
                bestTime = end-start
                bestCap = b
            cam.release()
    return bestCap

class myVideo:
    def __init__(self, source, backend=cv2.CAP_ANY):
        self.loop = False      # Para indicar si el video reiniciará al terminar
        self.process = None    # Función opcional de procesado de frames

        if isinstance(source, str):
            if os.path.exists(source):
                self._cap = cv2.VideoCapture(source)
                self._camera = False
                self._nextFrame = 0
                self._startTime = time.time()
                self._fps = self._cap.get(cv2.CAP_PROP_FPS)
                self._numFrames = self._cap.get(cv2.CAP_PROP_FRAME_COUNT)
                self._currentFrame = None
            else:
                self._cap = cv2.VideoCapture(source)
                self._camera = True  # Cámara IP o fuente inválida tratada como cámara
        elif isinstance(source, int):
            self._cap = cv2.VideoCapture(source, backend)
            self._camera = True

    def __del__(self):
        self._cap.release()

    def release(self):
        self._cap.release()
        del self

    def isOpened(self):
        return self._cap.isOpened()

    def read(self):
        if self._camera:
            ret, frame = self._cap.read()
            if ret:
                if self.process:
                    frame = self.process(frame)
                return ret, frame
            else:
                return False, None
        else:
            nextFrameStart = self._startTime + self._nextFrame / self._fps
            nextFrameEnd = self._startTime + (self._nextFrame + 1) / self._fps
            now = time.time()

            if now <= nextFrameStart:
                return True, self._currentFrame
            else:
                if now < nextFrameEnd:
                    correctFrame = self._nextFrame
                else:
                    correctFrame = int((now - self._startTime) * self._fps)

                if self.loop:
                    correctFrame = correctFrame % self._numFrames
                elif correctFrame >= self._numFrames:
                    return False, None

                if correctFrame != self._nextFrame:
                    self._cap.set(cv2.CAP_PROP_POS_FRAMES, correctFrame)

                ret, frame = self._cap.read()
                if ret:
                    self._currentFrame = frame
                    self._nextFrame = correctFrame + 1
                    if self.loop:
                        self._nextFrame = self._nextFrame % self._numFrames

                    if self.process:
                        frame = self.process(frame)

                return ret, frame

    def get(self, prop):
        return self._cap.get(prop)

    def set(self, prop, value):
        if prop == cv2.CAP_PROP_POS_FRAMES:
            self._nextFrame = value
        return self._cap.set(prop, value)

    def play(self, titulo, key=27):
    # Asegura que la ventana se crea correctamente con soporte para hilos
        cv2.startWindowThread()
        cv2.namedWindow(titulo, cv2.WINDOW_NORMAL)

        if self._cap.isOpened():
            print(f"[INFO] Cámara iniciada en ventana: {titulo}")
            while True:
                ret, frame = self.read()
                if not ret:
                    print("[INFO] No se pudo leer frame.")
                    break

                try:
                    if cv2.getWindowProperty(titulo, cv2.WND_PROP_VISIBLE) < 1:
                        print("[INFO] Ventana cerrada manualmente.")
                        break
                except cv2.error:
                    print("[WARN] No se pudo obtener propiedad de ventana. Asumiendo que fue cerrada.")
                    break

                if cv2.waitKey(20) == key:
                    print("[INFO] Tecla de salida pulsada.")
                    break

                if frame is not None:
                    # Mostrar frame en cualquier ventana (no solo 'Control_RA')
                    cv2.imshow(titulo, frame)

        cv2.destroyWindow(titulo)

def alphaBlending(fg, bg, x=0, y=0):
    sfg = fg.shape
    fgh = sfg[0]
    fgw = sfg[1]

    sbg = bg.shape
    bgh = sbg[0]
    bgw = sbg[1]

    h = max(bgh, y + fgh) - min(0, y)
    w = max(bgw, x + fgw) - min(0, x)

    CA = np.zeros(shape=(h, w, 3))
    aA = np.zeros(shape=(h, w))
    CB = np.zeros(shape=(h, w, 3))
    aB = np.zeros(shape=(h, w))

    bgx = max(0, -x)
    bgy = max(0, -y)

    if len(sbg) == 2 or sbg[2]==1:
        aB[bgy:bgy+bgh, bgx:bgx+bgw] = np.ones(shape=sbg)
        CB[bgy:bgy+bgh, bgx:bgx+bgw, :] = cv2.cvtColor(bg, cv2.COLOR_GRAY2BGR)
    elif sbg[2] == 3:
        aB[bgy:bgy+bgh, bgx:bgx+bgw] = np.ones(shape=sbg[0:2])
        CB[bgy:bgy+bgh, bgx:bgx+bgw, :] = bg
    else:
        aB[bgy:bgy+bgh, bgx:bgx+bgw] = bg[:, :, 3] / 255.0
        CB[bgy:bgy+bgh, bgx:bgx+bgw, :] = bg[:, :, 0:3]

    fgx = max(0, x)
    fgy = max(0, y)

    if len(sfg) == 2 or sfg[2]==1:
        aA[fgy:fgy+fgh, fgx:fgx+fgw] = np.ones(shape=sfg)
        CA[fgy:fgy+fgh, fgx:fgx+fgw, :] = cv2.cvtColor(fg, cv2.COLOR_GRAY2BGR)
    elif sfg[2] == 3:
        aA[fgy:fgy+fgh, fgx:fgx+fgw] = np.ones(shape=sfg[0:2])
        CA[fgy:fgy+fgh, fgx:fgx+fgw, :] = fg
    else:
        aA[fgy:fgy+fgh, fgx:fgx+fgw] = fg[:, :, 3] / 255.0
        CA[fgy:fgy+fgh, fgx:fgx+fgw, :] = fg[:, :, 0:3]

    aA = cv2.merge((aA, aA, aA))
    aB = cv2.merge((aB, aB, aB))
    a0 = aA + aB * (1 - aA)
    C0 = np.divide(((CA * aA) + (CB * aB)*(1.0 - aA)), a0, out=np.zeros_like(CA), where=(a0!=0))

    res = cv2.cvtColor(np.uint8(C0), cv2.COLOR_BGR2BGRA)
    res[:, :, 3] = np.uint8(a0[:, :, 0] * 255.0)

    return res

def proyeccion(puntos, rvec, tvec, cameraMatrix, distCoeffs):
    if isinstance(puntos, list):
        return(proyeccion(np.array(puntos, dtype=np.float32), rvec, tvec, cameraMatrix, distCoeffs))
    if isinstance(puntos, np.ndarray):
        if puntos.ndim == 1 and puntos.size == 3:
            res, _ = cv2.projectPoints(puntos.astype(np.float32), rvec, tvec, cameraMatrix, distCoeffs)
            return(res[0][0].astype(int))
        if puntos.ndim > 1:
            aux = proyeccion(puntos[0], rvec, tvec, cameraMatrix, distCoeffs)
            aux = np.expand_dims(aux, axis=0)
            for p in puntos[1:]:
                aux = np.append(aux, [proyeccion(p, rvec, tvec, cameraMatrix, distCoeffs)], axis=0)
            return(np.array(aux))

def histogramahsv(imagen, solotono=True):
    if solotono:
        hist, (ax1) = plt.subplots(1)
    else:
        hist, (ax1, ax2, ax3) = plt.subplots(1,3)
    framehsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(framehsv)
    histoh = cv2.calcHist( [framehsv], [0], None, [180], [0, 180])
    ax1.set_title("Hue")
    ax1.get_yaxis().set_visible(False)
    ax1.plot(histoh)
    if not solotono:
        histos = cv2.calcHist( [framehsv], [1], None, [256], [0, 256])
        ax2.set_title("Sat")
        ax2.get_yaxis().set_visible(False)
        ax2.plot(histos)
        histov = cv2.calcHist( [framehsv], [2], None, [256], [0, 256])
        ax3.set_title("Val")
        ax3.get_yaxis().set_visible(False)
        ax3.plot(histov)
    plt.show()

class matrizDeTransformacion:
    def __init__(self, matrix=None):
        # Inicializa la matriz como una identidad 4x4 si no se especifica ninguna
        self.matrix = matrix if matrix is not None else np.eye(4)

    @staticmethod
    def traslacion(tx, ty, tz):
        mat = np.eye(4)
        mat[:3, 3] = [tx, ty, tz]
        return matrizDeTransformacion(mat)

    @staticmethod
    def rotacion(axis, angulo):
        mat = np.eye(4)
        c, s = np.cos(angulo), np.sin(angulo)

        if axis == 'x':
            mat[:3, :3] = [[1, 0, 0],
                           [0, c, -s],
                           [0, s, c]]
        elif axis == 'y':
            mat[:3, :3] = [[c, 0, s],
                           [0, 1, 0],
                           [-s, 0, c]]
        elif axis == 'z':
            mat[:3, :3] = [[c, -s, 0],
                           [s, c, 0],
                           [0, 0, 1]]
        else:
            raise ValueError("El eje debe ser 'x', 'y' o 'z'.")
        
        return matrizDeTransformacion(mat)

    @staticmethod
    def escalado(sx=1, sy=1, sz=1):
        mat = np.eye(4)
        mat[0, 0] = sx
        mat[1, 1] = sy
        mat[2, 2] = sz
        return matrizDeTransformacion(mat)

    @staticmethod
    def rotacion_con_cuaternion(q):
        x, y, z, w = q

        # Normaliza el cuaternión
        norm = np.sqrt(x**2 + y**2 + z**2 + w**2)
        x, y, z, w = x / norm, y / norm, z / norm, w / norm

        # Calcula la matriz de rotación 3x3
        matriz_rotacion = np.array([
            [1 - 2*(y**2 + z**2), 2*(x*y - z*w), 2*(x*z + y*w)],
            [2*(x*y + z*w), 1 - 2*(x**2 + z**2), 2*(y*z - x*w)],
            [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x**2 + y**2)]
        ])

        # Convierte a matriz homogénea
        matriz = np.eye(4)
        matriz[:3, :3] = matriz_rotacion

        return matrizDeTransformacion(matriz)
    
    def __matmul__(self, other):
        # Operador @ para la composición de matrices.
        if not isinstance(other, matrizDeTransformacion):
            raise TypeError("El operador solo puede aplicarse entre instancias de matrizDeTransformacion.")
        return matrizDeTransformacion(np.matmul(self.matrix, other.matrix))

    def __array__(self):
        # Convierte la instancia a un np.array.
        return self.matrix

    @property
    def shape(self):
        return(self.matrix.shape)
    
    def __repr__(self):
        return f"matrizDeTransformacion(\n{self.matrix}\n)"

class modeloGLTF:
    def __init__(self, ruta_modelo=None):
        self.model_obj = None  
        self.gltf = None
        self.current_action = None
        if ruta_modelo:
            self.cargar(ruta_modelo)
        self.indice_animacion = None
        self.skeleton_helper = None

    def cargar(self, ruta_modelo):
        if self.model_obj:
            self.model_obj.remove()
        self.gltf = gfx.load_gltf(ruta_modelo)
        self.seleccionar_escena() # Selecciona la escena por defecto dentro del modelo GLTF
        self.skeleton_helper = gfx.SkeletonHelper(self.model_obj)
        self.skeleton_helper.visible = False

    def seleccionar_escena(self, indice=None):
        if self.gltf:
            if indice is None:
                if self.gltf.scene is not None:
                    self.model_obj = self.gltf.scene
                else:
                    self.model_obj = self.gltf.scenes[0]
            elif indice >= 0 and indice < len(self.gltf.scenes):
                self.model_obj = self.gltf.scenes[indice]
            else:
                raise ValueError("Índice de escena fuera de rango")
        else:
            raise ValueError("No hay modelo GLTF cargado")

    def escalar(self, escala):
        if isinstance(escala, tuple):
            self.model_obj.local.scale = (escala[0], escala[1], escala[2])
        else:
            # Si solo se indica un número se hace un escalado unidorme
            self.model_obj.local.scale = (escala, escala, escala)

    def rotar(self, rotacion):
        q = la.quat_from_euler(rotacion)
        self.model_obj.local.rotation = la.quat_mul(q, self.model_obj.local.rotation)

    def trasladar(self, posicion):
        self.model_obj.local.position = posicion

    def flotar(self):
        deltaZ = -self.model_obj.get_world_bounding_box()[0][2]
        pos = np.array(self.model_obj.local.position)
        pos[2] += deltaZ
        self.trasladar(pos)

    def animaciones(self):
        if not self.gltf or not self.gltf.animations:
            return []
        nombres = []
        for i, animation in enumerate(self.gltf.animations):
            nombre = animation.name if animation.name else f"Anim_{i}"
            nombres.append(nombre)
            
        return nombres

    def animar(self, nombre):
        if not self.gltf or not self.gltf.animations:
            return False

        for i, animation in enumerate(self.gltf.animations):
            nombre_animacion = animation.name if animation.name else f"Anim_{i}"
            if nombre_animacion == nombre:
                self.indice_animacion = i
                self.current_action = animation  # Guardar la animación actual
                return True
        
        return False

class escenaPYGFX:
    def __init__(self, fov, ancho, alto):
        self.mixer = gfx.AnimationMixer()
        self.clock = gfx.Clock()
        self.scene = gfx.Scene()
        self.scene.background = None  # Fondo transparente    
        self.canvas = WgpuCanvas(size=(ancho, alto))
        self.renderer = gfx.WgpuRenderer(self.canvas)
        self.camera = gfx.PerspectiveCamera(fov, aspect=ancho/alto, width=ancho, height=alto, depth_range=(0.1, 1000))
        self.renderer.render(self.scene, self.camera)
        


    def iluminar(self, intensidad=1.0):
        ambient_light = gfx.AmbientLight(intensidad)
        self.scene.add(ambient_light)
        
    def agregar_modelo(self, modelo):
        if hasattr(modelo, "model_obj"):
            # modeloGLTF
            skeleton_helper = gfx.SkeletonHelper(modelo.model_obj)
            skeleton_helper.visible = False
            self.scene.add(skeleton_helper)
            self.scene.add(modelo.model_obj)

            if not hasattr(self, "avatar") or self.avatar is None:
                self.avatar = modelo

            if modelo.indice_animacion is not None:
                action = self.mixer.clip_action(modelo.current_action)
                action.play()
                self.mixer.update(0.0)
        else:
            # gfx.Mesh, texto, iconos
            self.scene.add(modelo)

    
    def ilumina_modelo(self, modelo, intensidad=0.5):
        radio = modelo.model_obj.get_world_bounding_sphere()[3]
        posicion = modelo.model_obj.local.position
        luces = [(1, 1, 1), (1, -1, 1), (-1, 1, 1), (-1, -1, 1), (1, 1, -1), (1, -1, -1), (-1, 1, -1), (-1, -1, -1)]
        for posluz in luces:
            light = gfx.DirectionalLight(color=(1, 1, 1), intensity=intensidad)
            pos = np.sum([[posicion], [posluz]], axis=0)
            pos = pos / np.linalg.norm(pos) * 2 * radio
            light.local.position = pos
            light.look_at(posicion)
            self.scene.add(light)

    def actualizar_camara(self, matriz):
        self.camera.local.matrix = matriz

    def mostrar_ejes(self, size=1.0, thickness=2):
        axis = gfx.AxesHelper(size, thickness)
        self.scene.add(axis)

    def render(self):
        dt = self.clock.get_delta()
        self.mixer.update(dt)  # Importante: actualizar el mixer antes de renderizar
        self.renderer.render(self.scene, self.camera)
        return np.array(self.canvas.draw())
        
    def mostrar_texto(self, texto, color=(255, 255, 255), fondo=(30, 30, 30), tamaño=24, escala=0.005):
        """
        Crea un panel flotante con texto y lo añade a la escena.
        """
        # Eliminar panel anterior si ya existe
        if hasattr(self, 'panel_texto') and self.panel_texto:
            self.scene.remove(self.panel_texto)

        # Crear imagen PIL
        ancho, alto = 512, 128
        img = Image.new("RGB", (ancho, alto), color=fondo)
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", tamaño)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), texto, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((ancho - w) / 2, (alto - h) / 2), texto, font=font, fill=color)


        # Convertir a textura
        tex_data = np.array(img).astype(np.uint8)
        tex = gfx.Texture(tex_data, dim=2)
        material = gfx.MeshBasicMaterial(map=tex)

        # Crear plano y escalarlo
        geometry = gfx.plane_geometry(1, alto / ancho)
        self.panel_texto = gfx.Mesh(geometry, material)
        self.panel_texto.local.scale = (escala * ancho, escala * alto, 1)
        self.panel_texto.local.position = (0, 1.2, 0)  # encima del avatar, por ejemplo

        self.scene.add(self.panel_texto)

    def agregar(self, objeto):
        self.scene.add(objeto)

    def avatar_transform(self, matriz):
        if hasattr(self, 'avatar') and self.avatar:
            m = matriz.matrix  # matriz 4x4

            # ✅ Asignar posición
            self.avatar.model_obj.local.position = m[:3, 3].tolist()

            # ✅ Convertir rotación 3x3 a cuaternión
            rot_matrix = m[:3, :3]
            q = R.from_matrix(rot_matrix).as_quat()  # Devuelve (x, y, z, w)
            self.avatar.model_obj.local.rotation = tuple(q)

def pose_to_matrix(rvec, tvec):
    """
    Convierte un par (rvec, tvec) de OpenCV en una matriz de transformación homogénea 4x4.
    """
    rot_matrix, _ = cv2.Rodrigues(rvec)
    matriz = np.eye(4)
    matriz[:3, :3] = rot_matrix
    matriz[:3, 3] = tvec
    return matrizDeTransformacion(matriz)

