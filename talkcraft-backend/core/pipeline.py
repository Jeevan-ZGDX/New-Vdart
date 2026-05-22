import threading
import queue
import time
import logging
from typing import Callable, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PipelineQueue:
    def __init__(self, maxsize: int = 30):
        self._queue = queue.Queue(maxsize=maxsize)
        self._lock = threading.Lock()
        self._running = False

    def put(self, item: Any, block: bool = False, timeout: float = 0.01) -> bool:
        try:
            self._queue.put(item, block=block, timeout=timeout)
            return True
        except queue.Full:
            return False

    def get(self, block: bool = False, timeout: float = 0.01) -> Optional[Any]:
        try:
            return self._queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    def task_done(self):
        self._queue.task_done()

    def qsize(self) -> int:
        return self._queue.qsize()

    def empty(self) -> bool:
        return self._queue.empty()

    def clear(self):
        with self._queue.mutex:
            self._queue.queue.clear()


class PipelineStage:
    def __init__(self, name: str, process_fn: Callable, input_queue: PipelineQueue, output_queue: Optional[PipelineQueue] = None):
        self.name = name
        self.process_fn = process_fn
        self.input_queue = input_queue
        self.output_queue = output_queue
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._fps_counter = 0
        self._fps_time = time.time()
        self._current_fps = 0.0

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, name=f"Pipeline-{self.name}", daemon=True)
        self._thread.start()
        logger.info(f"Started pipeline stage: {self.name}")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info(f"Stopped pipeline stage: {self.name}")

    def _run(self):
        logger.info(f"Pipeline stage running: {self.name}")
        while self._running:
            item = self.input_queue.get(block=True, timeout=0.05)
            if item is None:
                continue

            try:
                result = self.process_fn(item)
                if result is not None and self.output_queue:
                    self.output_queue.put(result, block=False)
            except Exception as e:
                logger.error(f"Error in stage {self.name}: {e}")

            self.input_queue.task_done()
            self._update_fps()

    def _update_fps(self):
        self._fps_counter += 1
        elapsed = time.time() - self._fps_time
        if elapsed >= 1.0:
            self._current_fps = self._fps_counter / elapsed
            self._fps_counter = 0
            self._fps_time = time.time()

    @property
    def fps(self) -> float:
        return self._current_fps


class ProcessingPipeline:
    def __init__(self):
        self.stages: list[PipelineStage] = []
        self._running = False

    def add_stage(self, stage: PipelineStage):
        self.stages.append(stage)

    def start(self):
        self._running = True
        for stage in self.stages:
            stage.start()
        logger.info(f"Pipeline started with {len(self.stages)} stages")

    def stop(self):
        self._running = False
        for stage in reversed(self.stages):
            stage.stop()
        logger.info("Pipeline stopped")

    def get_stage(self, name: str) -> Optional[PipelineStage]:
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None

    @property
    def is_running(self) -> bool:
        return self._running
