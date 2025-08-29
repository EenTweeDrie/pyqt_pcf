import os
import open3d as o3d
import pandas as pd
from OpenGL.GL import glDeleteBuffers
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon, QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QListWidgetItem, QCheckBox, QApplication, QLabel, QPushButton, QMessageBox
from config import base_path
from Toolbar_Widgets.design import Ui_MainWindow
from Toolbar_Widgets.console_manager import ConsoleManager
from menu_bar import MenuBar
from Toolbar.tool_bar import ToolBar
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem

from Toolbar_Widgets import parameters_widget
from Toolbar_Widgets import multidiameter_widget
from pc_forestry.pcd.PCD import PCD
from pc_forestry.pcd.TREE import TREE
import shutil


class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MyMainWindow, self).__init__()
        self.dock_widgets = {}
        self.current_dock = None

        self.setWindowIcon(QIcon(os.path.join(base_path, "images/Icon.png")))

        self.setupUi(self)

        # Создаем экземпляр для управления консолью
        self.consoleManager = ConsoleManager(self)
        # Создаем виджет док-панели для консоли
        self.console_dock_widget = self.consoleManager.create_console_dock_widget()
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, self.console_dock_widget)
        # Перенаправляем стандартный вывод в консоль
        self.consoleManager.redirect_console_output()

        # Создаем меню
        self.menuCreator = MenuBar(self)
        self.menuCreator.create_actions()
        self.menuCreator.create_menu_bar()

        # Создаем панель инструментов
        self.toolbarsCreator = ToolBar(self)
        self.toolbarsCreator.create_actions()
        self.toolbarsCreator._createToolBars()

        # Подключаем обработчики событий для элементов меню и панели инструментов
        self.menuCreator.openAction.triggered.connect(self.select_files)
        self.menuCreator.saveAction.triggered.connect(self.save_selected_tree)
        self.menuCreator.exitAction.triggered.connect(
            QApplication.instance().quit)
        self.menuCreator.aboutAction.triggered.connect(self.show_about_dialog)

        self.toolbarsCreator.parametersAction.triggered.connect(
            lambda: self.toggle_dock_widget('parameters', Qt.DockWidgetArea.LeftDockWidgetArea)
        )
        self.toolbarsCreator.multidiameterAction.triggered.connect(
            lambda: self.toggle_dock_widget('multidiameter', Qt.DockWidgetArea.LeftDockWidgetArea)
        )

        self.toolbarsCreator.frontViewAction.triggered.connect(lambda: self.openGLWidget.set_view_parameters(1, 1, 1))
        self.toolbarsCreator.backViewAction.triggered.connect(lambda: self.openGLWidget.set_view_parameters(1, 180, 1))
        self.toolbarsCreator.leftSideViewAction.triggered.connect(lambda: self.openGLWidget.set_view_parameters(1, 90, 1))
        self.toolbarsCreator.rightSideViewAction.triggered.connect(lambda: self.openGLWidget.set_view_parameters(1, 270, 1))
        self.toolbarsCreator.topViewAction.triggered.connect(lambda: self.openGLWidget.set_view_parameters(90, 1, 1))
        self.toolbarsCreator.bottomViewAction.triggered.connect(lambda: self.openGLWidget.set_view_parameters(270, 1, 1))
        self.toolbarsCreator.increaseSizeAction.triggered.connect(self.openGLWidget.increase_point_size)
        self.toolbarsCreator.decreaseSizeAction.triggered.connect(self.openGLWidget.decrease_point_size)
        self.toolbarsCreator.focusAction.triggered.connect(self.focus_on_selected_item)

        # Подключаем кнопку и обработчик
        self.select_all_button.clicked.connect(self.toggle_select_all)
        # Подключаем обработчик события нажатия кнопки "Удалить"
        self.remove_button.clicked.connect(self.remove_selected_items)

        self.selected_files = []

        # Инициализация атрибута для DockWidget "Свойства"
        self.properties_dock = None
        self.properties_widget = None

        # Включаем поддержку drag and drop
        self.setAcceptDrops(True)

    def show_about_dialog(self):
        QMessageBox.about(self, "О приложении", "LIDAR pcf segmentation v0.1.4")

    def select_files(self):
        # Метод для выбора файлов
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выбрать файлы", "", "PointCloud files (*.las *.pcd *.laz *.h5 *.txt)")
        if files:
            self.add_files_to_list(files)

    def toggle_select_all(self):
        # Метод для переключения всех чекбоксов
        all_checked = all(self.listWidget.itemWidget(self.listWidget.item(index)).isChecked()
                          for index in range(self.listWidget.count()))

        # Устанавливаем новое состояние для всех чекбоксов
        new_state = Qt.CheckState.Unchecked if all_checked else Qt.CheckState.Checked
        new_state_bool = new_state == Qt.CheckState.Checked

        # Проходим по всем элементам в списке и устанавливаем новое состояние
        for index in range(self.listWidget.count()):
            item = self.listWidget.item(index)
            checkbox = self.listWidget.itemWidget(item)
            if checkbox:
                checkbox.setChecked(new_state_bool)

    def remove_selected_items(self):
        # Метод для удаления выбранных элементов
        items = []
        selected_count = 0

        # Подсчитываем количество выбранных элементов
        for index in range(self.listWidget.count()):
            item = self.listWidget.item(index)
            items.append(item)
            checkbox = self.listWidget.itemWidget(item)
            if checkbox and checkbox.isChecked():
                selected_count += 1

        # Если нет выбранных элементов, выходим
        if selected_count == 0:
            return

        # Показываем диалог подтверждения
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            'Подтверждение удаления',
            f'Вы уверены, что хотите удалить {selected_count} выбранных элементов?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        # Если пользователь не подтвердил удаление, выходим
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Проходим в обратном порядке по всем элементам и удаляем выбранные
        for item in reversed(items):
            checkbox = self.listWidget.itemWidget(item)
            if checkbox and checkbox.isChecked():
                file_path = checkbox.property("filePath")

                # Удаляем элемент из QListWidget
                row = self.listWidget.row(item)
                self.listWidget.takeItem(row)
                # Удаляем точку из OpenGLWidget, если файл загружен
                if file_path and file_path in self.openGLWidget.point_clouds:
                    del self.openGLWidget.point_clouds[file_path]
                if file_path and file_path in self.openGLWidget.vbo_data:
                    # Получаем информацию о VBO, которую нужно удалить
                    vbo_info = self.openGLWidget.vbo_data[file_path]

                    # Вызываем функцию удаления VBO
                    self.delete_vbo(vbo_info)
                    print(f"Удалён файл: {file_path}")

                    # Удаляем запись из словаря
                    del self.openGLWidget.vbo_data[file_path]

        # Обновляем отображение в OpenGLWidget
        self.openGLWidget.update()

        # Если список стал пустым, показываем сообщение-подсказку
        self.update_empty_list_message()

    def focus_on_selected_item(self):
        # Сначала проверяем текущий выделенный элемент
        currentItem = self.listWidget.currentItem()
        if currentItem:
            checkbox = self.listWidget.itemWidget(currentItem)
            if checkbox and checkbox.isChecked():
                file_path = checkbox.property("filePath")
                if file_path:
                    self.openGLWidget.focus_on_object(file_path)
                    return

        # Если выделенный элемент не подходит, ищем единственный отмеченный
        checked_files = []
        for index in range(self.listWidget.count()):
            item = self.listWidget.item(index)
            checkbox = self.listWidget.itemWidget(item)
            if checkbox and checkbox.isChecked():
                checked_files.append(checkbox.property("filePath"))

        if len(checked_files) == 1:
            file_path = checked_files[0]
            self.openGLWidget.focus_on_object(file_path)
            return

        if len(checked_files) > 1:
            print("Отмечено несколько элементов. Выделите один для фокусировки.")
        else:  # len(checked_files) == 0
            print("Нет активных элементов для фокусировки.")

    def delete_vbo(self, vbo_info):
        # vbo_info предполагается быть кортежем (point_vbo, color_vbo, _)
        point_vbo, color_vbo, _ = vbo_info

        # Освобождение ресурсов VBO для точек
        if point_vbo is not None:
            glDeleteBuffers(1, [int(point_vbo)])

        # Освобождение ресурсов VBO для цветов
        if color_vbo is not None:
            glDeleteBuffers(1, [int(color_vbo)])

    def checkbox_changed(self, state):
        checkbox = self.sender()
        if checkbox:
            file_path = checkbox.property("filePath")
            if state == 2:  # Checkbox is checked
                self.openGLWidget.load_point_cloud(file_path)
                self.update_properties_dock(file_path)

            elif state == 0:  # Checkbox is unchecked
                if file_path in self.openGLWidget.point_clouds:
                    self.openGLWidget.point_clouds[file_path]['active'] = False
                    self.openGLWidget.update()
                    self.clear_properties_dock()
                elif file_path in self.openGLWidget.models:
                    self.openGLWidget.models[file_path]['active'] = False
                    self.openGLWidget.update()
                    self.clear_properties_dock()

    def update_properties_dock(self, file_path):
        if file_path in self.openGLWidget.point_clouds:
            if self.openGLWidget.point_clouds[file_path]['active']:
                num_points = self.openGLWidget.vbo_data[file_path][2]
                self.clear_properties_dock()
                file_label = QLabel(f"Файл: {os.path.basename(file_path)}")
                num_points_label = QLabel(f"Количество точек: {num_points}")
                self.properties_layout.addWidget(file_label)
                self.properties_layout.addWidget(num_points_label)
        if file_path in self.openGLWidget.models:
            if self.openGLWidget.models[file_path]['active']:
                triangles = self.openGLWidget.vbo_data_models[file_path][2] / 3

                self.clear_properties_dock()
                file_label = QLabel(f"Файл: {os.path.basename(file_path)}")
                num_points_label = QLabel(
                    f"Количество полигонов: {int(triangles)}")
                self.properties_layout.addWidget(file_label)
                self.properties_layout.addWidget(num_points_label)

    def clear_properties_dock(self):
        if self.properties_layout:
            for i in reversed(range(self.properties_layout.count())):
                widget = self.properties_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

    def toggle_dock_widget(self, dock_widget_name, dock_area):
        action = None
        if dock_widget_name == 'parameters':
            action = self.toolbarsCreator.parametersAction
        elif dock_widget_name == 'multidiameter':
            action = self.toolbarsCreator.multidiameterAction

        if dock_widget_name not in self.dock_widgets:
            if dock_widget_name in ['parameters', 'multidiameter']:
                if dock_widget_name == 'parameters':
                    new_dock = parameters_widget.parameters_dock_widget(self)
                elif dock_widget_name == 'multidiameter':
                    new_dock = multidiameter_widget.multidiameter_dock_widget(self)

                self.addDockWidget(dock_area, new_dock)
                new_dock.setFloating(True)
                self.dock_widgets[dock_widget_name] = new_dock
                new_dock.show()
                new_dock.raise_()
                new_dock.activateWindow()
                if action:
                    action.setChecked(True)

                # Привязываем обработчик закрытия
                new_dock.visibilityChanged.connect(lambda visible, a=action: a.setChecked(visible) if a else None)

        else:
            dock_widget = self.dock_widgets.get(dock_widget_name)
            if dock_widget.isVisible():
                dock_widget.hide()
                if action:
                    action.setChecked(False)
            else:
                dock_widget.show()
                dock_widget.raise_()
                dock_widget.activateWindow()
                if action:
                    action.setChecked(True)

    def save_single_file(self, file_path):
        print("from:", file_path)
        save_path, _ = QFileDialog.getSaveFileName(self, "Сохранить выбранный файл", "",
                                                   "Excel Files (*.xlsx);; PointCloud files (*.las *.pcd *.laz *.h5 *.txt)")
        print("to:", save_path)
        if save_path:
            if save_path.endswith('.xlsx'):
                shutil.copy(file_path, save_path)
                print(f"Файл: {file_path} сохранён как: {save_path}")
            else:
                pc = PCD.read(file_path)
                pc.save(save_path)
                print(f"Файл: {file_path} сохранён как: {save_path}")

    def save_multiple_files(self, file_paths):
        save_dir = QFileDialog.getExistingDirectory(
            self, "Выбрать папку для сохранения файлов")
        if save_dir:
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                output_path = os.path.join(save_dir, file_name)
                if file_path.endswith('.xlsx'):
                    shutil.copy(file_path, output_path)
                    print(f"Файл: {file_path} сохранён как: {output_path}")
                else:
                    pc = PCD.read(file_path)
                    pc.save(output_path)
                    print(f"Файл: {file_path} сохранён как: {output_path}")

    def save_selected_tree(self):
        selected_files = []
        for index in range(self.listWidget.count()):
            item = self.listWidget.item(index)
            checkbox = self.listWidget.itemWidget(item)
            if checkbox.isChecked():
                selected_files.append(checkbox.property("filePath"))

        if not selected_files:
            print("Нет выбранных файлов для сохранения")
            return

        if len(selected_files) == 1:
            self.save_single_file(selected_files[0])
        else:
            self.save_multiple_files(selected_files)

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
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            valid_files = []

            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    # Проверяем расширение файла
                    if file_path.lower().endswith(('.las', '.pcd', '.laz', '.h5', '.txt')):
                        valid_files.append(file_path)

            if valid_files:
                self.add_files_to_list(valid_files)
                event.acceptProposedAction()
                print(f"Перетащено файлов: {len(valid_files)}")
            else:
                print("Нет поддерживаемых файлов для загрузки")
                event.ignore()
        else:
            event.ignore()

    def add_files_to_list(self, files):
        """Добавляет файлы в список (используется как для drag&drop, так и для обычного выбора)"""
        for file in files:
            # Проверяем, не добавлен ли уже этот файл
            file_already_exists = False
            for index in range(self.listWidget.count()):
                item = self.listWidget.item(index)
                checkbox = self.listWidget.itemWidget(item)
                if checkbox and checkbox.property("filePath") == file:
                    file_already_exists = True
                    break

            if not file_already_exists:
                # Создание нового элемента QListWidgetItem
                item = QListWidgetItem(self.listWidget)

                # Создание чекбокса с именем файла
                checkbox = QCheckBox(os.path.basename(file))
                checkbox.setChecked(False)

                checkbox.setProperty("filePath", file)
                print(f"Загружен файл: {file}")

                # Добавляем чекбокс в элемент QListWidgetItem
                self.listWidget.setItemWidget(item, checkbox)
                # Устанавливаем размер элемента списка для чекбокса
                item.setSizeHint(checkbox.sizeHint())

                checkbox.stateChanged.connect(self.checkbox_changed)
            else:
                print(f"Файл уже добавлен: {os.path.basename(file)}")

        # Переключаемся на список файлов после добавления файлов
        self.clear_empty_list_message()

    def clear_empty_list_message(self):
        """Переключается на список файлов, если есть файлы"""
        if hasattr(self, 'files_stack') and self.listWidget.count() > 0:
            self.files_stack.setCurrentWidget(self.listWidget)

    def update_empty_list_message(self):
        """Показывает виджет пустого состояния, если нет файлов"""
        if hasattr(self, 'files_stack') and self.listWidget.count() == 0:
            self.files_stack.setCurrentWidget(self.empty_state_widget)
