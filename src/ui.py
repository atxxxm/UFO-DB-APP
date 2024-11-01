from customtkinter import *
from tkinter import messagebox
import time,os
from .pyufodb import Relative_DB
from .otherFunc import githubLink, AuthorLink, NewsLink
from .dbEditor import DBEditor

class DatabaseApp(CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Database Interface")
        self.geometry("900x600")
        self.saves_dir = "src/saves"  # Путь к папке с сохранениями
        self.db_file = os.path.join(self.saves_dir, "database.ufo")
        self.load_frame()

    def create_new_database(self):
        # Создание папки для сохранений, если ее нет
        if not os.path.exists(self.saves_dir):
            os.makedirs(self.saves_dir)
        
        # Проверка на существование файла базы данных
        if os.path.exists(self.db_file):
            messagebox.showinfo("База данных", "Файл базы данных уже существует.")
        else:
            # Создаем новую базу данных и сохраняем в файл
            self.db = Relative_DB()
            self.db.create_table("sightings", ["date", "location", "description"])
            self.db.save_to_file(self.db_file)
            messagebox.showinfo("База данных", "Новая база данных создана успешно.")
            self.clear_window()
            self.load_frame()
            #self.load_file_manager()  # Обновляем интерфейс файлов

    def clear_window(self):
        self.resizable(True, True)
        self.start_frame.pack_forget()

    def load_frame(self):
        self.resizable(False, False)
        self.start_frame = CTkFrame(self)

        self.start_frame.pack(padx=5,
                              pady=5,
                              fill=BOTH, 
                              expand=True)

        self.file_manager = CTkFrame(self.start_frame,
                                     width=self._current_width//1.7)
        self.file_manager.pack(padx=5,
                               pady=5,
                               side=LEFT,
                               fill=Y)
        
        self.file_toolbar_frame = CTkFrame(self.file_manager,height=50,width=self._current_width//1.7)
        self.file_toolbar_frame.pack(padx=5,pady=5,fill=X)


        self.interface_menu = CTkFrame(self.start_frame)
        self.interface_menu.pack(padx=(0,5),
                                 pady=5,
                                 side=LEFT,
                                 fill=BOTH,
                                 expand=True)
        
        self.interface_menu_frame = CTkFrame(self.interface_menu,height=50)
        self.interface_menu_frame.pack(side=TOP,padx=5,pady=5,fill=X)

        self.interface_bottom_frame = CTkFrame(self.interface_menu,height=50)
        self.interface_bottom_frame.pack(side=BOTTOM,padx=5,pady=5,fill=X)

        self.load_im()
        self.load_file_manager()

    def load_im(self):
        self.create_new_table = CTkButton(self.interface_menu_frame,
                                          text="Create new Table (.ufo)",
                                          width=160,height=40,
                                          command=lambda: self.create_new_database())
        self.create_new_table.pack(side=LEFT,padx=5,pady=5)

        self.load_table = CTkButton(self.interface_menu_frame,
                                          text="Load Table (.ufo)",
                                          width=160,height=40,
                                          command=lambda: self.clear_window())
        self.load_table.pack(side=LEFT,padx=(0,5),pady=5)

        self.bbar = CTkFrame(self.interface_bottom_frame,corner_radius=0)
        self.bbar.pack(side=BOTTOM)

        self.authors_link = CTkButton(self.bbar,
                                         width=100, 
                                         text="Authors",
                                         command=lambda: githubLink())
        self.authors_link.pack(fill=X,expand=True,side=LEFT,padx=(9,0))

        self.github_link = CTkButton(self.bbar,
                                         width=100, 
                                         text="GitHub",
                                         command=lambda: AuthorLink())
        self.github_link.pack(fill=X,expand=True,side=LEFT,padx=5)

        self.news_link = CTkButton(self.bbar,
                                         width=100, 
                                         text="News",
                                         command=lambda: NewsLink())
        self.news_link.pack(fill=X,expand=True,side=LEFT,padx=(0,9))

    def load_file_manager(self):
        self.file_manager_label = CTkLabel(self.file_toolbar_frame, text="Saved Databases:",width=self._current_width//1.7)
        self.file_manager_label.pack(padx=5, pady=(5, 0))

        self.file_list_frame = CTkScrollableFrame(self.file_manager)
        self.file_list_frame.pack(padx=5, pady=5, fill=BOTH, expand=True)

        # Создаем папку для сохранений, если ее нет
        if not os.path.exists(self.saves_dir):
            os.makedirs(self.saves_dir)


        for filename in os.listdir(self.saves_dir):
            if filename.endswith(".ufo"):
                filepath = os.path.join(self.saves_dir, filename)
                filepath = os.path.join(self.saves_dir, filename)
                timestamp = os.path.getmtime(filepath)
                formatted_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp))

                file_frame = CTkFrame(self.file_list_frame, height=30)
                file_frame.pack(fill=X, padx=2, pady=2)

                file_label = CTkLabel(file_frame, text=filename[:-4], anchor="w")  # Убираем ".ufo"
                file_label.pack(side=LEFT, fill=X, expand=True, padx=5)

                time_label = CTkLabel(file_frame, text=formatted_time, width=100, anchor="e")
                time_label.pack(side=RIGHT, padx=5)

                file_label.bind("<Button-1>", lambda event, filepath=filepath: self.open_db_editor(filepath)) # Bind click to open editor

    def open_editor(self, filepath): # Helper function with the correct scope
        self.open_db_editor(filepath)  # Now calls the correct method

    def open_db_editor(self, db_file): # Original open_db_editor function
        editor = DBEditor(self, db_file)