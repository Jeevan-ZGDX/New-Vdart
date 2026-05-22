import queue
import threading
import time
from typing import Optional, Callable

from talkcraft_ai.utils.config import config
from talkcraft_ai.utils.logger import get_logger

logger = get_logger("tts_engine")


class TTSEngine:
    def __init__(self):
        self._enabled = config.tts.enabled
        self._rate = config.tts.rate
        self._volume = config.tts.volume
        self._voice_id = config.tts.voice_id
        self._engine = None
        self._queue: queue.Queue = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._current_text: str = ""
        self._on_start: Optional[Callable[[str], None]] = None
        self._on_done: Optional[Callable[[str], None]] = None
        self._lock = threading.Lock()
        if self._enabled:
            self._init_engine()

    def _init_engine(self) -> None:
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self._rate)
            self._engine.setProperty("volume", self._volume)
            if self._voice_id is not None:
                voices = self._engine.getProperty("voices")
                if 0 <= self._voice_id < len(voices):
                    self._engine.setProperty("voice", voices[self._voice_id].id)
            logger.info("TTS engine initialized")
        except ImportError:
            logger.warning("pyttsx3 not installed, TTS disabled")
            self._enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self._enabled = False

    def set_callbacks(
        self,
        on_start: Optional[Callable[[str], None]] = None,
        on_done: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._on_start = on_start
        self._on_done = on_done

    @property
    def is_speaking(self) -> bool:
        return self._current_text != ""

    @property
    def enabled(self) -> bool:
        return self._enabled

    def start(self) -> None:
        if not self._enabled:
            return
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="tts-worker")
        self._thread.start()
        logger.info("TTS worker started")

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        with self._lock:
            self._current_text = ""

    def speak(self, text: str) -> None:
        if not self._enabled or not text.strip():
            return
        self._queue.put(text)

    def _run(self) -> None:
        while self._running:
            try:
                text = self._queue.get(timeout=0.5)
                if text is None:
                    break
                self._speak_sync(text)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"TTS worker error: {e}")

    def _speak_sync(self, text: str) -> None:
        with self._lock:
            self._current_text = text
        if self._on_start:
            try:
                self._on_start(text)
            except Exception:
                pass
        try:
            if self._engine is not None:
                self._engine.say(text)
                self._engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS speak error: {e}")
        with self._lock:
            self._current_text = ""
        if self._on_done:
            try:
                self._on_done(text)
            except Exception:
                pass

    def set_rate(self, rate: int) -> None:
        self._rate = rate
        if self._engine is not None:
            try:
                self._engine.setProperty("rate", rate)
            except Exception:
                pass

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, volume))
        if self._engine is not None:
            try:
                self._engine.setProperty("volume", self._volume)
            except Exception:
                pass
