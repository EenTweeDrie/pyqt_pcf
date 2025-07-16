# Toolbar_Widgets/example_widget.py
from PyQt6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QApplication
from PyQt6.QtCore import Qt
import os
from pc_forestry.pcd.PCD import PCD
from pc_forestry.pcd.TREE import TREE
import pandas as pd
from tqdm import tqdm
from time import sleep


def example_dock_widget(self):
    """Возвращает (и кэширует) QDockWidget с нашим GUI."""
    if 'example' not in self.dock_widgets:
        dock = QDockWidget("Рассчет параметров")
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

        widget = QWidget()
        layout = QVBoxLayout()

        btn = QPushButton("Рассчитать параметры (Enter)")
        btn.setDefault(True)
        btn.clicked.connect(lambda: clicked_button(self))
        layout.addWidget(btn)

        status_label = QLabel("Обработка...")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.hide()
        layout.addWidget(status_label)

        widget.setLayout(layout)
        dock.setWidget(widget)

        # Сохраняем элементы управления для последующего доступа
        widget.calculate_btn = btn
        widget.status_label = status_label

        self.dock_widgets['example'] = dock

    return self.dock_widgets['example']


def clicked_button(self):
    selected_files = []
    for index in range(self.listWidget.count()):
        item = self.listWidget.item(index)
        checkbox = self.listWidget.itemWidget(item)
        if checkbox.isChecked():
            selected_files.append(checkbox.property("filePath"))
    if not selected_files:
        print("Ошибка: Не выбрано файлов")
        return

    dock = self.dock_widgets['example']
    widget = dock.widget()

    widget.calculate_btn.setEnabled(False)
    widget.status_label.show()
    QApplication.processEvents()

    try:
        # multiplier = int(self.multiplier_input.text())
        df = pd.DataFrame()
        for file_path in tqdm(selected_files):

            # Определяем абсолютный путь к текущему файлу
            script_path = os.path.abspath(__file__)
            # Определяем директорию, в которой находится этот файл (Toolbar_Widgets)
            script_dir = os.path.dirname(script_path)
            # Определяем родительскую директорию (pyqt_pcf)
            parent_dir = os.path.dirname(script_dir)
            # Определяем корневую директорию проекта
            project_root = os.path.dirname(parent_dir)

            # Создаём путь к tmp внутри корневой директории
            tmp_dir = os.path.join(project_root, "tmp")
            os.makedirs(tmp_dir, exist_ok=True)

            df_current = process(file_path)
            if df_current is not None:
                df = pd.concat([df, df_current])

        for col in df.select_dtypes(include=['float64', 'float32', 'int64', 'int32']).columns:
            df[col] = df[col].apply(lambda x: str(x).replace('.', ','))

        df.to_excel(os.path.join(tmp_dir, "parameters.xlsx"),
                    index=False)

        self.add_file_to_list_widget(os.path.join(tmp_dir, "parameters.xlsx"))
        self.dock_widgets['example'].hide()
    except Exception as e:
        print(f"Ошибка при обработке или сохранении файла: {e}")
        return
    finally:
        widget.calculate_btn.setEnabled(True)
        widget.status_label.hide()


def process(file_path: str):
    data = {
        'name': os.path.basename(file_path),
        'X': None, 'Y': None,
        'X_1_3': None, 'Y_1_3': None,
        'diameter_LS': None, 'diameter_HLS': None,
        'diameter_LS_cos': None, 'diameter_HLS_cos': None,
        'angle': None, 'height': None
    }
    try:
        pc = TREE.read(file_path)
        data['name'] = pc.name + os.path.splitext(file_path)[1]
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

    try:
        pc.estimate_coordinate()
        data['X'] = pc.coordinate[0]
        data['Y'] = pc.coordinate[1]
    except Exception as e:
        print(f"Error in estimate_coordinate for {file_path}: {e}")

    try:
        pc.find_trunk_cluster(intensity_cut=3000, height_threshold=1.5)
    except Exception as e:
        print(f"Error in find_trunk_cluster for {file_path}: {e}")

    try:
        pc.estimate_diameter()
        data['diameter_LS'] = pc.diameter_LS
        data['diameter_HLS'] = pc.diameter_HLS
    except Exception as e:
        print(f"Error in estimate_diameter for {file_path}: {e}")

    try:
        pc.estimate_height()
        data['height'] = pc.height
    except Exception as e:
        print(f"Error in estimate_height for {file_path}: {e}")

    try:
        angle = pc.get_angle()
        cos_angle = pc.get_cos_angle()
        data['angle'] = angle
        data['X_1_3'] = pc.custom_coordinate[0]
        data['Y_1_3'] = pc.custom_coordinate[1]

        if data['diameter_LS'] is not None and cos_angle is not None and cos_angle != 0:
            data['diameter_LS_cos'] = data['diameter_LS'] / cos_angle
        if data['diameter_HLS'] is not None and cos_angle is not None and cos_angle != 0:
            data['diameter_HLS_cos'] = data['diameter_HLS'] / cos_angle
    except Exception as e:
        print(f"Error in angle/cos calculation for {file_path}: {e}")

    return pd.DataFrame([data])
