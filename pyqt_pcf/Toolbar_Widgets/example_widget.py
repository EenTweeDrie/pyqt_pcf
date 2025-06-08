# Toolbar_Widgets/example_widget.py
from PyQt6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget
from PyQt6.QtCore import Qt
import os
from pc_forestry.pcd.PCD import PCD
from pc_forestry.pcd.TREE import TREE
import pandas as pd
from tqdm import tqdm


def example_dock_widget(self):
    """Возвращает (и кэширует) QDockWidget с нашим GUI."""
    if 'example' not in self.dock_widgets:
        dock = QDockWidget("Пример")
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        widget = QWidget()
        layout = QVBoxLayout()

        btn = QPushButton("Рассчитать параметры")
        btn.clicked.connect(lambda: clicked_button(self))
        layout.addWidget(btn)

        widget.setLayout(layout)
        dock.setWidget(widget)
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

    # multiplier = int(self.multiplier_input.text())
    df = pd.DataFrame()
    for file_path in tqdm(selected_files):

        # Определяем абсолютный путь к текущему файлу
        script_path = os.path.abspath(__file__)
        # Определяем директорию, в которой находится этот файл
        script_dir = os.path.dirname(script_path)
        # Определяем родительскую директорию (папку, содержащую script_dir)
        parent_dir = os.path.dirname(script_dir)

        # Создаём путь к tmp внутри родительской директории
        tmp_dir = os.path.join(parent_dir, "tmp")
        os.makedirs(tmp_dir, exist_ok=True)

        df_current = process(file_path)
        if df_current is not None:
            df = pd.concat([df, df_current])

    for col in df.select_dtypes(include=['float64', 'float32', 'int64', 'int32']).columns:
        df[col] = df[col].apply(lambda x: str(x).replace('.', ','))
    df.to_csv(os.path.join(tmp_dir, "parameters.csv"),
              index=False, sep=';')

    self.add_file_to_list_widget(os.path.join(tmp_dir, "parameters.csv"))


def process(file_path: str):
    data = {
        'name': os.path.basename(file_path),
        'X': None, 'Y': None,
        'X_1.3': None, 'Y_1.3': None,
        'diameter_LS': None, 'diameter_HLS': None,
        'diameter_LS_cos': None, 'diameter_HLS_cos': None,
        'angle': None, 'height': None
    }
    try:
        pc = TREE.read(file_path)
        data['name'] = pc.name
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
        data['X_1.3'] = pc.custom_coordinate[0]
        data['Y_1.3'] = pc.custom_coordinate[1]

        if data['diameter_LS'] is not None and cos_angle is not None and cos_angle != 0:
            data['diameter_LS_cos'] = data['diameter_LS'] / cos_angle
        if data['diameter_HLS'] is not None and cos_angle is not None and cos_angle != 0:
            data['diameter_HLS_cos'] = data['diameter_HLS'] / cos_angle
    except Exception as e:
        print(f"Error in angle/cos calculation for {file_path}: {e}")

    return pd.DataFrame([data])
