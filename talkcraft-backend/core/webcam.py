import cv2
import threading
import time
import logging
from core.pipeline import PipelineQueue

logger = logging.getLogger(__name__)


class WebcamCapture:
    def __init__(self, device_index: int = 0, target_fps: int = 15, frame_width: int = 640, frame_height: int = 480):
        self.device_index = device_index
        self.target_fps = target_fps
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.output_queue = PipelineQueue(maxsize=15)

        self._cap: cv2.VideoCapture | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._frame_count = 0
        self._fps_time = time.time()
        self._current_fps = 0.0
        self._last_frame = None
        self._lock = threading.Lock()

    def start(self):
        self._cap = cv2.VideoCapture(self.device_index)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open webcam at device {self.device_index}")

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self._cap.set(cv2.CAP_PROP_FPS, self.target_fps)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, name="WebcamCapture", daemon=True)
        self._thread.start()
        logger.info(f"Webcam capture started (device={self.device_index}, target_fps={self.target_fps})")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3.0)
        if self._cap:
            self._cap.release()
            self._cap = None
        logger.info("Webcam capture stopped")

    def _capture_loop(self):
        frame_interval = 1.0 / self.target_fps
        last_frame_time = time.time()

        while self._running:
            current_time = time.time()
            elapsed = current_time - last_frame_time

            if elapsed >= frame_interval:
                ret, frame = self._cap.read()
                if ret:
                    with self._lock:
                        self._last_frame = frame.copy()
                    self.output_queue.put((current_time, frame), block=False)
                    self._update_fps()
                    last_frame_time = current_time
                else:
                    logger.warning("Failed to read frame from webcam")
                    time.sleep(0.01)
            else:
                time.sleep(max(0, frame_interval - elapsed))

    def _update_fps(self):
        self._frame_count += 1
        elapsed = time.time() - self._fps_time
        if elapsed >= 1.0:
            self._current_fps = self._frame_count / elapsed
            self._frame_count = 0
            self._fps_time = time.time()

    def get_last_frame(self):
        with self._lock:
            return self._last_frame

    @property
    def fps(self) -> float:
        return self._current_fps

    @property
    def is_running(self) -> bool:
        return self._running
