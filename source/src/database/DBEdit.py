from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
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

class Editor(QDialog):
    def __init__(self, parent, db_file):
        super().__init__(parent)
        self.setWindowTitle("DB Editor")
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
        
        self.create_toolbar()
        self.create_table_frame()
        self.populate_table()

    def create_toolbar(self):
        toolbar = QToolBar("Toolbar", self)
        toolbar.setStyleSheet("background-color: #171717;")
        add_row_action = QAction(QIcon(ASSETS_PATH+"add_row.png"), "Добавить строку\nShift + A", self)
        add_row_action.triggered.connect(self.add_row)
        toolbar.addAction(add_row_action)

        add_column_action = QAction(QIcon(ASSETS_PATH+"add_column.png"), "Добавить столбец\nCtrl + Shift + A", self)
        add_column_action.triggered.connect(self.add_column)
        toolbar.addAction(add_column_action)
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        remove_row_action = QAction(QIcon(ASSETS_PATH+"remove_row.png"), "Удалить строку\nCtrl + D", self)
        remove_row_action.setShortcut("Ctrl + D")
        remove_row_action.triggered.connect(self.remove_row)
        toolbar.addAction(remove_row_action)

        remove_column_action = QAction(QIcon(ASSETS_PATH+"remove_column.png"), "Удалить столбец\nCtrl + Shift + D", self)
        remove_row_action.setShortcut("Ctrl + Shift + D")
        remove_column_action.triggered.connect(self.remove_column)
        toolbar.addAction(remove_column_action)

        layout = QVBoxLayout(self)
        layout.addWidget(toolbar)

    def add_column(self):
        new_column_name, ok = QInputDialog.getText(self, "Добавить столбец", "Введите название нового столбца:")
        if ok and new_column_name:
            if new_column_name in self.table.columns:
                QMessageBox.warning(self, "Столбец уже существует", "Столбец с таким именем уже существует.")
                return

            self.table.columns.append(new_column_name) 
            self.db.tables[self.table_name] = self.table  
            if not self.db.save_to_file(self.db_file):  
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить изменения.")
                return

            self.animate_add_column()
            self.populate_table() 

    def animate_add_column(self):
        column_index = len(self.table.columns) 

        self.table_widget.setColumnWidth(column_index - 1, 0)

        self.column_width_animation_timer = QTimer(self)
        self.column_width_animation_timer.timeout.connect(self.update_column_width)
        self.column_width_animation_timer.start(10)  
        
        self.current_width = 0
        self.final_width = 100 
        self.step = 2  

    def update_column_width(self):
        self.current_width += self.step

        if self.current_width >= self.final_width:
            self.current_width = self.final_width
            self.column_width_animation_timer.stop()  

        self.table_widget.setColumnWidth(len(self.table.columns) - 1, self.current_width)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_A and event.modifiers() == Qt.ShiftModifier:
            self.add_row()
        elif event.key() == Qt.Key_A and event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            self.add_column()
        elif event.key() == Qt.Key_Delete:
            self.remove_row()

    def remove_row(self):
        row = self.table_widget.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите строку для удаления.")
            return

        reply = QMessageBox.question(self, "Подтверждение", "Вы действительно хотите удалить эту строку?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.animate_remove_row(row)

    def animate_remove_row(self, row_index):
        self.row_height_animation_timer = QTimer(self)
        self.row_height_animation_timer.timeout.connect(lambda: self.update_row_height_remove(row_index))
        self.row_height_animation_timer.start(10)

        self.current_row_height = self.table_widget.rowHeight(row_index)
        self.row_animation_step = -2

    def update_row_height_remove(self, row_index):
        self.current_row_height += self.row_animation_step

        if self.current_row_height <= 0:
            self.current_row_height = 0
            self.row_height_animation_timer.stop()
            row_id = int(self.table_widget.item(row_index, 0).text())
            if self.db.delete_record(self.table_name, row_id):
                for i, record in enumerate(self.table.records):
                    record.add("id", str(i + 1))
                self.table_widget.removeRow(row_index)
                self.db.tables[self.table_name] = self.table
                if not self.db.save_to_file(self.db_file):
                    QMessageBox.critical(self, "Ошибка", "Не удалось сохранить изменения.")

            else:
                 QMessageBox.critical(self, "Ошибка", "Не удалось удалить строку.")
            return
           
        self.table_widget.setRowHeight(row_index, self.current_row_height)

    def remove_column(self):
        column = self.table_widget.currentColumn()
        if column < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите столбец для удаления.")
            return
        if column == 0:
            QMessageBox.warning(self, "Ошибка", "Столбец 'id' нельзя удалить.")
            return

        reply = QMessageBox.question(self, "Подтверждение", "Вы действительно хотите удалить этот столбец?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.animate_remove_column(column)

    def animate_remove_column(self, column_index):
        self.column_width_animation_timer = QTimer(self)
        self.column_width_animation_timer.timeout.connect(lambda: self.update_column_width_remove(column_index))
        self.column_width_animation_timer.start(10)

        self.current_width = self.table_widget.columnWidth(column_index)
        self.step = -2

    def update_column_width_remove(self, column_index):
        self.current_width += self.step

        if self.current_width <= 0:
            self.current_width = 0
            self.column_width_animation_timer.stop()

            column_name = self.table.columns[column_index - 1]
            for record in self.table.records:
                if column_name in record.fields:
                    del record.fields[column_name]
            self.table.columns.pop(column_index - 1)
            self.db.tables[self.table_name] = self.table
            if not self.db.save_to_file(self.db_file):
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить изменения.")
                return

            self.table_widget.removeColumn(column_index) # удаление столбца после анимации
            self.populate_table()
            return

        self.table_widget.setColumnWidth(column_index, self.current_width)

    def create_table_frame(self):
        self.table_widget = QTableWidget()
        self.table_widget.setFocusPolicy(Qt.StrongFocus)
        self.table_widget.setStyleSheet("""
                                        background-color: #171717;  /* Цвет фона */
                                        gridline-color: #d0d0d0;       /* Цвет линий сетки */
                                        color: white;                /* Цвет текста */
                                        QScrollBar::handle:vertical 
                                        {
                                            background: #aaaaaa; /* Цвет ползунка */
                                            min-height: 20px;
                                            border-radius: 5px;
                                        }
                                    """)

        self.table_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  
        self.layout().addWidget(self.table_widget)

        self.table_widget.horizontalHeader().sectionDoubleClicked.connect(self.rename_column)
        self.table_widget.horizontalHeader().setStyleSheet("""
                                                            QHeaderView::section {
                                                                background-color: #080808;  /* Фон заголовка */
                                                                color: white;               /* Цвет текста заголовка */
                                                                border: 1px solid #d0d0d0;  /* Цвет линий, разделяющих заголовки */
                                                            }
                                                        """)

        self.table_widget.cellChanged.connect(self.check_for_date_placeholder)
        
        self.table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        context_menu = QMenu(self)

        duplicate_action = QAction("Заполнить строки", self)
        duplicate_action.triggered.connect(self.duplicate_row)
        context_menu.addAction(duplicate_action)

        context_menu.exec_(self.table_widget.viewport().mapToGlobal(pos))
        
    def duplicate_row(self):
        selected_ranges = self.table_widget.selectedRanges()  
        if not selected_ranges:
            QMessageBox.warning(self, "Предупреждение", "Выберите строки для заполнения.")
            return

        selected_column = self.table_widget.currentColumn()  
        if selected_column < 1: 
            QMessageBox.warning(self, "Предупреждение", "Выберите столбец для заполнения.")
            return

        first_selected_row = selected_ranges[0].topRow() 

        item = self.table_widget.item(first_selected_row, selected_column)
        value_to_fill = item.text() if item else ""

        for range_index in range(len(selected_ranges)):
            for row in range(selected_ranges[range_index].topRow(), selected_ranges[range_index].bottomRow() + 1):
                if row != first_selected_row:  
                    self.table_widget.item(row, selected_column).setText(value_to_fill)  

    def rename_column(self, column_index):
        if column_index == 0:
            QMessageBox.warning(self, "Ошибка", "Столбец 'id' нельзя переименовать.")
            return

        if column_index >= len(self.table.columns) + 1:  
            return
        
        old_column_name = self.table.columns[column_index - 1]  
        new_column_name, ok = QInputDialog.getText(self, "Переименовать столбец", 
                                                   f"Введите новое имя для столбца '{old_column_name}':")
        if ok and new_column_name and new_column_name != old_column_name:
            if new_column_name in self.table.columns:
                QMessageBox.warning(self, "Ошибка", "Столбец с таким именем уже существует.")
                return

            self.table.columns[column_index - 1] = new_column_name  
            self.db.tables[self.table_name] = self.table  

            if not self.db.save_to_file(self.db_file): 
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить изменения.")
                return

            self.populate_table() 

    def check_for_date_placeholder(self, row, column):
        item = self.table_widget.item(row, column)

        if item and item.text() == "$data":
            item.setText("")  
            
            date_edit = QDateEdit(self.table_widget)
            date_edit.setCalendarPopup(True)
            date_edit.setDate(QDate.currentDate())
            date_edit.dateChanged.connect(lambda date: self.update_item_with_date(row, column, date))

            if self.table_widget.cellWidget(row, column) is not None:
                self.table_widget.removeCellWidget(row, column)

            self.table_widget.setCellWidget(row, column, date_edit)
            date_edit.setFocus()

            date_edit.editingFinished.connect(lambda: self.handle_date_edit_finished(row, column))

    def handle_date_edit_finished(self, row, column):
        date_edit = self.table_widget.cellWidget(row, column)
        if date_edit is not None:
            date = date_edit.date()
            self.update_item_with_date(row, column, date)

            self.table_widget.removeCellWidget(row, column)
            
    def update_item_with_date(self, row, column, date):
        if date.isValid():
            item = QTableWidgetItem(date.toString("dd-MM-yyyy"))
            item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, column, item)
        else:
            self.table_widget.setItem(row, column, QTableWidgetItem(""))
 
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
        
    def save_changes(self):
        updated_columns = []
        for j in range(1, len(self.table.columns) + 1): 
            new_col_name = self.table_widget.horizontalHeaderItem(j).text()
            updated_columns.append(new_col_name)

        self.table.columns = updated_columns

        for i, record in enumerate(self.table.records):
            updates = {}
            for j, col in enumerate(self.table.columns):
                value = self.table_widget.item(i, j + 1).text() if self.table_widget.item(i, j + 1) else ""
                updates[col] = value

            try:
                self.db.update(self.table_name, int(record.get_field('id')), updates)
            except (ValueError, RuntimeError) as e:
                QMessageBox.critical(self, "Ошибка", str(e))
                return

        self.db.tables[self.table_name] = self.table
        if not self.db.save_to_file(self.db_file):
            QMessageBox.critical(self, "Ошибка", "Не удалось сохранить изменения в файл.")

    def add_row(self):
        self.save_changes()
        new_record_data = {col: "" for col in self.table.columns}
        self.db.insert(self.table_name, new_record_data)

        self.animate_add_row() 

    def animate_add_row(self):
        row_count = self.table_widget.rowCount()
        self.table_widget.insertRow(row_count)  

        for j in range(self.table_widget.columnCount()):
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row_count, j, item)

        self.table_widget.setRowHeight(row_count, 0)  

        self.row_height_animation_timer = QTimer(self)
        self.row_height_animation_timer.timeout.connect(self.update_row_height)
        self.row_height_animation_timer.start(20) 

        self.current_row_height = 0
        self.final_row_height = self.table_widget.rowHeight(0) if row_count > 0 else 25
        self.row_animation_step = 1  

    def update_row_height(self):
        self.current_row_height += self.row_animation_step
        
        if self.current_row_height >= self.final_row_height:
            self.current_row_height = self.final_row_height
            self.row_height_animation_timer.stop()
            self.populate_table()  
            return

        self.table_widget.setRowHeight(self.table_widget.rowCount() - 1, self.current_row_height)

