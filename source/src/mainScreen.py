import sys, os, time, random
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from .ui import DBEditor 
from .web import openURLGitHub, openURLAuthors

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

greeting = [
    "Добро пожаловать!",
    "Как дела?",
    "Рад тебя видеть!",
    "Приветствую!",
    "Здравствуй!",
    "Готов к работе?",
    "Чем сегодня займемся?",
    "Что будем делать?",
    "Надеюсь, у тебя всё хорошо!",
    "Приятно снова тебя видеть!",
    "Что нового?",
    "Какие планы на сегодня?",
    "Давай начнём!",
    "Приступим к работе!",
    "Я готов к твоим командам!",
    "Жду твоих указаний!",
    "Что тебя интересует?",
    "Чем могу помочь?",
    "В чём нуждаешься?",
    "Какая задача сегодня?",
    "С чем я могу тебе помочь?",
    "Обращайся, всегда рад помочь!",
    "Не стесняйся, спрашивай!",
    "Сегодня мы покорим новые вершины!",
    "Вперёд к новым достижениям!",
    "Удачного дня!",
    "Пусть работа будет лёгкой!",
    "Надеюсь, день пройдёт продуктивно!",
    "За работу!",
    "Поехали!"
]

class WelcomeWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Welcome")
        self.setWindowIcon(QIcon(ASSETS_PATH+"icon.png"))
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self.setFixedSize(800, 600)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(20) 
        self.setLayout(main_layout)
        self.setStyleSheet("background-color: #222222;")

        logo_path = ASSETS_PATH+'ufo_logo.png'
        if os.path.exists(logo_path):
            logo = QLabel()
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio) 
            logo.setPixmap(pixmap)
            logo.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(logo)
            
        self.title = QLabel("")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 40px; font-weight: bold; color: #ffffff;") 
        self.full_text = "UFO DATABASE"
        self.current_text = ""
        self.text_index = 0
        self.start_text_animation()
        main_layout.addWidget(self.title)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(30)
        self.create_button("GitHub", ASSETS_PATH+"github.png", self.GitHub, buttons_layout)
        self.create_button("Авторы", ASSETS_PATH+"authors.png", self.Authors, buttons_layout)
        self.create_button("Справка", ASSETS_PATH+"help.png", lambda: None, buttons_layout) 
        main_layout.addLayout(buttons_layout)


        greet = random.choice(greeting)
        description = QLabel(greet)
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet("color: #aaaaaa; font-size: 18px;") 
        main_layout.addWidget(description)

        startButton = QPushButton("Начать")
        startButton.setStyleSheet("color: #ffffff; background-color: #5555ff; font-size: 18px; padding: 10px 20px; border-radius: 5px;") 
        startButton.setFixedWidth(200)
        startButton.clicked.connect(self.Start)
        main_layout.addWidget(startButton, alignment=Qt.AlignCenter)


        self.version_label = QLabel("Версия: 1.2 beta")
        self.version_label.setStyleSheet("color: #aaaaaa; font-size: 14px; padding-top: 5px;")
        main_layout.addWidget(self.version_label, alignment=Qt.AlignLeft) 

    def create_button(self, text, icon_path, callback, layout):
        button = QPushButton(text)
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(32,32)) 
        button.setStyleSheet("color: #ffffff; background-color: #333333; border: none; border-radius: 5px; padding: 10px 20px;") 
        button.clicked.connect(callback)
        layout.addWidget(button)


    def start_text_animation(self):
        self.full_text = "UFO DATABASE"
        self.current_text = ""
        self.text_index = 0
        self.typing_speed = 15  
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_title_text)
        self.timer.start(1000 // self.typing_speed)

    def update_title_text(self):
        if self.text_index < len(self.full_text):
            self.current_text += self.full_text[self.text_index]
            self.title.setText(self.current_text)
            self.text_index += 1
            time.sleep(random.uniform(0.05, 0.15)) 
            QApplication.processEvents()
        else:
            self.timer.stop()

    def GitHub(self):
        openURLGitHub()

    def Authors(self):
        openURLAuthors()

    def Start(self):
        dialog = DBEditor()
        dialog.showMaximized()
        self.close()  # Закрываем главное окно
        app.exec() # Запускаем цикл событий приложения

if __name__ == "__main__":
    app = QApplication(sys.argv)
    welcome = WelcomeWindow()
    welcome.show()
    sys.exit(app.exec())