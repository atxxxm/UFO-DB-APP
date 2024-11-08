import sys, shutil, os, json
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from .database.DBEdit import Editor
from .database.DBViewer import DBViewer 
from .database.pyufodb import Relative_DB 

CONFIG_FILE = "config.json"
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

class DBEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UFO DATABASE")
        self.resize(800, 600)
        self.setWindowIcon(QIcon(ASSETS_PATH+"icon.png"))
        self.setAcceptDrops(True)

        self.last_folder_path = self.load_last_folder()
        if not os.path.exists(self.last_folder_path):
            os.makedirs(self.last_folder_path) 

        self.opened_files = {}
        self.clipboard = QApplication.clipboard()
        self.copied_file_path = None
        self.initialize_ui()
        
        self.dock_animation = QPropertyAnimation(self.dock_widget, b"maximumWidth")
        self.dock_animation.setDuration(300)  
        self.dock_animation.setEasingCurve(QEasingCurve.InOutCubic)  
        
        self.debug_area_animation = QPropertyAnimation(self.debug_area, b"maximumHeight")
        self.debug_area_animation.setDuration(300)
        self.debug_area_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.debug_area_animation.setStartValue(0)
        self.debug_area_animation.setEndValue(130)

        if self.last_folder_path and os.path.exists(self.last_folder_path):
            self.populate_files(self.last_folder_path)

    def initialize_ui(self):
        self.setStyleSheet("QMainWindow { background-color: #171717; }")  

        self.toolbar = QToolBar("Поле с инструментами")
        self.toolbar.setStyleSheet("background-color: #0f0f0f;")  
        self.addToolBar(self.toolbar)

        toggle_dock_action = QAction(QIcon(ASSETS_PATH+"toggle_dock.png"), "Проводник\nCtrl+E", self)
        toggle_dock_action.setShortcut("Ctrl+E")
        toggle_dock_action.triggered.connect(self.toggle_dock)
        self.toolbar.addAction(toggle_dock_action)

        self.dock_widget = self.createDockWidget() 

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True) 
 
        self.tab_widget.tabCloseRequested.connect(self.close_tab) 
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.tab_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self.show_tab_context_menu)

        new_action = QAction(QIcon(ASSETS_PATH+"new_action.png"), "Новый файл\nCtrl+N", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.create_new_file) 
        open_action = QAction(QIcon(ASSETS_PATH+"open_action.png"), "Открыть папку\nCtrl+O", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.handle_open_folder)
        self.toolbar.addAction(new_action)
        self.toolbar.addAction(open_action)
        
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  
        search_layout.addWidget(spacer)  

        self.search_line_edit = QLineEdit()
        self.search_line_edit.setPlaceholderText("Поиск файлов...")
        self.search_line_edit.setFixedSize(200, 30)  
        self.search_line_edit.textChanged.connect(self.search_files)

        search_layout.addWidget(self.search_line_edit)

        search_layout.setContentsMargins(10, 0, 32, 0)  

        self.toolbar.addWidget(search_widget)

        self.database_toolbar = QToolBar("Инструменты базы данных")
        self.database_toolbar.setStyleSheet("background-color: #0f0f0f;")
        self.addToolBar(Qt.RightToolBarArea, self.database_toolbar)

        run_action = QAction(QIcon(ASSETS_PATH+"run_action.png"), "Запустить базу данных\nCtrl+R", self)
        run_action.setShortcut("Ctrl+R")
        run_action.triggered.connect(self.run_database)
        self.database_toolbar.addAction(run_action)

        save_action = QAction(QIcon(ASSETS_PATH+"save_action.png"), "Сохранить\nCtrl+S", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_data)
        self.database_toolbar.addAction(save_action)

        save_all_action = QAction(QIcon(ASSETS_PATH+"save_all_action.png"), "Сохранить всё\nCtrl+Shift+S", self)
        save_all_action.setShortcut("Ctrl+Shift+S")
        save_all_action.triggered.connect(self.save_all_data)
        self.database_toolbar.addAction(save_all_action)

        self.debug_area = QTextEdit()  
        self.debug_area.setVisible(False)  
        self.debug_area.setStyleSheet("background-color: #171717; color: white;")  

        self.splitter = QSplitter(Qt.Vertical)
        self.debug_area.setMaximumHeight(130)

        self.splitter.addWidget(self.tab_widget)
        self.splitter.addWidget(self.debug_area)
  
        self.toggle_debug_button = QPushButton("Показать/Скрыть отладочную панель")
        self.toggle_debug_button.clicked.connect(self.toggle_debug_area)  
        self.toggle_debug_button.setStyleSheet("background-color: #171717; color: white;")  

        main_layout = QVBoxLayout()

        main_layout.addWidget(self.splitter)  
        main_layout.addWidget(self.toggle_debug_button) 

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def log_action(self, message):
        self.debug_area.append(f"{message}")
   
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): 
            event.acceptProposedAction()  

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith(".ufo"):  
                file_name = os.path.basename(file_path)
                if not self.dock_content.findItems(file_name, Qt.MatchExactly):
                    item = QListWidgetItem(QIcon(ASSETS_PATH+"ufo_icon.png"), file_name)
                    self.dock_content.addItem(item)
                self.log_action(f"Файл '{file_name}' добавлен в проводник.")
      
    def createDockWidget(self):
        dock_widget = QDockWidget("Проводник", self)
        dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.dock_content = QListWidget()  
        self.dock_content.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.dock_content.setStyleSheet("background-color: #171717; color: white;") 
        dock_widget.setWidget(self.dock_content)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_widget)

        self.dock_content.itemDoubleClicked.connect(self.open_file_from_list)
        self.dock_content.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dock_content.customContextMenuRequested.connect(self.show_context_menu)
        return dock_widget

    def show_context_menu(self, pos):
        context_menu = QMenu(self)
        
        selected_items = self.dock_content.selectedItems()

        if selected_items:
            if len(selected_items) == 1:
                file_name = selected_items[0].text()

                delete_action = QAction("Удалить", self)
                delete_action.triggered.connect(lambda: self.delete_file(file_name))
                context_menu.addAction(delete_action)

                rename_action = QAction("Переименовать", self)
                rename_action.triggered.connect(lambda: self.rename_file(file_name))
                context_menu.addAction(rename_action)

                copy_action = QAction("Копировать", self)
                copy_action.triggered.connect(lambda: self.copy_file(file_name))
                context_menu.addAction(copy_action)
            
            else:
                delete_action = QAction("Удалить выделенные", self)
                delete_action.triggered.connect(lambda: self.delete_selected_files(selected_items))
                context_menu.addAction(delete_action)

                copy_action = QAction("Копировать выделенные", self)
                copy_action.triggered.connect(lambda: self.copy_selected_files(selected_items))
                context_menu.addAction(copy_action)

        else:
            new_file_action = QAction("Создать новый файл", self)
            new_file_action.triggered.connect(self.create_new_file)
            context_menu.addAction(new_file_action)

            refresh_action = QAction("Обновить", self)
            refresh_action.triggered.connect(lambda: self.populate_files(self.last_folder_path))
            context_menu.addAction(refresh_action)

            paste_action = QAction("Вставить", self)
            paste_action.triggered.connect(self.paste_file)
            context_menu.addAction(paste_action)

        context_menu.exec(self.dock_content.viewport().mapToGlobal(pos))

    def delete_file(self, file_name):
        file_path = os.path.join(self.last_folder_path, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            self.log_action(f"Файл '{file_name}' удален.")
            self.populate_files(self.last_folder_path)
        else:
            QMessageBox.warning(self, "Ошибка", "Файл не найден.")
            self.log_action(f"Попытка удаления файла '{file_name}', но файл не найден.")

    def delete_selected_files(self, selected_items):
        files_to_delete = [item.text() for item in selected_items]

        for file_name in files_to_delete:
            self.delete_file(file_name)

    def rename_file(self, file_name):
        new_name, ok = QInputDialog.getText(self, "Переименовать файл", "Введите новое имя файла:", text=file_name)
        if ok and new_name:
            if not new_name.strip() or any(char in new_name for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
                QMessageBox.warning(self, "Ошибка", "Некорректное имя файла.")
                self.log_action(f"Неудачная попытка переименования '{file_name}': некорректное имя.")
                return
            old_file_path = os.path.join(self.last_folder_path, file_name)
            new_file_path = os.path.join(self.last_folder_path, new_name)
            if os.path.exists(old_file_path):
                os.rename(old_file_path, new_file_path)
                self.log_action(f"Файл '{file_name}' переименован в '{new_name}'.")
                self.populate_files(self.last_folder_path)
            else:
                QMessageBox.warning(self, "Ошибка", "Файл не найден.")
                self.log_action(f"Попытка переименования '{file_name}', но файл не найден.")

    def copy_file(self, file_name):
        self.copied_file_path = os.path.join(self.last_folder_path, file_name)
        self.clipboard.setText(self.copied_file_path)
        self.log_action(f"Файл '{file_name}' скопирован в буфер обмена.")

    def copy_selected_files(self, selected_items):
        copied_files = []
        for item in selected_items:
            file_name = item.text()
            file_path = os.path.join(self.last_folder_path, file_name)
            if os.path.exists(file_path):
                copied_files.append(file_path)
        if copied_files:
            self.copied_file_path = copied_files 
            self.log_action(f"Выделенные файлы скопированы в буфер обмена.")
        else:
            self.copied_file_path = None  
            
    def paste_file(self):
        if self.copied_file_path:
            if isinstance(self.copied_file_path, list):
                for src in self.copied_file_path:
                    dest_file_name = os.path.basename(src)
                    dest_file_path = os.path.join(self.last_folder_path, dest_file_name)

                    if os.path.exists(dest_file_path):
                        base_name, ext = os.path.splitext(dest_file_name)
                        count = 1
                        new_dest_file_name = f"{base_name} копия{ext}"
                        new_dest_file_path = os.path.join(self.last_folder_path, new_dest_file_name)

                        while os.path.exists(new_dest_file_path):
                            new_dest_file_name = f"{base_name} копия ({count}){ext}"
                            new_dest_file_path = os.path.join(self.last_folder_path, new_dest_file_name)
                            count += 1
                        
                        dest_file_path = new_dest_file_path  
                        
                    shutil.copy2(src, dest_file_path)
                    self.log_action(f"Файл '{dest_file_name}' вставлен как '{os.path.basename(dest_file_path)}'.")

            else:
                dest_file_name = os.path.basename(self.copied_file_path)
                dest_file_path = os.path.join(self.last_folder_path, dest_file_name)

                if os.path.exists(dest_file_path):
                    base_name, ext = os.path.splitext(dest_file_name)
                    count = 1
                    new_dest_file_name = f"{base_name} копия{ext}"
                    new_dest_file_path = os.path.join(self.last_folder_path, new_dest_file_name)

                    while os.path.exists(new_dest_file_path):
                        new_dest_file_name = f"{base_name} копия ({count}){ext}"
                        new_dest_file_path = os.path.join(self.last_folder_path, new_dest_file_name)
                        count += 1

                    dest_file_path = new_dest_file_path  

                shutil.copy2(self.copied_file_path, dest_file_path)
                self.log_action(f"Файл '{dest_file_name}' вставлен как '{os.path.basename(dest_file_path)}'.")

            self.populate_files(self.last_folder_path)
        else:
            QMessageBox.warning(self, "Ошибка", "Нет файла для вставки.")

    def show_tab_context_menu(self, pos):
        context_menu = QMenu(self)
        close_all_action = QAction("Закрыть все вкладки", self)
        close_all_action.triggered.connect(self.close_all_tabs)
        context_menu.addAction(close_all_action)
        context_menu.exec(self.tab_widget.mapToGlobal(pos))

    def close_all_tabs(self):
        while self.tab_widget.count() > 0:
            self.close_tab(0)
        self.log_action("Все вкладки закрыты.")
            
    def search_files(self, text):
        self.dock_content.clear()
        self.log_action(f"Поиск файлов с текстом '{text}'")
        for file in os.listdir(self.last_folder_path):
            if file.endswith('.ufo') and text.lower() in file.lower():
                item = QListWidgetItem(QIcon(ASSETS_PATH+"ufo_icon.png"), file)
                self.dock_content.addItem(item)

    def toggle_dock(self):
        if self.dock_widget.isVisible():
            self.dock_animation.setStartValue(self.dock_widget.width())
            self.dock_animation.setEndValue(0)

            self.dock_animation.finished.connect(self.dock_widget.hide)

            self.log_action("Проводник скрыт.")
        else:
            self.dock_widget.show()
            self.dock_animation.setStartValue(0)
            self.dock_animation.setEndValue(250)
            self.dock_animation.finished.disconnect(self.dock_widget.hide)  

            self.log_action("Проводник показан.")
        
        self.dock_animation.start()
        
    def toggle_debug_area(self):
        if self.debug_area.isVisible():
            self.debug_area_animation.setStartValue(self.debug_area.height())
            self.debug_area_animation.setEndValue(0)
            self.debug_area_animation.finished.connect(self.debug_area.hide)
        else:
            self.debug_area.show() 
            self.debug_area_animation.setStartValue(0)
            self.debug_area_animation.setEndValue(130)  
            self.debug_area_animation.finished.disconnect()

        self.debug_area_animation.start()

    def on_tab_changed(self, index):
        if index == -1: 
            return

        tab_name = self.tab_widget.tabText(index)
        self.log_action(f"Активная вкладка изменена на: {tab_name}")

        current_widget = self.tab_widget.widget(index)
        animation = QPropertyAnimation(current_widget, b"windowOpacity")
        animation.setDuration(300) 
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.start()


        self.tab_widget.setStyleSheet(
            f"""
            QTabBar::tab:selected {{
                background-color: #0f0f0f; 
            }}
            """
        )

        QTimer.singleShot(150, lambda: self.tab_widget.setStyleSheet(""))

    def handle_open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder_path:
            self.save_last_folder(folder_path)
            self.populate_files(folder_path)

    def populate_files(self, folder_path):
        ufo_files = [f for f in os.listdir(folder_path) if f.endswith('.ufo')]
        self.dock_content.clear()
        if ufo_files:
            for file in ufo_files:
                item = QListWidgetItem(QIcon(ASSETS_PATH+"ufo_icon.png"), file)  
                self.dock_content.addItem(item)
        else:
            self.dock_content.addItem("В выбранной папке нет файлов с расширением .ufo.")

    def open_file_from_list(self, item):
        file_name = item.text()
        if file_name not in self.opened_files:
            file_path = os.path.join(self.last_folder_path, file_name)
            editor = Editor(self, file_path) 
            editor.setStyleSheet("QWidget { background-color: #0f0f0f; solid #171717; }") 
            tab_index = self.tab_widget.addTab(editor, file_name)  
            self.tab_widget.setCurrentIndex(tab_index) 
            self.opened_files[file_name] = editor  
            self.log_action(f"Файл '{file_name}' открыт в новой вкладке.")

    def close_tab(self, index):
        if index >= 0:
            tab_text = self.tab_widget.tabText(index)  
            self.tab_widget.removeTab(index)  
            if tab_text in self.opened_files:
                editor = self.opened_files[tab_text]
                editor.deleteLater() 
                del self.opened_files[tab_text]  

    def run_database(self):
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            tab_text = self.tab_widget.tabText(current_index)
            editor = self.opened_files[tab_text]

            editor.save_changes()
            self.log_action(f"Изменения в файле '{tab_text}' сохранены.")
            self.log_action(f"Запуск базы данных {tab_text}")

            db_viewer = DBViewer(self, editor.db_file)  
            db_viewer.exec() 
        else:
            QMessageBox.warning(self, "Ошибка", "Нет открытых файлов для запуска базы данных.")

    def save_data(self):
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            tab_text = self.tab_widget.tabText(current_index)
            editor = self.opened_files[tab_text]
            editor.save_changes()
            self.log_action(f"Изменения в файле '{tab_text}' сохранены.")

    def save_all_data(self):
        for editor in self.opened_files.values():
            editor.save_changes()
        self.log_action("Все открытые файлы сохранены.")

    def load_last_folder(self):
        try:
            with open("config.json", "r") as f:  # Замените "config.json" на имя вашего файла
                config = json.load(f)
                last_folder = config.get("last_folder") # Используйте .get() для безопасного доступа

                if last_folder: # Проверяем, что путь не пустой и не None
                    #  Лучше использовать os.path.join для объединения путей
                    normalized_path = os.path.normpath(last_folder)

                    return normalized_path # Возвращаем ТОЛЬКО если путь существует
                else:
                    return "_internal/base" #  Путь по умолчанию, если "last_folder" не найден или пустой
        except FileNotFoundError:
            print("Файл конфигурации не найден. Используется путь по умолчанию.")
            return "_internal/base"
        except json.JSONDecodeError:
            print("Ошибка чтения JSON. Используется путь по умолчанию.")
            return "_internal/base"

    def save_last_folder(self, folder_path):
        config = {"last_folder": folder_path}
        with open(CONFIG_FILE, 'w') as config_file:
            json.dump(config, config_file)

    def create_new_file(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Создание нового файла")
        dialog.setFixedSize(400, 300)
        
        dialog.setStyleSheet("""
            QDialog {
                background-color: #171717;
                color: white;
                border-radius: 10px;
            }
            QLineEdit, QSpinBox {
                background-color: #444;
                color: white;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QLabel {
                font-size: 16px;
                color: white;
                margin-bottom: 10px;
            }
            QPushButton {
                background-color: #2a2d86;
                color: white;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3538a1;
            }
            QPushButton:pressed {
                background-color: #3f43bc;
            }
            QHBoxLayout {
                spacing: 20px;
                margin-top: 20px;
            }
        """)

        layout = QVBoxLayout(dialog)
        
        name_label = QLabel("Введите имя файла (без расширения):", dialog)
        name_input = QLineEdit(dialog)
        layout.addWidget(name_label)
        layout.addWidget(name_input)
        
        row_count_label = QLabel("Количество строк (1-20):", dialog)
        row_count_input = QSpinBox(dialog)
        row_count_input.setRange(1, 20)
        row_count_input.setButtonSymbols(QSpinBox.NoButtons) 
        layout.addWidget(row_count_label)
        layout.addWidget(row_count_input)

        column_count_label = QLabel("Количество столбцов (1-20):", dialog)
        column_count_input = QSpinBox(dialog)
        column_count_input.setRange(1, 20)
        column_count_input.setButtonSymbols(QSpinBox.NoButtons) 
        layout.addWidget(column_count_label)
        layout.addWidget(column_count_input)

        buttons_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Отмена", dialog)
        cancel_button.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_button)
        
        create_button = QPushButton("Создать", dialog)
        create_button.setShortcut("Enter")  
        create_button.clicked.connect(lambda: self.on_create_file(dialog, name_input, row_count_input, column_count_input))
        buttons_layout.addWidget(create_button)

        layout.addLayout(buttons_layout)

        row_count_input.wheelEvent = self.handle_wheel_event(row_count_input)
        column_count_input.wheelEvent = self.handle_wheel_event(column_count_input)

        def keyPressEvent(event):
            if event.key() == Qt.Key_Return: 
                self.on_create_file(dialog, name_input, row_count_input, column_count_input)
            else:
                QDialog.keyPressEvent(dialog, event) 
        
        dialog.keyPressEvent = keyPressEvent

        animation = QPropertyAnimation(dialog, b"windowOpacity")
        animation.setDuration(500)
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.start()

        dialog.exec()

    def handle_wheel_event(self, spinbox):
        def event(event):
            if event.angleDelta().y() > 0:
                spinbox.stepUp() 
            elif event.angleDelta().y() < 0:
                spinbox.stepDown()  
            event.accept()
        return event

    def on_create_file(self, dialog, name_input, row_count_input, column_count_input):
        file_name = name_input.text()
        if not file_name.strip():
            QMessageBox.warning(self, "Ошибка", "Имя файла не может быть пустым.")
            return

        row_count = row_count_input.value()
        column_count = column_count_input.value()
        
        if any(char in file_name for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            QMessageBox.warning(self, "Ошибка", "Некорректное имя файла.")
            return

        full_file_name = f"{file_name}.ufo"
        file_path = os.path.join(self.last_folder_path, full_file_name)
        
        column_names = self.generate_column_names(column_count)
        
        if not os.path.exists(self.last_folder_path):
            os.makedirs(self.last_folder_path)

        db = Relative_DB()
        db.create_table("sightings", column_names)

        for _ in range(row_count):
            empty_row = {col: "" for col in column_names}
            db.insert("sightings", empty_row)

        db.save_to_file(file_path)
        self.log_action(f"Создан новый файл '{full_file_name}' с {row_count} строками и {column_count} столбцами.")
        
        self.populate_files(self.last_folder_path)
        
        dialog.accept()

    def generate_column_names(self, count):
        """Генерация имен столбцов от 'a' до 'zzz'."""
        if count < 1 or count > 78:
            return []
        
        names = []
        for i in range(count):
            name = ""
            num = i
            while num >= 0:
                name = chr(num % 26 + ord('a')) + name
                num = num // 26 - 1 
            names.append(name)
        
        return names


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = DBEditor()
    dialog.showMaximized()
    sys.exit(app.exec())
