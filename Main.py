from PySide6.QtWidgets import QApplication
from GUI import TestApp
from WebSocket import Camera
from baza import cam_check
import sys


if __name__ == "__main__":
    app_qt = QApplication(sys.argv)  # создаём экземпляр приложения
    cam = Camera()
    box = cam_check()

    window = TestApp(cam, box)       # создаём окно
    window.show()                    # показываем окно

    sys.exit(app_qt.exec())          # запускаем главный цикл Qt
