import time
import numpy as np
from queue import Queue, Empty
from typing import Optional
from threading import Thread, Event

from talkcraft.utils.logger import get_logger
from talkcraft.utils.config import config
from talkcraft.transcription.whisper_engine import WhisperEngine


class TranscriptionWorker:
    def __init__(self, audio_queue: Queue, transcription_queue: Queue):
        self._audio_queue = audio_queue
        self._transcription_queue = transcription_queue
        self._engine = WhisperEngine()
        self._thread: Optional[Thread] = None
        self._stop_event = Event()
        self._logger = get_logger("talkcraft.transcription.worker")
        self._accumulated_text = ""
        self._last_transcription_time = time.time()

    def start(self):
        if self._thread and self._thread.is_alive():
            self._logger.warning("Transcription worker already running")
            return

        self._stop_event.clear()
        self._engine.load_model()
        self._thread = Thread(target=self._run, name="TranscriptionWorker", daemon=True)
        self._thread.start()
        self._logger.info("Transcription worker started")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)
            if self._thread.is_alive():
                self._logger.warning("Transcription worker did not stop cleanly")
        self._logger.info("Transcription worker stopped")

    def _run(self):
        while not self._stop_event.is_set():
            try:
                audio_chunk = self._audio_queue.get(timeout=0.5)
            except Empty:
                continue

            try:
                result = self._engine.transcribe(audio_chunk)
                if result and result["text"]:
                    text = result["text"]
                    now = time.time()
                    elapsed = now - self._last_transcription_time

                    transcription_data = {
                        "text": text,
                        "timestamp": now,
                        "duration": result.get("duration", 0),
                        "word_count": result.get("word_count", 0),
                        "segments": result.get("segments", []),
                        "interval": elapsed,
                    }

                    try:
                        self._transcription_queue.put_nowait(transcription_data)
                    except Exception:
                        self._logger.warning("Transcription queue full - dropping result")

                    self._accumulated_text = text
                    self._last_transcription_time = now
                    self._logger.debug(f"Transcribed: {text[:60]}...")

            except Exception as e:
                self._logger.error(f"Transcription processing error: {e}")
            finally:
                self._audio_queue.task_done()

    @property
    def accumulated_text(self) -> str:
        return self._accumulated_text
