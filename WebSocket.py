import time
import cv2
import os
from pygrabber.dshow_graph import FilterGraph
import obsws_python as obs
from datetime import datetime


class Camera:
    def __init__(self):
        self.cl = None
        self.flag = False
        self.record_flag = False
        self.stop_cam_all_rec = False
        self.password_value = ""
        self.camera_ultra_name = ""

    def password(self, pwd):
        self.password_value = pwd

    def connect(self):
        """Подключаемся к OBS WebSocket (v5.0+)"""
        try:
            self.cl = obs.ReqClient(host="localhost", port=4455, password=self.password_value, timeout=3)
            self.flag = False
            self.record_flag = False
            print("✅ Подключение к OBS успешно")
        except Exception as e:
            print(f"❌ Ошибка подключения к OBS: {e}")

    def get_camera_ids(self):
        """Получаем ID сцен и источников из OBS"""
        try:
            response = self.cl.get_scene_item_list(scene_name="MainCam")
            ids = {}
            for item in response.scene_items:
                if item['sourceName'] in ['Main', 'Back']:
                    ids[item['sourceName']] = item['sceneItemId']
            return ids
        except Exception as e:
            print(f"⚠️ Ошибка получения ID камер: {e}")
            return {}

    def record_cycle(self, duration=10):
        """Повторная запись OBS каждые duration секунд"""
        if not self.cl:
            print("❌ OBS не подключён")
            return

        try:
            self.record_flag = True
            while self.record_flag:
                print("▶ Начало записи...")
                self.cl.start_record()
                time.sleep(duration)
                self.cl.stop_record()
                print("💾 Запись завершена, новый цикл через 2 секунды...")
                time.sleep(2)
        except Exception as e:
            print(f"⚠️ Ошибка записи: {e}")

    def Start(self, value=5, value1=5):
        """Переключение между камерами"""
        ids = self.get_camera_ids()
        id_main = ids.get("Main")
        id_back = ids.get("Back")

        if id_main is None or id_back is None:
            print("❌ Не удалось найти камеры 'Main' и 'Back' в сцене MainCam")
            return

        self.flag = True
        try:
            while self.flag:
                time.sleep(value)
                self.cl.set_scene_item_enabled(scene_name="MainCam", scene_item_id=id_main, scene_item_enabled=False)
                self.cl.set_scene_item_enabled(scene_name="MainCam", scene_item_id=id_back, scene_item_enabled=True)
                print("🔁 Камера 2 включена, камера 1 выключена.")

                time.sleep(value1)
                self.cl.set_scene_item_enabled(scene_name="MainCam", scene_item_id=id_main, scene_item_enabled=True)
                self.cl.set_scene_item_enabled(scene_name="MainCam", scene_item_id=id_back, scene_item_enabled=False)
                print("🔁 Камера 1 включена, камера 2 выключена.")
        except Exception as e:
            print(f"⚠️ Ошибка при переключении камер: {e}")

    def start_all(self):
        CAMERA_NAME = self.camera_ultra_name
        OUTPUT_FOLDER = "recordings"
        DURATION = 300
        FPS = 30
        self.stop_cam_all_rec = False
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)

        def get_camera_index(name):
            graph = FilterGraph()
            for i, dev_name in enumerate(graph.get_input_devices()):
                if name.lower() in dev_name.lower():
                    return i
            return None

        camera_index = get_camera_index(CAMERA_NAME)
        if camera_index is None:
            print(f"❌ Камера '{CAMERA_NAME}' не найдена")
            return
        else:
            print(f"✅ Камера найдена, индекс: {camera_index}")

        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print("❌ Не удалось открыть камеру")
            return

        # получаем реальные размеры кадра
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"📏 Разрешение камеры: {width}x{height}")

        try:
            while not self.stop_cam_all_rec:
                now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                output_file = os.path.join(OUTPUT_FOLDER, f"record_{now}.avi")
                fourcc = cv2.VideoWriter_fourcc(*"MJPG")  # более совместимый кодек
                out = cv2.VideoWriter(output_file, fourcc, FPS, (width, height))

                start_time = time.time()
                print(f"▶ Начата запись файла {output_file}")

                while time.time() - start_time < DURATION and not self.stop_cam_all_rec:
                    ret, frame = cap.read()
                    if not ret:
                        print("⚠️ Не удалось получить кадр")
                        continue
                    out.write(frame)
                    cv2.imshow("Recording...", frame)
                    if cv2.waitKey(1) & 0xFF == 27:
                        self.stop_cam_all_rec = True
                        break

                out.release()
                print(f"💾 Файл {output_file} завершён")

        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("✅ Камера закрыта, запись завершена")
