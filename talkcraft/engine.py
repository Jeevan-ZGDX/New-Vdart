import time
import numpy as np
from typing import Optional
from threading import Thread, Event
from pathlib import Path

from talkcraft.utils.logger import get_logger
from talkcraft.utils.config import config
from talkcraft.realtime.queues import QueueManager
from talkcraft.realtime.workers import AnalysisWorker, FeedbackWorker
from talkcraft.realtime.event_manager import event_manager, EventType
from talkcraft.audio.microphone import MicrophoneRecorder
from talkcraft.audio.file_loader import AudioFileLoader
from talkcraft.transcription.transcription_worker import TranscriptionWorker
from talkcraft.analysis.grammar_checker import GrammarChecker
from talkcraft.analysis.filler_detector import FillerDetector
from talkcraft.analysis.speaking_pace import SpeakingPace
from talkcraft.analysis.speech_patterns import SpeechPatterns
from talkcraft.feedback.feedback_engine import FeedbackEngine
from talkcraft.ui.dashboard import shared_state


class FileFeederThread:
    def __init__(self, audio_queue, audio_data: np.ndarray, sample_rate: int):
        self._audio_queue = audio_queue
        self._audio_data = audio_data
        self._sample_rate = sample_rate
        self._chunk_duration = config.audio.chunk_duration
        self._stop_event = Event()
        self._thread: Optional[Thread] = None
        self._logger = get_logger("talkcraft.engine.file_feeder")

    @property
    def total_chunks(self) -> int:
        chunk_samples = int(self._sample_rate * self._chunk_duration)
        total = len(self._audio_data)
        return (total + chunk_samples - 1) // chunk_samples

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(target=self._run, name="FileFeeder", daemon=True)
        self._thread.start()
        self._logger.info(f"File feeder started ({self.total_chunks} chunks)")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)

    def _run(self):
        chunk_samples = int(self._sample_rate * self._chunk_duration)
        total = len(self._audio_data)
        chunk_duration_sec = chunk_samples / self._sample_rate

        for start in range(0, total, chunk_samples):
            if self._stop_event.is_set():
                break

            end = min(start + chunk_samples, total)
            chunk = self._audio_data[start:end]

            if len(chunk) < chunk_samples:
                padded = np.zeros(chunk_samples, dtype=np.float32)
                padded[:len(chunk)] = chunk
                chunk = padded

            chunk_2d = chunk.reshape(-1, 1)
            self._audio_queue.put(chunk_2d)

            actual_duration = (end - start) / self._sample_rate
            sleep_time = max(0, actual_duration - 0.05)
            self._stop_event.wait(sleep_time)

        self._logger.info("File feeder finished")
        shared_state.is_recording = False


class TalkCraftEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self._logger = get_logger("talkcraft.engine")
        self._queue_manager = QueueManager()
        self._running = False
        self._input_mode = "mic"

        self._grammar_checker = GrammarChecker()
        self._filler_detector = FillerDetector()
        self._speaking_pace = SpeakingPace()
        self._speech_patterns = SpeechPatterns()
        self._feedback_engine = FeedbackEngine()

        self._microphone: Optional[MicrophoneRecorder] = None
        self._file_feeder: Optional[FileFeederThread] = None
        self._transcription_worker: Optional[TranscriptionWorker] = None
        self._analysis_worker: Optional[AnalysisWorker] = None
        self._feedback_worker: Optional[FeedbackWorker] = None

        self._start_time: float = 0.0
        self._initialized = True

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def input_mode(self) -> str:
        return self._input_mode

    @property
    def session_duration(self) -> float:
        if self._start_time == 0:
            return 0.0
        return time.time() - self._start_time

    def _start_pipeline(self):
        try:
            self._grammar_checker.load()
        except Exception as e:
            self._logger.warning(f"Grammar checker not available: {e}")

        self._transcription_worker = TranscriptionWorker(
            audio_queue=self._queue_manager.audio_queue,
            transcription_queue=self._queue_manager.transcription_queue,
        )
        self._transcription_worker.start()

        self._analysis_worker = AnalysisWorker(
            transcription_queue=self._queue_manager.transcription_queue,
            analysis_queue=self._queue_manager.analysis_queue,
            grammar_checker=self._grammar_checker,
            filler_detector=self._filler_detector,
            speaking_pace=self._speaking_pace,
            speech_patterns=self._speech_patterns,
        )
        self._analysis_worker.start()

        self._feedback_worker = FeedbackWorker(
            analysis_queue=self._queue_manager.analysis_queue,
            feedback_queue=self._queue_manager.feedback_queue,
            feedback_engine=self._feedback_engine,
        )
        self._feedback_worker.start()

    def start_mic(self):
        if self._running:
            self.stop()

        self._logger.info("Starting TalkCraft microphone mode...")
        self._running = True
        self._input_mode = "mic"
        self._start_time = time.time()

        self._start_pipeline()

        self._microphone = MicrophoneRecorder(
            audio_queue=self._queue_manager.audio_queue,
        )

        shared_state.is_recording = True
        self._microphone.start()
        self._logger.info("Microphone mode started")

    def start_file(self, file_path: str) -> bool:
        if self._running:
            self.stop()

        self._logger.info(f"Starting TalkCraft file mode: {file_path}")

        try:
            loader = AudioFileLoader()
            audio_data, sample_rate = loader.load(file_path)
        except (FileNotFoundError, RuntimeError, ValueError) as e:
            self._logger.error(f"Failed to load audio file: {e}")
            return False

        self._running = True
        self._input_mode = "file"
        self._start_time = time.time()

        self._start_pipeline()

        self._file_feeder = FileFeederThread(
            audio_queue=self._queue_manager.audio_queue,
            audio_data=audio_data,
            sample_rate=sample_rate,
        )

        shared_state.is_recording = True
        shared_state.transcription_text = ""
        shared_state.transcription_history.clear()
        shared_state.feedback_messages.clear()
        self._filler_detector.reset()
        self._speaking_pace.reset()
        self._feedback_engine.reset()

        self._file_feeder.start()
        self._logger.info("File mode started")
        return True

    def poll_updates(self):
        if not self._running:
            return

        shared_state.session_duration = self.session_duration

        try:
            feedback = self._queue_manager.feedback_queue.get_nowait()
            messages = feedback.get("messages", [])
            analysis = feedback.get("analysis", {})
            for msg in messages:
                shared_state.update_feedback(msg)
            if analysis:
                shared_state.update_metrics(analysis)
                text = analysis.get("text", "")
                if text:
                    shared_state.update_transcription(text)
            event_manager.emit(EventType.FEEDBACK_UPDATE, feedback)
            self._queue_manager.feedback_queue.task_done()
        except Exception:
            pass

    def stop(self):
        self._logger.info("Stopping TalkCraft engine...")
        self._running = False
        shared_state.is_recording = False

        if self._microphone:
            self._microphone.stop()
            self._microphone = None

        if self._file_feeder:
            self._file_feeder.stop()
            self._file_feeder = None

        if self._transcription_worker:
            self._transcription_worker.stop()
            self._transcription_worker = None

        if self._analysis_worker:
            self._analysis_worker.stop()
            self._analysis_worker = None

        if self._feedback_worker:
            self._feedback_worker.stop()
            self._feedback_worker = None

        self._queue_manager.clear_all()
        self._logger.info("TalkCraft engine stopped")
