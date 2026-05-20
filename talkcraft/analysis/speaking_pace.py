import time
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from collections import deque

from talkcraft.utils.logger import get_logger
from talkcraft.utils.config import config


class SpeakingPace:
    def __init__(self):
        self._logger = get_logger("talkcraft.analysis.pace")
        self._max_wpm = config.analysis.max_words_per_minute
        self._min_wpm = config.analysis.min_words_per_minute

        self._word_timestamps: deque = deque(maxlen=1000)
        self._pace_history: deque = deque(maxlen=50)
        self._chunk_durations: deque = deque(maxlen=50)
        self._total_words = 0
        self._total_chunks = 0

    def analyze(self, text: str, timestamp: float, duration: float) -> Optional[Dict[str, Any]]:
        if not text or duration <= 0:
            return None

        start = time.time()
        word_count = len(text.split())

        if word_count == 0:
            return None

        self._total_words += word_count
        self._total_chunks += 1
        self._word_timestamps.append((timestamp, word_count))
        self._chunk_durations.append(duration)

        current_wpm = (word_count / duration) * 60.0 if duration > 0 else 0.0

        self._pace_history.append(current_wpm)

        avg_wpm = self._calculate_average_wpm(window_seconds=30.0)
        variability = self._calculate_variability()
        trend = self._get_pace_trend()
        consistency = self._calculate_consistency()

        status = "normal"
        severity = 0
        if current_wpm > self._max_wpm:
            status = "too_fast"
            severity = min(5, int((current_wpm - self._max_wpm) / 10) + 1)
        elif current_wpm < self._min_wpm:
            status = "too_slow"
            severity = min(3, int((self._min_wpm - current_wpm) / 10) + 1)

        result = {
            "current_wpm": round(current_wpm, 1),
            "average_wpm": round(avg_wpm, 1),
            "word_count": word_count,
            "total_words": self._total_words,
            "duration": duration,
            "status": status,
            "severity": severity,
            "max_wpm": self._max_wpm,
            "min_wpm": self._min_wpm,
            "variability": variability,
            "trend": trend,
            "consistency": consistency,
            "processing_time": time.time() - start,
        }

        return result

    def _calculate_average_wpm(self, window_seconds: float = 30.0) -> float:
        if not self._word_timestamps:
            return 0.0

        now = time.time()
        cutoff = now - window_seconds
        recent_words = [(ts, wc) for ts, wc in self._word_timestamps if ts >= cutoff]

        if not recent_words:
            return 0.0

        total_words_in_window = sum(wc for _, wc in recent_words)
        time_span = min(
            window_seconds,
            recent_words[-1][0] - recent_words[0][0] + 1.0
        )

        if time_span <= 0:
            return 0.0

        return (total_words_in_window / time_span) * 60.0

    def _calculate_variability(self) -> Dict[str, Any]:
        if len(self._pace_history) < 3:
            return {"score": 0.5, "description": "insufficient_data"}

        recent = list(self._pace_history)[-10:]
        if len(recent) < 3:
            recent = list(self._pace_history)

        mean = np.mean(recent)
        if mean == 0:
            return {"score": 0.5, "description": "neutral"}

        std = np.std(recent)
        cv = std / mean

        if cv < 0.1:
            return {"score": round(cv, 3), "description": "very_consistent", "label": "Very steady pace"}
        elif cv < 0.2:
            return {"score": round(cv, 3), "description": "consistent", "label": "Consistent pace"}
        elif cv < 0.35:
            return {"score": round(cv, 3), "description": "moderate", "label": "Moderately varied pace"}
        else:
            return {"score": round(cv, 3), "description": "erratic", "label": "Highly varied pace — try to steady"}

    def _calculate_consistency(self) -> float:
        if len(self._pace_history) < 5:
            return 1.0
        recent = list(self._pace_history)[-5:]
        mean = np.mean(recent)
        if mean == 0:
            return 1.0
        max_dev = max(abs(w - mean) for w in recent)
        return max(0.0, 1.0 - max_dev / mean)

    def _get_pace_trend(self) -> str:
        if len(self._pace_history) < 5:
            return "stable"

        recent = list(self._pace_history)[-5:]
        if recent[-1] > recent[0] * 1.15:
            return "increasing"
        elif recent[-1] < recent[0] * 0.85:
            return "decreasing"
        return "stable"

    def get_session_summary(self) -> Dict[str, Any]:
        if not self._pace_history:
            return {"average_wpm": 0, "min_wpm": 0, "max_wpm": 0, "total_words": 0}

        return {
            "average_wpm": round(np.mean(self._pace_history), 1) if self._pace_history else 0,
            "min_wpm": round(min(self._pace_history), 1) if self._pace_history else 0,
            "max_wpm": round(max(self._pace_history), 1) if self._pace_history else 0,
            "total_words": self._total_words,
            "total_chunks": self._total_chunks,
            "variability": self._calculate_variability(),
        }

    @property
    def recent_pace(self) -> List[float]:
        return list(self._pace_history)

    def reset(self):
        self._word_timestamps.clear()
        self._pace_history.clear()
        self._chunk_durations.clear()
        self._total_words = 0
        self._total_chunks = 0
