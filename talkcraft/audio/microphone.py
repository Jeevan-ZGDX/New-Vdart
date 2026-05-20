import numpy as np
from queue import Queue
from typing import Optional

from talkcraft.utils.logger import get_logger
from talkcraft.utils.config import config
from talkcraft.audio.stream_handler import AudioStreamHandler


class MicrophoneRecorder:
    def __init__(self, audio_queue: Queue):
        self._audio_queue = audio_queue
        self._logger = get_logger("talkcraft.audio.mic")
        self._stream_handler: Optional[AudioStreamHandler] = None

        chunk_samples = config.audio.chunk_samples
        self._chunk_buf = np.zeros(chunk_samples, dtype=np.float32)
        self._chunk_pos = 0

    @property
    def is_recording(self) -> bool:
        return self._stream_handler is not None and self._stream_handler.is_active

    def _audio_callback(self, chunk: np.ndarray):
        chunk = chunk[:, 0]

        chunk_samples = len(self._chunk_buf)
        samples = chunk.shape[0]
        space = chunk_samples - self._chunk_pos
        copy_len = samples if samples < space else space

        self._chunk_buf[self._chunk_pos:self._chunk_pos + copy_len] = chunk[:copy_len]
        self._chunk_pos += copy_len

        if self._chunk_pos >= chunk_samples:
            self._audio_queue.put_nowait(self._chunk_buf.copy())
            self._chunk_buf.fill(0.0)
            self._chunk_pos = 0

            overflow = samples - copy_len
            if overflow > 0:
                self._chunk_buf[:overflow] = chunk[copy_len:]
                self._chunk_pos = overflow

    def start(self):
        if self.is_recording:
            self._logger.warning("Already recording")
            return

        self._chunk_pos = 0
        self._chunk_buf.fill(0.0)

        self._stream_handler = AudioStreamHandler(callback=self._audio_callback)
        self._stream_handler.start()
        self._logger.info("Microphone recording started")

    def stop(self):
        if self._stream_handler:
            self._stream_handler.stop()
            self._stream_handler = None
        self._logger.info("Microphone recording stopped")
