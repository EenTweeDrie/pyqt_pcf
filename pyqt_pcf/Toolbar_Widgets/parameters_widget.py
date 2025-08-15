

# Toolbar_Widgets/parameters_widget.py
import os
import pandas as pd
import yaml
from pc_forestry.pcd.TREE import TREE
from .base_widget import create_dock_widget


def parameters_dock_widget(self):
    """Возвращает (и кэширует) QDockWidget для расчета параметров."""
    default_params = {
        # 'intensity_cut': 3000,
        # 'height_threshold': 1.5
    }
    return create_dock_widget(
        self,
        name='parameters',
        title="Расчет параметров",
        button_text="Рассчитать параметры (Enter)",
        process_func=process,
        output_filename="parameters.xlsx",
        default_params=default_params
    )


def process(file_path: str, params: dict):
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
        pc.find_trunk_cluster()
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
