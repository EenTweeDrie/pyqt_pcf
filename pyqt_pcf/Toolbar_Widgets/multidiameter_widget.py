
# Toolbar_Widgets/multidiameter_widget.py
import os
import numpy as np
import pandas as pd
from pc_forestry.pcd.TREE import TREE
from .base_widget import create_dock_widget


def multidiameter_dock_widget(self):
    """Возвращает (и кэширует) QDockWidget для расчета диаметров многоствольных деревьев."""
    default_params = {
        # 'intensity_cut': 3000,
        # 'height_threshold': 1.5
    }
    return create_dock_widget(
        self,
        name='multidiameter',
        title="Расчет диаметров многоствольных деревьев",
        button_text="Рассчитать диаметры (Enter)",
        process_func=process,
        output_filename="multidiameter.xlsx",
        default_params=default_params
    )


def process(file_path: str, params: dict):
    pc = TREE.read(file_path)
    pc.find_trunk_ml()
    pc.estimate_multi_trunk_diameters()
    if pc.multi_trunk_diameters_df is None:
        center = pd.DataFrame([{'xc': np.nan, 'yc': np.nan, 'diameter_cm': np.nan}])
    else:
        center = pc.multi_trunk_diameters_df[['xc', 'yc']].copy()
        if hasattr(pc, 'shift') and pc.shift is not None:
            center += pc.shift[:2]
        center['diameter_cm'] = pc.multi_trunk_diameters_df['diameter_cm']

    center['filename'] = pc.name + os.path.splitext(file_path)[1]
    return center
