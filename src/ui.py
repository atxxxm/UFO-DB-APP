from customtkinter import *
from tkinter import messagebox
import time,os
from .pyufodb import Relative_DB
from .otherFunc import githubLink, AuthorLink, NewsLink
from .dbEditor import DBEditor

import shutil
from tkinter import filedialog

class DatabaseApp(CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Database Interface")
        self.geometry("900x600")
        self.saves_dir = "src/saves"
        self.load_frame()

    def init_create_db_frame(self):
        # Поле для ввода названия базы данных
        CTkLabel(self.create_db_frame, text="Название базы данных:").pack(padx=5, pady=(5, 0))
        self.db_name_entry = CTkEntry(self.create_db_frame)
        self.db_name_entry.pack(padx=5, pady=5)

        # Ползунок для выбора количества строк
        CTkLabel(self.create_db_frame, text="Количество строк:").pack(padx=5, pady=(5, 0))
        self.row_scale = CTkSlider(self.create_db_frame, from_=1, to=100, number_of_steps=99)
        self.row_scale.pack(padx=5, pady=5)

        # Ползунок для выбора количества столбцов
        CTkLabel(self.create_db_frame, text="Количество столбцов:").pack(padx=5, pady=(5, 0))
        self.column_scale = CTkSlider(self.create_db_frame, from_=1, to=26, number_of_steps=25)  # 26 столбцов (a-z)
        self.column_scale.pack(padx=5, pady=5)

        # Кнопка для создания базы данных
        CTkButton(self.create_db_frame, text="Создать базу данных", command=self.create_new_db).pack(padx=5, pady=(10, 5))

    def create_new_database(self):
        
        self.create_db_frame.pack(padx=5, pady=5, fill=BOTH, expand=True)
        self.init_create_db_frame()

    def create_new_db(self):
        db_name = self.db_name_entry.get().strip()
        if not db_name:
            messagebox.showerror("Ошибка", "Пожалуйста, введите название базы данных.")
            return
        
        row_count = self.row_scale.get()
        column_count = int(self.column_scale.get())
        
        # Генерация имен столбцов
        column_names = self.generate_column_names(column_count)

        # Создание файла базы данных
        if not os.path.exists(self.saves_dir):
            os.makedirs(self.saves_dir)
        self.db_file = os.path.join(self.saves_dir, f"{db_name}.ufo")
        
        if os.path.exists(self.db_file):
            messagebox.showinfo("База данных", "Файл базы данных уже существует.")
        else:
            self.db = Relative_DB()
            self.db.create_table("sightings", column_names)
            self.db.save_to_file(self.db_file)
            messagebox.showinfo("База данных", "Новая база данных создана успешно.")
            self.clear_window()
            self.load_frame()

    def generate_column_names(self, count):
        """Генерация имен столбцов от 'a' до 'zzz'."""
        if count < 1 or count > 78:  # Максимум 78 (a - z, aa - zz, aaa - zzz)
            return []
        
        names = []
        for i in range(count):
            name = ""
            while i >= 0:
                name = chr((i % 26) + 97) + name  # 97 - ASCII 'a'
                i = (i // 26) - 1
            names.append(name)
        
        return names

    def clear_window(self):
        self.resizable(True, True)
        self.start_frame.pack_forget()

    def load_frame(self):
        self.resizable(False, False)
        self.start_frame = CTkFrame(self)
        self.start_frame.pack(padx=5, pady=5, fill=BOTH, expand=True)
        self.file_manager = CTkFrame(self.start_frame, width=self._current_width // 1.7)
        self.file_manager.pack(padx=5, pady=5, side=LEFT, fill=Y)
        self.file_toolbar_frame = CTkFrame(self.file_manager, height=50, width=self._current_width // 1.7)
        self.file_toolbar_frame.pack(padx=5, pady=5, fill=X)
        self.interface_menu = CTkFrame(self.start_frame)
        self.interface_menu.pack(padx=(0, 5), pady=5, side=LEFT, fill=BOTH, expand=True)
        self.interface_menu_frame = CTkFrame(self.interface_menu, height=50)
        self.interface_menu_frame.pack(side=TOP, padx=5, pady=5, fill=X)
        self.interface_bottom_frame = CTkFrame(self.interface_menu, height=50)
        self.interface_bottom_frame.pack(side=BOTTOM, padx=5, pady=5, fill=X)
        self.load_im()
        self.load_file_manager()

    def load_im(self):
        self.create_btn = CTkButton(self.interface_menu_frame, text="Create new Table (.ufo)", width=160, height=40,
                  command=lambda: self.create_new_database()).pack(side=LEFT, padx=5, pady=5)
        CTkButton(self.interface_menu_frame, text="Load Table (.ufo)", width=160, height=40,
                  command=self.load_file_dialog).pack(side=LEFT, padx=(0, 5), pady=5)
        
        self.create_db_frame = CTkFrame(self.interface_menu)

        self.bbar = CTkFrame(self.interface_bottom_frame, corner_radius=0)
        self.bbar.pack(side=BOTTOM)
        CTkButton(self.bbar, width=100, text="Authors", command=githubLink).pack(fill=X, expand=True, side=LEFT, padx=(9, 0))
        CTkButton(self.bbar, width=100, text="GitHub", command=AuthorLink).pack(fill=X, expand=True, side=LEFT, padx=5)
        CTkButton(self.bbar, width=100, text="News", command=NewsLink).pack(fill=X, expand=True, side=LEFT, padx=(0, 9))

    def load_file_manager(self):
        CTkLabel(self.file_toolbar_frame, text="Saved Databases:", width=self._current_width // 1.7).pack(padx=5, pady=(5, 0))
        self.file_list_frame = CTkScrollableFrame(self.file_manager)
        self.file_list_frame.pack(padx=5, pady=5, fill=BOTH, expand=True)

        if not os.path.exists(self.saves_dir):
            os.makedirs(self.saves_dir)

        self.refresh_file_list()

    def refresh_file_list(self):
        # Очищаем предыдущий список файлов
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()

        for filename in os.listdir(self.saves_dir):
            if filename.endswith(".ufo"):
                filepath = os.path.join(self.saves_dir, filename)
                timestamp = os.path.getmtime(filepath)
                formatted_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp))

                file_frame = CTkFrame(self.file_list_frame, height=30)
                file_frame.pack(fill=X, padx=2, pady=2)

                file_label = CTkLabel(file_frame, text=filename[:-4], anchor="w")
                file_label.pack(side=LEFT, fill=X, expand=True, padx=5)
                CTkLabel(file_frame, text=formatted_time, width=100, anchor="e").pack(side=RIGHT, padx=5)

                # Обработка клика для открытия файла
                file_label.bind("<Button-1>", lambda event, filepath=filepath: self.open_db_editor(filepath))
                file_label.bind("<Enter>", lambda event: file_label.configure(cursor="hand2"))
                file_label.bind("<Leave>", lambda event: file_label.configure(cursor=""))

    def load_file_dialog(self):
        file_path = filedialog.askopenfilename(title="Select a UFO file", filetypes=[("UFO Files", "*.ufo")])
        if file_path:
            self.copy_file_to_saves(file_path)
            self.refresh_file_list()

    def copy_file_to_saves(self, file_path):
        # Копируем файл в папку saves
        filename = os.path.basename(file_path)
        dest_path = os.path.join(self.saves_dir, filename)
        try:
            shutil.copy(file_path, dest_path)
            messagebox.showinfo("Файл загружен", f"Файл {filename} успешно загружен.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скопировать файл: {e}")

    def open_db_editor(self, db_file):
        DBEditor(self, db_file)

if __name__ == "__main__":
    app = DatabaseApp()
    app.mainloop()
