import sys
import threading
from functools import partial
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QHBoxLayout, QDialog, QScrollArea, QFrame
)
from PySide6.QtCore import Qt


class TestApp(QWidget):
    def __init__(self, camera_connector, box_connector):
        super().__init__()
        self.connector = camera_connector
        self.box = box_connector

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("OBS Controller")
        self.setFixedSize(600, 800)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Статус
        self.status_label = QLabel("Подключение к OBS...")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Поля ввода
        self.interval_input = QLineEdit("5")
        self.interval_input.setPlaceholderText("Интервал камеры 1 (сек)")

        self.interval_input1 = QLineEdit("5")
        self.interval_input1.setPlaceholderText("Интервал камеры 2 (сек)")

        self.interval_input2 = QLineEdit()
        self.interval_input2.setPlaceholderText("Пароль OBS")

        self.cam_time_input = QLineEdit("10")
        self.cam_time_input.setPlaceholderText("Время записи OBS (сек)")

        for w in [self.interval_input, self.interval_input1, self.interval_input2, self.cam_time_input]:
            w.setFixedHeight(35)
            main_layout.addWidget(w)

        # Кнопки
        buttons = [
            ("Отправить пароль", self.check_password),
            ("Запустить смену камер", self.startsystem),
            ("Остановить смену камер", self.stop_cam_change),
            ("Начать запись OBS", self.rec_stream),
            ("Начать запись камеры", self.start_all_rec),
            ("Остановить запись камеры", self.stop_all_rec_cam),
            ("Меню камер", self.cam_menu),
        ]

        for text, func in buttons:
            btn = QPushButton(text)
            btn.setFixedHeight(40)
            btn.clicked.connect(func)
            main_layout.addWidget(btn)

        self.setLayout(main_layout)

    def check_password(self):
        pwd = self.interval_input2.text().strip()
        if not pwd:
            self.status_label.setText("❌ Введите пароль OBS")
            return
        self.connector.password(pwd)
        self.connector.connect()
        self.status_label.setText("✅ OBS подключен")

    def startsystem(self):
        if not getattr(self.connector, "ws", None):
            self.status_label.setText("❌ Сначала подключитесь к OBS")
            return
        try:
            value = int(self.interval_input.text())
            value1 = int(self.interval_input1.text())
        except ValueError:
            self.status_label.setText("❌ Неверный формат интервала")
            return

        self.connector.flag = True
        threading.Thread(target=self.connector.Start, args=(value, value1), daemon=True).start()
        self.status_label.setText("⏱ Смена камер запущена")

    def stop_cam_change(self):
        self.connector.flag = False
        self.status_label.setText("🛑 Смена камер остановлена")

    def rec_stream(self):
        if not getattr(self.connector, "cl", None):
            self.status_label.setText("❌ OBS не подключен")
            return
        try:
            rec_time = int(self.cam_time_input.text())
        except ValueError:
            self.status_label.setText("❌ Неверный формат времени записи")
            return

        self.connector.record_flag = True
        threading.Thread(target=self.connector.record_cycle, args=(rec_time,), daemon=True).start()
        self.status_label.setText("⏺ Запись OBS запущена")

    def start_all_rec(self):
        threading.Thread(target=self.connector.start_all, daemon=True).start()
        self.status_label.setText("⏺ Запись всех камер запущена")

    def stop_all_rec_cam(self):
        self.connector.stop_cam_all_rec = True
        self.status_label.setText("🛑 Запись всех камер остановлена")

    def closeEvent(self, event):
        self.connector.flag = False
        self.connector.record_flag = False
        self.connector.stop_cam_all_rec = True
        event.accept()

    def cam_menu(self):
        popup = QDialog(self)
        popup.setWindowTitle("Меню камер")
        popup.setFixedSize(400, 400)

        scroll = QScrollArea()
        container = QVBoxLayout()
        frame = QFrame()
        frame_layout = QVBoxLayout(frame)

        cameras = self.box.get_camera_names()
        for cam_name in cameras:
            btn = QPushButton(cam_name)
            btn.clicked.connect(partial(self.cam_unload, cam_name, popup))
            frame_layout.addWidget(btn)

        scroll.setWidgetResizable(True)
        scroll.setWidget(frame)

        container.addWidget(scroll)
        popup.setLayout(container)
        popup.exec()

    def cam_unload(self, cam_name, popup):
        self.connector.camera_ultra_name = cam_name
        popup.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Моки для теста
    class MockConnector:
        def __init__(self):
            self.ws = True
            self.cl = True
            self.flag = False
            self.record_flag = False
            self.stop_cam_all_rec = False
        def password(self, p): pass
        def connect(self): pass
        def Start(self, a, b): print("Start cameras:", a, b)
        def record_cycle(self, t): print("Recording OBS:", t)
        def start_all(self): print("Start all rec")

    class MockBox:
        def get_camera_names(self): return ["Камера 1", "Камера 2", "Камера 3"]

    window = TestApp(MockConnector(), MockBox())
    window.show()
    sys.exit(app.exec())
