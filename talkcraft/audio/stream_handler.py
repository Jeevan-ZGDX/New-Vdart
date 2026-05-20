import numpy as np
import sounddevice as sd
from typing import Optional, Callable
from threading import Event

from talkcraft.utils.logger import get_logger
from talkcraft.utils.config import config


class AudioStreamHandler:
    def __init__(self, callback: Optional[Callable[[np.ndarray], None]] = None):
        self._callback = callback
        self._stream: Optional[sd.InputStream] = None
        self._stop_event = Event()
        self._logger = get_logger("talkcraft.audio.stream")
        self._device = config.audio.device
        self._sample_rate = config.audio.sample_rate
        self._channels = config.audio.channels
        self._blocksize = config.audio.blocksize

    @property
    def is_active(self) -> bool:
        return self._stream is not None and self._stream.active

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def list_devices(self) -> list:
        return sd.query_devices()

    def start(self):
        if self.is_active:
            self._logger.warning("Audio stream already active")
            return

        self._stop_event.clear()

        def audio_callback(indata, frames, time_info, status):
            if status and not self._stop_event.is_set():
                self._logger.debug(f"Audio stream status: {status}")
            if self._stop_event.is_set():
                raise sd.CallbackStop

            audio_chunk = indata.copy()
            if self._callback:
                try:
                    self._callback(audio_chunk)
                except Exception as e:
                    self._logger.error(f"Audio callback error: {e}")

        try:
            self._stream = sd.InputStream(
                device=self._device,
                samplerate=self._sample_rate,
                channels=self._channels,
                blocksize=self._blocksize,
                dtype=config.audio.dtype,
                callback=audio_callback,
            )
            self._stream.start()
            self._logger.info(
                f"Audio stream started (rate={self._sample_rate}, "
                f"channels={self._channels}, blocksize={self._blocksize})"
            )
        except Exception as e:
            self._logger.error(f"Failed to start audio stream: {e}")
            raise

    def stop(self):
        self._stop_event.set()
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
                self._logger.info("Audio stream stopped")
            except Exception as e:
                self._logger.error(f"Error stopping audio stream: {e}")
            finally:
                self._stream = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
