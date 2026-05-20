import numpy as np
from typing import Optional
from threading import Lock


class CircularAudioBuffer:
    def __init__(self, max_samples: int, channels: int = 1):
        self._buffer = np.zeros((max_samples, channels), dtype=np.float32)
        self._max_samples = max_samples
        self._channels = channels
        self._write_pos = 0
        self._available = 0
        self._lock = Lock()

    @property
    def available(self) -> int:
        with self._lock:
            return self._available

    def write(self, data: np.ndarray):
        samples = data.shape[0]
        with self._lock:
            if samples >= self._max_samples:
                self._buffer[:] = data[-self._max_samples:]
                self._write_pos = 0
                self._available = self._max_samples
                return

            end_pos = self._write_pos + samples
            if end_pos <= self._max_samples:
                self._buffer[self._write_pos:end_pos] = data
            else:
                first_part = self._max_samples - self._write_pos
                self._buffer[self._write_pos:] = data[:first_part]
                self._buffer[:samples - first_part] = data[first_part:]

            self._write_pos = end_pos % self._max_samples
            self._available = min(self._available + samples, self._max_samples)

    def read(self, num_samples: int) -> np.ndarray:
        with self._lock:
            if self._available == 0:
                return np.zeros((0, self._channels), dtype=np.float32)

            num_samples = min(num_samples, self._available)
            read_start = (self._write_pos - self._available) % self._max_samples
            end_pos = read_start + num_samples

            if end_pos <= self._max_samples:
                result = self._buffer[read_start:end_pos].copy()
            else:
                first_part = self._max_samples - read_start
                result = np.vstack([
                    self._buffer[read_start:],
                    self._buffer[:num_samples - first_part],
                ])

            return result

    def read_latest(self, num_samples: int) -> np.ndarray:
        with self._lock:
            if self._available == 0:
                return np.zeros((0, self._channels), dtype=np.float32)

            num_samples = min(num_samples, self._available)
            read_start = (self._write_pos - num_samples) % self._max_samples
            end_pos = read_start + num_samples

            if end_pos <= self._max_samples:
                result = self._buffer[read_start:end_pos].copy()
            else:
                first_part = self._max_samples - read_start
                result = np.vstack([
                    self._buffer[read_start:],
                    self._buffer[:num_samples - first_part],
                ])

            return result

    def clear(self):
        with self._lock:
            self._buffer.fill(0.0)
            self._write_pos = 0
            self._available = 0

    def get_all(self) -> np.ndarray:
        return self.read(self._available)
