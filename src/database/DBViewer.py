from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QPixmap
from .pyufodb import Relative_DB
import os

ASSETS_PATH_PRIMARY = "src/asset/"
ASSETS_PATH_SECONDARY = "_internal/src/asset/"

def get_assets_path():
    """Возвращает существующий путь к ресурсам."""
    if os.path.exists(ASSETS_PATH_PRIMARY):
        return ASSETS_PATH_PRIMARY
    elif os.path.exists(ASSETS_PATH_SECONDARY):
        return ASSETS_PATH_SECONDARY
    else:
        raise FileNotFoundError("Папка с ресурсами не найдена ни по одному из путей.")

# Пример использования:
ASSETS_PATH = get_assets_path()

class DBViewer(QDialog):
    def __init__(self, parent, db_file):
        super().__init__(parent)
        self.setWindowTitle("DB Viewer")
        
        self.setMinimumSize(800, 600)
        
        self.db_file = db_file
        self.db = Relative_DB()

        if not self.db.load_from_file(self.db_file):
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить файл базы данных")
            self.reject() 
            return
        
        if not self.db.tables:
            QMessageBox.warning(self, "Предупреждение", "База данных пуста. Не найдено ни одной таблицы")
            self.reject()  
            return

        self.table_name = list(self.db.tables.keys())[0]
        self.table = self.db.tables[self.table_name]

        self.layout = QVBoxLayout(self)  
        self.create_toolbar()  
        self.create_table_frame()
        self.populate_table()

    def create_toolbar(self):
        toolbar = QToolBar("Toolbar", self)
        toolbar.setStyleSheet("background-color: #171717;")  
        
        fullscreen_action = QAction(QIcon(ASSETS_PATH+"fullscreen_icon.png"), "Полный экран\nCtrl+F", self)
        fullscreen_action.setShortcut("Ctrl+F")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        toolbar.addAction(fullscreen_action)

        export_action = QAction(QIcon(ASSETS_PATH+"export_icon.png"), "Экспорт\nCtrl+E", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_data)
        toolbar.addAction(export_action)

        screenshot_action = QAction(QIcon(ASSETS_PATH+"screenshot_icon.png"), "Скриншот\nShift+S", self)
        screenshot_action.setShortcut("Shift+S")
        screenshot_action.triggered.connect(self.take_screenshot)
        toolbar.addAction(screenshot_action)

        self.layout.addWidget(toolbar)  

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.setWindowState(self.windowState() & ~Qt.WindowFullScreen)
        else:
            self.setWindowState(self.windowState() | Qt.WindowFullScreen)

    def create_table_frame(self):
        self.table_widget = QTableWidget()
        self.table_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  
        self.table_widget.setStyleSheet("""
                                        background-color: #171717;  /* Цвет фона */
                                        gridline-color: #d0d0d0;   /* Цвет линий сетки */
                                        color: white;              /* Цвет текста */
                                        QScrollBar::handle:vertical 
                                        {
                                            background: #aaaaaa; /* Цвет ползунка */
                                            min-height: 20px;
                                            border-radius: 5px;
                                        }
                                    """)
        
        self.layout.addWidget(self.table_widget)  

        self.table_widget.horizontalHeader().setStyleSheet("""
                                                            QHeaderView::section {
                                                                background-color: #080808;  /* Фон заголовка */
                                                                color: white;               /* Цвет текста заголовка */
                                                                border: 1px solid #d0d0d0;  /* Цвет линий, разделяющих заголовки */
                                                            }
                                                        """)

    def populate_table(self):
        self.table_widget.setRowCount(len(self.table.records))  
        self.table_widget.setColumnCount(len(self.table.columns) + 1)  

        columns = ["id"] + self.table.columns
        self.table_widget.setHorizontalHeaderLabels(columns)

        for i, record in enumerate(self.table.records):
            for j, col in enumerate(columns):
                if col == "id":
                    item = QTableWidgetItem(str(i + 1)) 
                else:
                    item = QTableWidgetItem(record.get_field(col))

                item.setTextAlignment(Qt.AlignCenter)
                
                self.table_widget.setItem(i, j, item)

        self.table_widget.setColumnWidth(0, 50)  
        for j in range(len(columns)):
            self.table_widget.horizontalHeaderItem(j).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        self.table_widget.horizontalHeader().setStretchLastSection(True)

    def export_data(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Экспортировать базу данных", "", "UFO Files (*.ufo);;All Files (*)", options=options)
        
        if file_path:
            if not file_path.endswith('.ufo'):
                file_path += '.ufo'
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(','.join(["id"] + self.table.columns) + '\n')
                for i, record in enumerate(self.table.records):
                    row_data = [str(i + 1)] + [record.get_field(col) for col in self.table.columns]
                    file.write(','.join(row_data) + '\n')
            
            QMessageBox.information(self, "Успех", "База данных успешно экспортирована.")

    def take_screenshot(self):
        screenshot = self.table_widget.grab() 

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить скриншот базы данных", "", "PNG Files (*.png);;JPEG Files (*.jpg;*.jpeg);;All Files (*)", options=options)
        if file_path:
            screenshot.save(file_path) 
            QMessageBox.information(self, "Успех", "Скриншот успешно сохранен.")
