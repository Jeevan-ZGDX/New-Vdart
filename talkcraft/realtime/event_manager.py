import time
from typing import Callable, Dict, List, Any, Optional
from threading import Lock
from enum import Enum, auto

from talkcraft.utils.logger import get_logger


class EventType(Enum):
    TRANSCRIPTION_UPDATE = auto()
    ANALYSIS_UPDATE = auto()
    FEEDBACK_UPDATE = auto()
    METRICS_UPDATE = auto()
    AUDIO_LEVEL = auto()
    ERROR_OCCURRED = auto()
    STATUS_CHANGE = auto()
    QUEUE_STATS = auto()
    ALL = auto()


class EventManager:
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }
        self._lock = Lock()
        self._logger = get_logger("talkcraft.events")
        self._event_history: List[Dict[str, Any]] = []
        self._max_history = 200

    def subscribe(self, event_type: EventType, callback: Callable):
        with self._lock:
            if event_type == EventType.ALL:
                for et in EventType:
                    if et != EventType.ALL:
                        if callback not in self._subscribers[et]:
                            self._subscribers[et].append(callback)
            else:
                if callback not in self._subscribers[event_type]:
                    self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable):
        with self._lock:
            if event_type == EventType.ALL:
                for et in EventType:
                    if et != EventType.ALL:
                        if callback in self._subscribers[et]:
                            self._subscribers[et].remove(callback)
            else:
                if callback in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(callback)

    def emit(self, event_type: EventType, data: Any = None):
        with self._lock:
            callbacks = list(self._subscribers.get(event_type, []))
            timestamp = time.time()

        event_record = {
            "type": event_type,
            "data": data,
            "timestamp": timestamp,
        }

        self._event_history.append(event_record)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

        for callback in callbacks:
            try:
                callback(data)
            except Exception as e:
                self._logger.error(f"Event callback error: {e}")

    def get_recent_events(self, count: int = 10) -> List[Dict[str, Any]]:
        return self._event_history[-count:]

    def clear_history(self):
        self._event_history.clear()


event_manager = EventManager()
