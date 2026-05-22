import numpy as np
import subprocess
from pathlib import Path
from typing import Optional, Iterator, Tuple

from talkcraft.utils.logger import get_logger


SUPPORTED_EXTENSIONS = {'.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac', '.wma'}

_FFMPEG_AVAILABLE: Optional[bool] = None


def _check_ffmpeg() -> bool:
    global _FFMPEG_AVAILABLE
    if _FFMPEG_AVAILABLE is not None:
        return _FFMPEG_AVAILABLE
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=3
        )
        _FFMPEG_AVAILABLE = result.returncode == 0
    except Exception:
        _FFMPEG_AVAILABLE = False
    return _FFMPEG_AVAILABLE


class AudioFileLoader:
    def __init__(self):
        self._logger = get_logger("talkcraft.audio.file_loader")
        self._has_soundfile = False
        self._has_pydub = False
        self._check_dependencies()

    def _check_dependencies(self):
        try:
            import soundfile
            self._has_soundfile = True
        except ImportError:
            pass
        try:
            from pydub import AudioSegment
            self._has_pydub = True
        except ImportError:
            pass

    def load(self, path: str, target_sr: int = 16000) -> Tuple[np.ndarray, int]:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported format: {ext}. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        data = None
        sr = None

        if self._has_soundfile:
            try:
                import soundfile as sf
                data, sr = sf.read(str(path))
                self._logger.info(f"Loaded {path.name} with soundfile ({sr}Hz)")
            except Exception as e:
                self._logger.debug(f"soundfile failed for {ext}: {e}")
                data = None

        if data is None and self._has_pydub:
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_file(str(path))
                sr = audio.frame_rate
                data = np.array(audio.get_array_of_samples(), dtype=np.float32)
                if audio.channels > 1:
                    data = data.reshape(-1, audio.channels).mean(axis=1)
                self._logger.info(f"Loaded {path.name} with pydub ({sr}Hz)")
            except Exception as e:
                self._logger.debug(f"pydub failed for {ext}: {e}")
                data = None

        if data is None:
            needs_ffmpeg = ext in ('.mp3', '.m4a', '.aac', '.wma') and not _check_ffmpeg()
            if needs_ffmpeg:
                raise RuntimeError(
                    f"Cannot load {path.name} (format: {ext}). "
                    f"ffmpeg is required for {ext} files. "
                    f"Install: winget install ffmpeg  or download from https://ffmpeg.org"
                )
            raise RuntimeError(
                f"Cannot load {path.name} (format: {ext}). "
                f"Install pydub and soundfile: pip install pydub soundfile; "
                f"also install ffmpeg (https://ffmpeg.org) for audio support."
            )

        if data.ndim > 1:
            data = data.mean(axis=1)

        if sr != target_sr:
            data = self._resample(data, sr, target_sr)
            sr = target_sr

        if data.dtype != np.float32:
            data = data.astype(np.float32)

        if np.abs(data).max() > 1.0:
            data = data / 32768.0

        duration = len(data) / sr
        self._logger.info(
            f"Audio prepared: {duration:.1f}s, {sr}Hz, mono, float32"
        )

        return data, sr

    def chunk_generator(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        chunk_duration: float = 2.0,
    ) -> Iterator[np.ndarray]:
        chunk_samples = int(sample_rate * chunk_duration)
        total = len(audio_data)

        for start in range(0, total, chunk_samples):
            end = min(start + chunk_samples, total)
            chunk = audio_data[start:end]

            if len(chunk) < chunk_samples:
                padded = np.zeros(chunk_samples, dtype=np.float32)
                padded[:len(chunk)] = chunk
                chunk = padded

            yield chunk.reshape(-1, 1)

    def _resample(self, data: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        from scipy import signal

        ratio = target_sr / orig_sr
        new_len = int(round(len(data) * ratio))

        if new_len < 2:
            self._logger.warning(f"Audio too short ({len(data)} samples at {orig_sr}Hz)")
            return np.zeros(max(1, new_len), dtype=np.float32)

        resampled = signal.resample(data, new_len)
        return resampled.astype(np.float32)

    @staticmethod
    def format_supported() -> str:
        return ", ".join(sorted(SUPPORTED_EXTENSIONS))
