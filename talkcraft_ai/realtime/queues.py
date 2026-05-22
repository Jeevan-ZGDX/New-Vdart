import queue
from dataclasses import dataclass, field
from typing import Any, Optional


class MonitoredQueue:
    def __init__(self, maxsize: int = 10, name: str = "queue"):
        self._queue: queue.Queue = queue.Queue(maxsize=maxsize)
        self._maxsize = maxsize
        self._name = name
        self._put_count = 0
        self._get_count = 0
        self._overflow_count = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def qsize(self) -> int:
        return self._queue.qsize()

    @property
    def overflow_count(self) -> int:
        return self._overflow_count

    def put(self, item: Any, block: bool = True, timeout: Optional[float] = None) -> bool:
        try:
            self._queue.put(item, block=block, timeout=timeout)
            self._put_count += 1
            return True
        except queue.Full:
            self._overflow_count += 1
            return False

    def put_nowait(self, item: Any) -> bool:
        try:
            self._queue.put_nowait(item)
            self._put_count += 1
            return True
        except queue.Full:
            self._overflow_count += 1
            return False

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        try:
            item = self._queue.get(block=block, timeout=timeout)
            self._get_count += 1
            return item
        except queue.Empty:
            return None

    def get_nowait(self) -> Any:
        try:
            item = self._queue.get_nowait()
            self._get_count += 1
            return item
        except queue.Empty:
            return None

    def clear(self) -> int:
        count = 0
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                count += 1
            except queue.Empty:
                break
        return count

    def stats(self) -> dict:
        return {
            "name": self._name,
            "size": self.qsize,
            "maxsize": self._maxsize,
            "put": self._put_count,
            "get": self._get_count,
            "overflow": self._overflow_count,
        }

    def __repr__(self) -> str:
        return f"MonitoredQueue({self._name}, size={self.qsize}/{self._maxsize})"


@dataclass
class QueueManager:
    audio: MonitoredQueue = field(default_factory=lambda: MonitoredQueue(5, "audio"))
    transcription: MonitoredQueue = field(default_factory=lambda: MonitoredQueue(10, "transcription"))
    ai_request: MonitoredQueue = field(default_factory=lambda: MonitoredQueue(5, "ai_request"))
    ai_response: MonitoredQueue = field(default_factory=lambda: MonitoredQueue(5, "ai_response"))
    tts: MonitoredQueue = field(default_factory=lambda: MonitoredQueue(5, "tts"))
    feedback: MonitoredQueue = field(default_factory=lambda: MonitoredQueue(10, "feedback"))

    def get_all_stats(self) -> dict:
        return {q.name: q.stats() for q in [
            self.audio, self.transcription, self.ai_request,
            self.ai_response, self.tts, self.feedback,
        ]}

    def clear_all(self) -> None:
        for q in [self.audio, self.transcription, self.ai_request,
                  self.ai_response, self.tts, self.feedback]:
            q.clear()
