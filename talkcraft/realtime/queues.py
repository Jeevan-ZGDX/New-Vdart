import time
from queue import Queue, Full, Empty
from typing import Any, Optional
from dataclasses import dataclass, field

from talkcraft.utils.logger import get_logger
from talkcraft.utils.config import config


@dataclass
class QueueStats:
    audio_queue_size: int = 0
    transcription_queue_size: int = 0
    analysis_queue_size: int = 0
    feedback_queue_size: int = 0
    total_audio_chunks: int = 0
    total_transcriptions: int = 0
    total_analyses: int = 0
    total_feedback: int = 0
    dropped_chunks: int = 0
    queue_overflows: int = 0
    timestamp: float = field(default_factory=time.time)


class MonitoredQueue:
    def __init__(self, maxsize: int = 0, name: str = "queue"):
        self._queue = Queue(maxsize=maxsize)
        self._maxsize = maxsize
        self._name = name
        self._logger = get_logger(f"talkcraft.queue.{name}")
        self._put_count = 0
        self._get_count = 0
        self._overflow_count = 0

    def put(self, item: Any, block: bool = True, timeout: Optional[float] = None) -> bool:
        try:
            self._queue.put(item, block=block, timeout=timeout)
            self._put_count += 1
            return True
        except Full:
            self._overflow_count += 1
            self._logger.warning(f"{self._name} overflow (put_count={self._put_count})")
            return False

    def put_nowait(self, item: Any) -> bool:
        return self.put(item, block=False)

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        try:
            item = self._queue.get(block=block, timeout=timeout)
            self._get_count += 1
            return item
        except Empty:
            raise

    def get_nowait(self) -> Any:
        return self.get(block=False)

    def task_done(self):
        self._queue.task_done()

    def qsize(self) -> int:
        return self._queue.qsize()

    def empty(self) -> bool:
        return self._queue.empty()

    def full(self) -> bool:
        return self._queue.full()

    @property
    def name(self) -> str:
        return self._name

    @property
    def overflow_count(self) -> int:
        return self._overflow_count

    @property
    def put_count(self) -> int:
        return self._put_count


class QueueManager:
    def __init__(self):
        qcfg = config.queues
        self.audio_queue = MonitoredQueue(maxsize=qcfg.audio_queue_maxsize, name="audio")
        self.transcription_queue = MonitoredQueue(maxsize=qcfg.transcription_queue_maxsize, name="transcription")
        self.analysis_queue = MonitoredQueue(maxsize=qcfg.analysis_queue_maxsize, name="analysis")
        self.feedback_queue = MonitoredQueue(maxsize=qcfg.feedback_queue_maxsize, name="feedback")
    def get_stats(self) -> QueueStats:
        return QueueStats(
            audio_queue_size=self.audio_queue.qsize(),
            transcription_queue_size=self.transcription_queue.qsize(),
            analysis_queue_size=self.analysis_queue.qsize(),
            feedback_queue_size=self.feedback_queue.qsize(),
            total_audio_chunks=self.audio_queue.put_count,
            total_transcriptions=self.transcription_queue.put_count,
            total_analyses=self.analysis_queue.put_count,
            total_feedback=self.feedback_queue.put_count,
            dropped_chunks=self.audio_queue.overflow_count,
            queue_overflows=(
                self.audio_queue.overflow_count
                + self.transcription_queue.overflow_count
                + self.analysis_queue.overflow_count
                + self.feedback_queue.overflow_count
            ),
        )

    def clear_all(self):
        for q in [self.audio_queue, self.transcription_queue,
                  self.analysis_queue, self.feedback_queue]:
            while not q.empty():
                try:
                    q.get_nowait()
                except Empty:
                    break
