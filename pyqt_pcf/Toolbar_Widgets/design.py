import os

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import (QHBoxLayout, QListWidget, QDockWidget,
                             QListWidgetItem, QCheckBox, QVBoxLayout, QWidget, QPushButton, QLabel, QStackedWidget, QComboBox, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont, QPixmap

from point_cloud_widget import OpenGLWidget
from config import base_path

# Пример!!!
from Toolbar_Widgets import parameters_widget


class EmptyStateWidget(QWidget):
    """Виджет для отображения пустого состояния с drag and drop подсказкой"""

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setAcceptDrops(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Иконка файла
        icon_label = QLabel()
        icon_path = os.path.join(base_path, "images", "generated-image(3).png")
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            # Масштабируем иконку до размера 72x72 пикселя с сохранением пропорций
            scaled_pixmap = pixmap.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)
        else:
            # Если иконка не найдена, используем текст как fallback
            icon_label.setText("📁")
            icon_font = QFont()
            icon_font.setPointSize(72)
            icon_label.setFont(icon_font)

        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Применяем прозрачность через стиль
        icon_label.setStyleSheet("color: rgba(136, 136, 136, 0.3); opacity: 0.3;")
        layout.addWidget(icon_label)

        # Основной текст
        main_label = QLabel("Перетащите файлы сюда")
        main_font = QFont()
        main_font.setPointSize(18)
        main_font.setBold(True)
        main_label.setFont(main_font)
        main_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_label.setStyleSheet("color: #888888; margin: 20px 0px;")
        layout.addWidget(main_label)

        # Дополнительный текст
        sub_label = QLabel("или откройте через Ctrl+O")
        sub_font = QFont()
        sub_font.setPointSize(12)
        sub_label.setFont(sub_font)
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_label.setStyleSheet("color: #777777; margin-bottom: 20px;")
        layout.addWidget(sub_label)

        # Форматы файлов
        formats_label = QLabel("Поддерживаемые форматы:\n.las • .pcd • .laz • .h5 • .txt")
        formats_font = QFont()
        formats_font.setPointSize(10)
        formats_label.setFont(formats_font)
        formats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        formats_label.setStyleSheet("color: #555555;")
        layout.addWidget(formats_label)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Обработка события входа перетаскиваемых данных"""
        if event.mimeData().hasUrls():
            # Проверяем, есть ли среди перетаскиваемых объектов файлы
            urls = event.mimeData().urls()
            valid_files = []

            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    # Проверяем расширение файла
                    if file_path.lower().endswith(('.las', '.pcd', '.laz', '.h5', '.txt')):
                        valid_files.append(file_path)

            if valid_files:
                event.acceptProposedAction()
                return

        event.ignore()

    def dragMoveEvent(self, event):
        """Обработка события перемещения при перетаскивании"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """Обработка события сброса файлов"""
        if event.mimeData().hasUrls() and self.main_window:
            urls = event.mimeData().urls()
            valid_files = []

            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    # Проверяем расширение файла
                    if file_path.lower().endswith(('.las', '.pcd', '.laz', '.h5', '.txt')):
                        valid_files.append(file_path)

            if valid_files:
                self.main_window.add_files_to_list(valid_files)
                event.acceptProposedAction()
                print(f"Перетащено файлов: {len(valid_files)}")
            else:
                print("Нет поддерживаемых файлов для загрузки")
                event.ignore()
        else:
            event.ignore()


class DragDropListWidget(QListWidget):
    """Кастомный QListWidget с поддержкой drag and drop"""

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Обработка события входа перетаскиваемых данных"""
        if event.mimeData().hasUrls():
            # Проверяем, есть ли среди перетаскиваемых объектов файлы
            urls = event.mimeData().urls()
            valid_files = []

            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    # Проверяем расширение файла
                    if file_path.lower().endswith(('.las', '.pcd', '.laz', '.h5', '.txt')):
                        valid_files.append(file_path)

            if valid_files:
                event.acceptProposedAction()
                return

        event.ignore()

    def dragMoveEvent(self, event):
        """Обработка события перемещения при перетаскивании"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """Обработка события сброса файлов"""
        if event.mimeData().hasUrls() and self.main_window:
            urls = event.mimeData().urls()
            valid_files = []

            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    # Проверяем расширение файла
                    if file_path.lower().endswith(('.las', '.pcd', '.laz', '.h5', '.txt')):
                        valid_files.append(file_path)

            if valid_files:
                self.main_window.add_files_to_list(valid_files)
                event.acceptProposedAction()
                print(f"Перетащено файлов в список: {len(valid_files)}")
            else:
                print("Нет поддерживаемых файлов для загрузки")
                event.ignore()
        else:
            event.ignore()


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowTitle("LIDAR segmentation and modeling")
        MainWindow.resize(2560, 1440)
        MainWindow.showMaximized()
        # Центральный виджет
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setProperty("class", "custom-widget")
        # Создаем вертикальную компоновку для centralwidget
        self.centralLayout = QVBoxLayout(self.centralwidget)
        self.centralLayout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы

        self.openGLWidget = OpenGLWidget(parent=self.centralwidget)
        self.openGLWidget.setObjectName("openGLWidget")
        self.centralLayout.addWidget(self.openGLWidget)

        MainWindow.setCentralWidget(self.centralwidget)

        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        # Стыковочные виджеты
        self.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea, self.files_dock_widget())
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,
                           self.properties_dock_widget())

    def update_list(self, list):
        list.clear()
        for file_name in self.openGLWidget.point_clouds:
            if self.openGLWidget.point_clouds[file_name]['active']:
                list.addItem(file_name)

    def init_dock_widgets(self):
        self.dock_widgets = {
            'parameters': parameters_widget.parameters_dock_widget(self)  # ← наш виджет
        }

    def properties_dock_widget(self):
        dock = QDockWidget('Свойства')
        dock.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        widget = QWidget()
        main_layout = QVBoxLayout()

        # Создаем группу "Свойства отображения"
        display_group = QGroupBox("Свойства отображения")
        display_layout = QFormLayout()

        # Выпадающий список для цветовой палитры
        self.color_palette_combo = QComboBox()
        self.color_palette_combo.addItems([
            "Blue > Green > Yellow > Red",
            "Grey",
            "Viridis",
            "Brown > Yellow",
            "Yellow > Brown",
            "Topo landserf",
            "High contrast",
            "Cividis",
            "Blue > White > Red",
            "Red > Yellow"
        ])
        display_layout.addRow("Цветовая палитра:", self.color_palette_combo)

        # Выпадающий список для поля цвета
        self.color_field_combo = QComboBox()
        self.color_field_combo.addItems([
            "intensity",
            "rgb",
            "z",
            "normals",
            "original_cloud_index",
            "gps_time",
            "illuminance"
        ])
        display_layout.addRow("Поле цвета:", self.color_field_combo)

        display_group.setLayout(display_layout)
        main_layout.addWidget(display_group)

        # Создаем группу "Свойства файла"
        file_group = QGroupBox("Свойства файла")
        file_layout = QFormLayout()
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)

        # Сохраняем ссылки на layouts для обновления
        self.properties_layout = main_layout
        self.file_properties_layout = file_layout

        widget.setLayout(main_layout)
        dock.setWidget(widget)
        return dock

    def files_dock_widget(self):
        dock = QDockWidget('Файлы')
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        widget = QWidget()
        layout = QVBoxLayout()  # Используем вертикальную компоновку

        # Создаем горизонтальную компоновку для кнопок
        buttons_layout = QHBoxLayout()

        # Добавляем кнопку "Выбрать всё"
        self.select_all_button = QPushButton("Выбрать всё")
        self.select_all_button.setShortcut("Ctrl+A")
        self.select_all_button.setToolTip("Ctrl+A")
        buttons_layout.addWidget(self.select_all_button)

        # Добавляем кнопку "Show/Hide"
        self.display_button = QPushButton("Show/Hide")
        self.display_button.setShortcut("Ctrl+R")
        self.display_button.setToolTip("Показать/скрыть выбранные объекты (Ctrl+R)")
        buttons_layout.addWidget(self.display_button)

        # Добавляем кнопку "Удалить"
        self.remove_button = QPushButton("Удалить")
        self.remove_button.setShortcut("Ctrl+D")
        self.remove_button.setToolTip("Ctrl+D")
        buttons_layout.addWidget(self.remove_button)

        # Добавляем горизонтальную компоновку кнопок в вертикальную компоновку
        layout.addLayout(buttons_layout)

        # Создаем QStackedWidget для переключения между пустым состоянием и списком файлов
        self.files_stack = QStackedWidget()

        # Виджет пустого состояния
        self.empty_state_widget = EmptyStateWidget(main_window=self)
        self.files_stack.addWidget(self.empty_state_widget)

        # QListWidget с поддержкой drag and drop
        self.listWidget = DragDropListWidget(main_window=self)
        self.listWidget.setToolTip(
            "Перетащите файлы сюда или используйте кнопку 'Выбрать файлы'\nПоддерживаемые форматы: .las, .pcd, .laz, .h5, .txt")
        self.files_stack.addWidget(self.listWidget)

        # По умолчанию показываем пустое состояние
        self.files_stack.setCurrentWidget(self.empty_state_widget)

        layout.addWidget(self.files_stack)

        widget.setLayout(layout)
        dock.setWidget(widget)
        return dock

    def update_empty_list_message(self):
        """Показывает виджет пустого состояния, если нет файлов"""
        if self.listWidget.count() == 0:
            self.files_stack.setCurrentWidget(self.empty_state_widget)

    def clear_empty_list_message(self):
        """Переключается на список файлов, если есть файлы"""
        if self.listWidget.count() > 0:
            self.files_stack.setCurrentWidget(self.listWidget)

    def add_file_to_list_widget(self, file_path):
        # Добавляем облако точек земли в list_widget
        ground_item = QListWidgetItem(self.listWidget)
        ground_checkbox = QCheckBox(os.path.basename(file_path))
        ground_checkbox.setChecked(True)
        ground_checkbox.setProperty("filePath", file_path)
        self.listWidget.setItemWidget(ground_item, ground_checkbox)
        ground_item.setSizeHint(ground_checkbox.sizeHint())
        ground_checkbox.stateChanged.connect(self.checkbox_changed)
