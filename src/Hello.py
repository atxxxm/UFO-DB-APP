from PIL import Image, ImageTk
import tkinter as tk
import time, sys, os
from .database.DBViewer import *
from .database.DBEdit import *
from .mainScreen import *
from .ui import *

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

def main():
    root = tk.Tk()
    root.overrideredirect(True)  # Убираем рамку окна
    root.attributes('-topmost', True) # Окно поверх всех остальных

    width = 960
    height = 540

    # Получаем размеры экрана
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Центрируем сплэшскрин
    x = (screen_width - 960) // 2
    y = (screen_height - 540) // 2
    root.geometry(f"960x540+{x}+{y}")

    # Загружаем изображение
    try:
        image = Image.open(ASSETS_PATH+"loading.png")
        # Уменьшаем изображение, сохраняя пропорции, до максимального размера 900x600
        image.thumbnail((width, height))  # thumbnail изменяет изображение inplace
        photo = ImageTk.PhotoImage(image)
        label = tk.Label(root, image=photo)
        label.pack(fill=tk.BOTH, expand=True)
    except FileNotFoundError:
        print("Файл loading.png не найден.")
        label = tk.Label(root, text="Loading...", font=("Arial", 24))
        label.pack(expand=True)


    root.update() # Отображаем сплэшскрин

    # Имитируем загрузку (замените на вашу реальную логику загрузки)
    time.sleep(3)

    root.destroy() # Закрываем сплэшскрин


    # Здесь начинается основное приложение
    open_db_editor()

def open_db_editor():
    app = QApplication(sys.argv)
    welcome = WelcomeWindow()
    welcome.show()
    sys.exit(app.exec())
