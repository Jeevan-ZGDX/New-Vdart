import time
import numpy as np
from typing import Optional, List, Dict, Any
from threading import Lock

from talkcraft.utils.logger import get_logger
from talkcraft.utils.config import config


class WhisperEngine:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self._model = None
        self._logger = get_logger("talkcraft.transcription.engine")
        self._loaded = False
        self._initialized = True

    def load_model(self):
        if self._loaded:
            return

        self._logger.info(
            f"Loading whisper model: {config.transcription.model_size} "
            f"(device={config.transcription.device}, "
            f"compute={config.transcription.compute_type})"
        )
        start = time.time()

        try:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                model_size_or_path=config.transcription.model_size,
                device=config.transcription.device,
                compute_type=config.transcription.compute_type,
                download_root=None,
                cpu_threads=4,
                num_workers=1,
            )
            self._loaded = True
            self._logger.info(
                f"Model loaded in {time.time() - start:.2f}s"
            )
        except ImportError:
            self._logger.error(
                "faster-whisper not installed. "
                "Run: pip install faster-whisper"
            )
            raise
        except Exception as e:
            self._logger.error(f"Failed to load whisper model: {e}")
            raise

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def transcribe(self, audio: np.ndarray) -> Optional[Dict[str, Any]]:
        if not self._loaded:
            self.load_model()

        try:
            audio_float = audio.squeeze().astype(np.float32)

            if np.abs(audio_float).max() > 1.0:
                audio_float = audio_float / 32768.0

            segments, info = self._model.transcribe(
                audio_float,
                language=config.transcription.language,
                beam_size=config.transcription.beam_size,
                best_of=config.transcription.best_of,
                vad_filter=config.transcription.vad_filter,
                vad_parameters=config.transcription.vad_parameters,
                without_timestamps=False,
                condition_on_previous_text=False,
                compression_ratio_threshold=2.0,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.6,
            )

            segments_list = list(segments)
            full_text = " ".join(seg.text.strip() for seg in segments_list).strip()

            if not full_text:
                return None

            word_count = len(full_text.split())
            duration = info.duration if info and info.duration else 0

            result = {
                "text": full_text,
                "segments": [
                    {
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text.strip(),
                        "avg_logprob": seg.avg_logprob,
                    }
                    for seg in segments_list
                ],
                "language": info.language if info else "en",
                "duration": duration,
                "word_count": word_count,
            }

            return result

        except Exception as e:
            self._logger.error(f"Transcription error: {e}")
            return None

    def unload(self):
        if self._model:
            self._model = None
            self._loaded = False
            self._logger.info("Model unloaded")
