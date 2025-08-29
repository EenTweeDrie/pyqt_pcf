# Toolbar_Widgets/base_widget.py
from PyQt6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QApplication, QTextEdit
from PyQt6.QtCore import Qt
import os
import pandas as pd
from tqdm import tqdm
import yaml


def create_dock_widget(self, name, title, button_text, process_func, output_filename, default_params=None):
    """
    Фабрика для создания док-виджетов обработки файлов.
    """
    if name in self.dock_widgets:
        return self.dock_widgets[name]

    dock = QDockWidget(title)
    dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

    widget = QWidget()
    main_layout = QVBoxLayout()

    btn = QPushButton(button_text)
    btn.setDefault(True)

    main_layout.addWidget(btn)

    yaml_editor = None
    if default_params is not None:
        content_layout = QHBoxLayout()

        # Left panel: file list
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        list_label = QLabel("Выбранные файлы для обработки:")
        left_layout.addWidget(list_label)
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        left_layout.addWidget(list_widget)
        content_layout.addWidget(left_panel)
        widget.list_widget = list_widget

        # Right panel: YAML editor
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        yaml_label = QLabel("Конфигурация обработки (YAML):")
        right_layout.addWidget(yaml_label)
        yaml_editor = QTextEdit()

        # Отображаем только активные параметры без комментариев
        default_yaml = yaml.dump(default_params, sort_keys=False, default_flow_style=False)
        yaml_editor.setPlainText(default_yaml)

        right_layout.addWidget(yaml_editor)
        content_layout.addWidget(right_panel)
        widget.yaml_editor = yaml_editor

        main_layout.addLayout(content_layout)

    status_label = QLabel("Обработка...")
    status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    status_label.hide()
    main_layout.addWidget(status_label)

    widget.setLayout(main_layout)
    dock.setWidget(widget)

    # Save controls for later access
    widget.calculate_btn = btn
    widget.status_label = status_label

    def on_button_click():
        clicked_button_handler(self, dock, process_func, output_filename, with_params=(default_params is not None))

    btn.clicked.connect(on_button_click)

    if default_params is not None:
        def update_list(visible):
            if visible:
                widget.list_widget.clear()
                for index in range(self.listWidget.count()):
                    item = self.listWidget.item(index)
                    checkbox = self.listWidget.itemWidget(item)
                    if checkbox.isChecked():
                        file_path = checkbox.property("filePath")
                        widget.list_widget.addItem(os.path.basename(file_path))

        dock.visibilityChanged.connect(update_list)

    self.dock_widgets[name] = dock
    return dock


def clicked_button_handler(self, dock, process_func, output_filename, with_params):
    selected_files = []
    for index in range(self.listWidget.count()):
        item = self.listWidget.item(index)
        checkbox = self.listWidget.itemWidget(item)
        if checkbox.isChecked():
            selected_files.append(checkbox.property("filePath"))
    if not selected_files:
        print("Ошибка: Не выбрано файлов")
        return

    widget = dock.widget()

    params = {}
    if with_params:
        try:
            params_text = widget.yaml_editor.toPlainText()
            params = yaml.safe_load(params_text)
            if params is None:
                params = {}
        except yaml.YAMLError as e:
            print(f"Ошибка парсинга YAML: {e}")
            return

    print(params)

    widget.calculate_btn.setEnabled(False)
    widget.status_label.show()
    QApplication.processEvents()

    try:
        # Определяем корневую директорию проекта, предполагая, что 'self' - это главное окно,
        # у которого есть свойство 'workspace_dir', установленное при инициализации.
        # Если это не так, вам нужно будет адаптировать этот код.
        workspace_dir = getattr(self, 'workspace_dir', os.path.dirname(os.path.abspath(__file__)))
        tmp_dir = os.path.join(workspace_dir, "tmp")
        os.makedirs(tmp_dir, exist_ok=True)

        df = pd.DataFrame()
        for file_path in tqdm(selected_files):
            df_current = process_func(file_path, params)

            if df_current is not None:
                df = pd.concat([df, df_current])

        if not df.empty:
            output_path = os.path.join(tmp_dir, output_filename)
            df.to_excel(output_path, index=False)
            self.add_file_to_list_widget(output_path)

        dock.hide()
    except Exception as e:
        print(f"Ошибка при обработке или сохранении файла: {e}")
        return
    finally:
        widget.calculate_btn.setEnabled(True)
        widget.status_label.hide()
