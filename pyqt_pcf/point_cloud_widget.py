from OpenGL.arrays import vbo
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QPointF
from OpenGL.GL import *
import open3d as o3d
import numpy as np
import laspy
import pywavefront
import os
from pc_forestry.pcd.PCD import PCD


class OpenGLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super(OpenGLWidget, self).__init__(parent)
        self.point_clouds = {}
        self.models = {}
        self.scale_factor = 2
        self.last_mouse_position = None
        self.rotation_x = 1
        self.rotation_y = 1
        self.rotation_z = 1
        self.rotation_mode = "Z"
        self.point_cloud_position = QPointF(0, 0)  # Текущее положение облака точек
        self.scene_center = np.array([0.0, 0.0, 0.0])
        self.point_size = 3

        self.vbo = None
        self.num_points = 0
        self.color = (1.0, 1.0, 1.0)  # Белый цвет по умолчанию

        self.vbo_data = {}
        self.vbo_data_models = {}

    def to_VBO(self, pc: PCD, color_field: str = 'intensity'):
        points = pc.points

        if color_field == 'rgb' and pc.rgb.size > 0:
            colors = pc.rgb / 255.0
        elif hasattr(pc, color_field) and getattr(pc, color_field).size > 0:
            field_values = np.asarray(getattr(pc, color_field))
            field_values = (field_values - field_values.min()) / \
                (field_values.max() - field_values.min())
            colors = np.zeros((field_values.shape[0], 3))
            colors[:, 0] = field_values  # r
            colors[:, 1] = field_values  # g
            colors[:, 2] = field_values  # b
        else:
            colors = np.ones_like(points)

        point_vbo = vbo.VBO(np.array(points, dtype=np.float32))
        color_vbo = vbo.VBO(np.array(colors, dtype=np.float32))
        return point_vbo, color_vbo, len(points)

    def load_point_cloud(self, filename):
        if filename not in self.point_clouds:
            self.point_clouds[filename] = {'active': False, 'data': None}

        if filename in self.vbo_data:
            self.point_clouds[filename]['active'] = True
            self.update()
            return

        try:
            pc = PCD.read(filename, verbose=False)
        except Exception as e:
            print(f"Ошибка при загрузке файла {filename}: {e}")
            if not self.point_clouds[filename]['data']:
                del self.point_clouds[filename]
            return

        if pc.points.size == 0:
            print(f"В файле {filename} не найдено точек")
            if not self.point_clouds[filename]['data']:
                del self.point_clouds[filename]
            return

        point_vbo, color_vbo, num_points = self.to_VBO(pc)

        self.vbo_data[filename] = (point_vbo, color_vbo, num_points)
        self.point_clouds[filename] = {'active': True, 'data': pc.points}
        self.scale_factor = self.calculate_scale_factor_for_all()
        self.update()

    def load_model(self, filename):
        if filename not in self.models:
            self.models[filename] = {'active': False, 'data': None}

        if filename in self.vbo_data_models:
            self.models[filename]['active'] = True
            self.update()
            return

        file_extension = os.path.splitext(filename)[1].lower()
        if file_extension == '.obj':
            scene = pywavefront.Wavefront(filename, collect_faces=True)
            vertices = []
            total_faces = 0
            for _, mesh in scene.meshes.items():
                total_faces += len(mesh.faces)
                for face in mesh.faces:
                    vertices.extend([scene.vertices[index] for index in face])
            points = np.array(vertices, dtype=np.float32)
            colors = np.ones((len(points), 3))  # Белый цвет для всех вершин
        else:
            print("Unsupported file format")
            return

        point_vbo = vbo.VBO(points)
        color_vbo = vbo.VBO(colors)
        self.vbo_data_models[filename] = (point_vbo, color_vbo, len(points))
        self.models[filename] = {
            'active': True,
            'data': points,
            'num_polygons': total_faces
        }
        self.scale_factor = self.calculate_scale_factor_for_all()
        self.update()

    def calculate_scale_factor_for_all(self):
        all_points_list = []
        if self.vbo_data:
            for key in self.vbo_data:
                if self.point_clouds.get(key, {}).get('active'):
                    cloud_data = self.point_clouds[key].get('data')
                    if cloud_data is not None and cloud_data.size > 0:
                        all_points_list.append(cloud_data)

        if self.vbo_data_models:
            for key in self.vbo_data_models:
                if self.models.get(key, {}).get('active'):
                    model_data = self.models[key].get('data')
                    if model_data is not None and model_data.size > 0:
                        all_points_list.append(model_data)

        if not all_points_list:
            self.scene_center = np.array([0.0, 0.0, 0.0])
            return 1.0

        all_points = np.vstack(all_points_list)
        min_bounds = np.min(all_points, axis=0)
        max_bounds = np.max(all_points, axis=0)

        self.scene_center = (min_bounds + max_bounds) / 2.0

        scene_size = max_bounds - min_bounds
        max_dim = np.max(scene_size) if scene_size.size > 0 else 0

        scale_factor = 1.5 / max_dim if max_dim != 0 else 1.0
        return scale_factor

    def resizeGL(self, width, height):
        # Определяем размеры окна
        if height == 0:
            height = 1

        # Устанавливаем область отображения OpenGL
        glViewport(0, 0, width, height)

        # Модифицируем проекционную матрицу так, чтобы сохранить пропорции контента
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect_ratio = width / height
        if aspect_ratio > 1:
            glOrtho(-aspect_ratio, aspect_ratio, -1.0, 1.0, -1.0, 1.0)
        else:
            glOrtho(-1.0, 1.0, -1 / aspect_ratio, 1 / aspect_ratio, -1.0, 1.0)

        glMatrixMode(GL_MODELVIEW)

    def set_view_parameters(self, x, y, z):
        self.scale_factor = self.calculate_scale_factor_for_all()
        self.rotation_x = x
        self.rotation_y = y
        self.rotation_z = z
        self.point_cloud_position = QPointF(0, 0)
        self.update()  # Обновляем виджет, чтобы отобразить изменения

    def focus_on_object(self, filename):
        """
        Фокусируется на указанном объекте (облаке точек или модели).
        """
        target_data = None
        if filename in self.point_clouds and self.point_clouds[filename]['active']:
            target_data = self.point_clouds[filename]['data']
        elif filename in self.models and self.models[filename]['active']:
            target_data = self.models[filename]['data']

        if target_data is not None and target_data.size > 0:
            min_bounds = np.min(target_data, axis=0)
            max_bounds = np.max(target_data, axis=0)

            self.scene_center = (min_bounds + max_bounds) / 2.0

            scene_size = max_bounds - min_bounds
            max_dim = np.max(scene_size) if scene_size.size > 0 else 0

            self.scale_factor = 1.5 / max_dim if max_dim != 0 else 1.0
            self.point_cloud_position = QPointF(0, 0)  # Сбрасываем смещение
            self.update()

    def initializeGL(self):
        glClearColor(0.15, 0.15, 0.15, 1)
        glEnable(GL_DEPTH_TEST)

        self.vbo = vbo.VBO(np.array([], dtype=np.float32))
        self.color_vbo = vbo.VBO(np.array([], dtype=np.float32))

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        glPointSize(self.point_size)

        # Трансформации применяются в обратном порядке:
        # 4. Перемещение (панорамирование) мышью
        glTranslatef(self.point_cloud_position.x(), -self.point_cloud_position.y(), 0)
        # 3. Масштабирование (зум)
        glScalef(self.scale_factor, self.scale_factor, self.scale_factor)
        # 2. Вращение
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)
        glRotatef(self.rotation_z, 0, 0, 1)
        # 1. Центрирование сцены/объекта в начале координат
        glTranslatef(-self.scene_center[0], -self.scene_center[1], -self.scene_center[2])

        # Отрисовка всех облаков точек
        for filename, cloud_info in self.point_clouds.items():
            if cloud_info['active']:  # Проверяем, активно ли облако
                if filename in self.vbo_data:
                    point_vbo, color_vbo, num_points = self.vbo_data[filename]
                    point_vbo.bind()
                    glVertexPointer(3, GL_FLOAT, 0, None)
                    glEnableClientState(GL_VERTEX_ARRAY)

                    color_vbo.bind()
                    glColorPointer(3, GL_FLOAT, 0, None)
                    glEnableClientState(GL_COLOR_ARRAY)

                    glDrawArrays(GL_POINTS, 0, num_points)

                    glDisableClientState(GL_VERTEX_ARRAY)
                    glDisableClientState(GL_COLOR_ARRAY)
                    point_vbo.unbind()
                    color_vbo.unbind()

        glDisableClientState(GL_VERTEX_ARRAY)
        glPopMatrix()
        # self.update() # Этот вызов не нужен здесь, он вызывает бесконечную перерисовку

    def increase_point_size(self):
        self.point_size += 1
        self.update()

    def decrease_point_size(self):
        if self.point_size > 1:
            self.point_size -= 1
            self.update()

    def set_scale_factor(self, scale):
        self.scale_factor = scale
        self.update()

    def mousePressEvent(self, event):
        self.last_mouse_position = event.position()
        if event.buttons() == Qt.MouseButton.MiddleButton:
            # Изменение режима вращения при нажатии на среднюю кнопку мыши
            self.rotation_mode = "X" if self.rotation_mode == "Z" else "Z"
            self.update()

    def normalize_angle(self, angle):
        while angle < 0:
            angle += 360
        while angle >= 360:
            angle = 0
        return angle

    def mouseMoveEvent(self, event):
        rotation_sensitivity = 0.3  # Коэффициент чувствительности вращения

        if (self.last_mouse_position and event.buttons() == Qt.MouseButton.LeftButton):
            delta = event.position() - self.last_mouse_position
            if self.rotation_mode == "Z":
                self.rotation_x += delta.y() * rotation_sensitivity
                self.rotation_y += delta.x() * rotation_sensitivity
            else:
                self.rotation_z -= delta.x() * rotation_sensitivity

            # Нормализуем углы поворота
            self.rotation_x = self.normalize_angle(self.rotation_x)
            self.rotation_y = self.normalize_angle(self.rotation_y)
            self.rotation_z = self.normalize_angle(self.rotation_z)

            self.last_mouse_position = event.position()
            self.update()

        shift_sensitivity = 0.00285 / self.scale_factor  # Коэффициент чувствительности смещения

        if (self.last_mouse_position and event.buttons() == Qt.MouseButton.RightButton):
            delta = event.position() - self.last_mouse_position
            self.point_cloud_position += delta * shift_sensitivity
            self.last_mouse_position = event.position()
            self.update()

    def mouseReleaseEvent(self, event):
        self.last_mouse_position = None

    def wheelEvent(self, event):
        angle = event.angleDelta().y()

        # Определение коэффициента изменения масштаба
        scale_factor_change = 1.1  # Увеличение или уменьшение масштаба на 10%
        if angle > 0:
            self.scale_factor *= scale_factor_change
        else:
            self.scale_factor /= scale_factor_change

        # Предотвращение слишком маленького или слишком большого масштаба
        if self.scale_factor < 0.005:
            self.scale_factor = 0.005
        elif self.scale_factor > 100:
            self.scale_factor = 100

        self.update()
