
# Toolbar_Widgets/multidiameter_widget.py
import os
import numpy as np
import pandas as pd
import yaml
from pc_forestry.pcd.TREE import TREE
from .base_widget import create_dock_widget


def multidiameter_dock_widget(self):
    """Возвращает (и кэширует) QDockWidget для расчета диаметров многоствольных деревьев."""

    # Загружаем только активные параметры из YAML файла
    config_path = os.path.join(os.path.dirname(__file__), 'multidiameter_config.yaml')
    default_params = {}

    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as file:
                loaded_params = yaml.safe_load(file)
                if loaded_params:
                    default_params = loaded_params
    except Exception as e:
        print(f"Ошибка при загрузке конфигурации многоствольных диаметров: {e}")
        default_params = {}
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
    device = params.get('device', 'cpu')
    pc.device = device
    print(f"Device: {device}")
    try:
        model_path = os.path.join(os.path.dirname(__file__),
                                  '..', 'pc_forestry', 'predict', 'checkpoints', f'catboost_model_{device}.pkl')
        pc.find_trunk_ml(model_path=model_path,
                         config=params.get('find_trunk_ml', {})
                         )
    except Exception as e:
        model_path = os.path.join(os.path.dirname(__file__),
                                  '..', '..', '..', 'pc_forestry', 'predict', 'checkpoints', f'catboost_model_{device}.pkl')
        pc.find_trunk_ml(model_path=model_path,
                         config=params.get('find_trunk_ml', {})
                         )
    pc.estimate_multi_trunk_diameters()

    if pc.multi_trunk_diameters_df is None or pc.multi_trunk_diameters_df.empty:
        # Если стволы не найдены, создаем одну строку с пустыми значениями
        result_data = {
            'number_of_trunks': 1,  # По умолчанию 1, если стволы не найдены
            'multi_diameters': np.nan,
            'min_diameter': np.nan,
            'max_diameter': np.nan,
            'multi_coordinates': np.nan
        }
        result_df = pd.DataFrame([result_data])
    else:
        # Если стволы найдены, агрегируем информацию в одну строку (один объект = одна строка)
        df = pc.multi_trunk_diameters_df.copy()

        # Применяем сдвиг координат, если он есть
        if hasattr(pc, 'shift') and pc.shift is not None:
            df['xc'] += pc.shift[0]
            df['yc'] += pc.shift[1]

        num_trunks = len(df)

        # Сортируем по диаметру для форматирования вывода
        df_sorted = df.sort_values(by='diameter_cm', ascending=False)

        # Находим минимальный и максимальный диаметры
        min_diameter = df_sorted['diameter_cm'].min()
        max_diameter = df_sorted['diameter_cm'].max()

        # Все диаметры, отсортированные по убыванию, в виде строки
        all_diameters_str = f"{{{'; '.join(f'{d:.1f}' for d in df_sorted['diameter_cm'])}}}".replace('.', ',')

        # Все координаты, отсортированные по диаметру, в виде строки
        coords_list = [f"({f'{row.xc:.2f}'.replace('.', ',')}; {f'{row.yc:.2f}'.replace('.', ',')})" for _, row in df_sorted.iterrows()]
        all_coords_str = f"{{{', '.join(coords_list)}}}"

        result_data = {
            'number_of_trunks': num_trunks,
            'multi_diameters': all_diameters_str,
            'min_diameter': min_diameter,
            'max_diameter': max_diameter,
            'multi_coordinates': all_coords_str
        }
        result_df = pd.DataFrame([result_data])

    # Добавляем имя файла
    result_df['filename'] = pc.name + os.path.splitext(file_path)[1]

    # Переупорядочиваем столбцы в соответствии с запросом
    result_df = result_df[['filename', 'number_of_trunks', 'min_diameter_cm', 'max_diameter_cm', 'diameters_cm', 'multicoordinates']]

    return result_df
