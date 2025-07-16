import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QToolBar, QApplication
from PyQt6.QtGui import QIcon, QAction

from config import base_path


class ToolBar:
    def __init__(self, parent=None):
        self.parent = parent

    def _createToolBars(self):
        # Создание панели инструментов "Панель управленя взаимодействием"
        editToolBar = QToolBar(
            "Панель управления взаимодействием", self.parent)

        # Пример!!!
        editToolBar.addAction(self.exampleAction)  # ← добавили

        self.parent.addToolBar(editToolBar)

        # Использование объекта QToolBar и области панели инструментов
        interactionToolBar = QToolBar(
            "Панель управления вращения", self.parent)
        interactionToolBar.addAction(self.frontViewAction)
        interactionToolBar.addAction(self.backViewAction)
        interactionToolBar.addAction(self.leftSideViewAction)
        interactionToolBar.addAction(self.rightSideViewAction)
        interactionToolBar.addAction(self.topViewAction)
        interactionToolBar.addAction(self.bottomViewAction)
        interactionToolBar.addAction(self.focusAction)
        interactionToolBar.addAction(self.increaseSizeAction)
        interactionToolBar.addAction(self.decreaseSizeAction)
        self.parent.addToolBar(
            Qt.ToolBarArea.LeftToolBarArea, interactionToolBar)

    def create_actions(self):
        # Действия для панели инструментов "Панель управленя взаимодействием"
        self.exampleAction = QAction(
            QIcon(os.path.join(base_path, "images/example.png")),
            "Рассчет параметров (Ctrl+P)", self.parent
        )
        self.exampleAction.setShortcut("Ctrl+P")
        # Действия для панели инструментов "Панель управления вращения"
        self.increaseSizeAction = QAction(QIcon(os.path.join(base_path, "images/plus.png")), "Увеличить", self.parent)
        self.decreaseSizeAction = QAction(QIcon(os.path.join(base_path, "images/minus.png")), "Уменьшить", self.parent)
        self.focusAction = QAction(QIcon(os.path.join(base_path, "images/arrow.png")), "Фокус", self.parent)
        self.frontViewAction = QAction(QIcon(os.path.join(base_path, "images/FrontView.png")), "Вид спереди", self.parent)
        self.backViewAction = QAction(QIcon(os.path.join(base_path, "images/BackView.png")), "Вид сзади", self.parent)
        self.leftSideViewAction = QAction(QIcon(os.path.join(base_path, "images/SideViewLeft.png")), "Вид сбоку", self.parent)
        self.rightSideViewAction = QAction(QIcon(os.path.join(base_path, "images/SideViewRight.png")), "Вид сбоку", self.parent)
        self.topViewAction = QAction(QIcon(os.path.join(base_path, "images/TopView.png")), "Вид сверху", self.parent)
        self.bottomViewAction = QAction(QIcon(os.path.join(base_path, "images/BottomView.png")), "Вид снизу", self.parent)
