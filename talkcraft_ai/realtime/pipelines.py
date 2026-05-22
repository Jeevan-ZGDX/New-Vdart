import threading
import time
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass, field

from talkcraft_ai.utils.config import config
from talkcraft_ai.utils.logger import get_logger
from talkcraft_ai.realtime.queues import QueueManager, MonitoredQueue
from talkcraft_ai.conversation.engine import ConversationEngine
from talkcraft_ai.scoring.conversation_scorer import ConversationScorer
from talkcraft_ai.feedback.live_feedback import LiveFeedbackEngine, FeedbackItem
from talkcraft_ai.audio.tts_engine import TTSEngine

logger = get_logger("pipeline")


@dataclass
class PipelineState:
    running: bool = False
    paused: bool = False
    current_mode: str = "casual_conversation"
    current_topic: str = ""
    error_count: int = 0


class ConversationPipeline:
    """Queue/thread-based conversation pipeline."""

    def __init__(self, engine: ConversationEngine, tts: TTSEngine,
                 scorer: ConversationScorer, feedback: LiveFeedbackEngine):
        self._engine = engine
        self._tts = tts
        self._scorer = scorer
        self._feedback = feedback
        self._queues = QueueManager()
        self._state = PipelineState()
        self._threads: Dict[str, threading.Thread] = {}
        self._on_transcription: Optional[Callable[[str], None]] = None
        self._on_ai_chunk: Optional[Callable[[str], None]] = None
        self._on_ai_response: Optional[Callable[[str], None]] = None
        self._on_feedback: Optional[Callable[[List[FeedbackItem]], None]] = None
        self._on_state_change: Optional[Callable[[PipelineState], None]] = None
        self._on_scores: Optional[Callable[[Dict], None]] = None
        self._lock = threading.Lock()
        logger.info("ConversationPipeline initialized")

    def set_callbacks(
        self,
        on_transcription: Optional[Callable[[str], None]] = None,
        on_ai_chunk: Optional[Callable[[str], None]] = None,
        on_ai_response: Optional[Callable[[str], None]] = None,
        on_feedback: Optional[Callable[[List[FeedbackItem]], None]] = None,
        on_state_change: Optional[Callable[[PipelineState], None]] = None,
        on_scores: Optional[Callable[[Dict], None]] = None,
    ) -> None:
        self._on_transcription = on_transcription
        self._on_ai_chunk = on_ai_chunk
        self._on_ai_response = on_ai_response
        self._on_feedback = on_feedback
        self._on_state_change = on_state_change
        self._on_scores = on_scores

    @property
    def queues(self) -> QueueManager:
        return self._queues

    @property
    def state(self) -> PipelineState:
        return self._state

    def start(self) -> None:
        if self._state.running:
            return
        self._state.running = True
        self._state.error_count = 0
        self._tts.start()
        self._start_thread("transcription", self._transcription_worker)
        self._start_thread("ai_request", self._ai_request_worker)
        self._start_thread("ai_response", self._ai_response_worker)
        self._start_thread("tts", self._tts_worker)
        self._start_thread("feedback", self._feedback_worker)
        logger.info("Pipeline started")
        self._notify_state()

    def stop(self) -> None:
        self._state.running = False
        for name, thread in self._threads.items():
            if thread and thread.is_alive():
                thread.join(timeout=3.0)
        self._tts.stop()
        self._queues.clear_all()
        self._threads.clear()
        logger.info("Pipeline stopped")
        self._notify_state()

    def pause(self) -> None:
        self._state.paused = True
        self._notify_state()

    def resume(self) -> None:
        self._state.paused = False
        self._notify_state()

    def receive_audio(self, audio_chunk: bytes) -> None:
        if not self._state.running or self._state.paused:
            return
        self._queues.audio.put_nowait(audio_chunk)

    def receive_transcription(self, text: str) -> None:
        if not self._state.running or self._state.paused:
            return
        if self._on_transcription:
            self._on_transcription(text)
        self._queues.transcription.put_nowait(text)

    def receive_vision_data(self, vision: Dict) -> None:
        if not self._state.running:
            return
        self._scorer.update_from_vision(vision)

    def _start_thread(self, name: str, target: Callable) -> None:
        thread = threading.Thread(target=target, daemon=True, name=f"pipeline-{name}")
        thread.start()
        self._threads[name] = thread

    def _transcription_worker(self) -> None:
        while self._state.running:
            try:
                text = self._queues.transcription.get(timeout=0.3)
                if text is None or not text.strip():
                    continue
                if self._state.paused:
                    continue
                self._queues.ai_request.put_nowait(text)
            except Exception as e:
                if self._state.running:
                    logger.error(f"Transcription worker error: {e}")
                    self._state.error_count += 1

    def _ai_request_worker(self) -> None:
        while self._state.running:
            try:
                text = self._queues.ai_request.get(timeout=0.3)
                if text is None:
                    continue
                if self._state.paused:
                    self._queues.ai_request.put_nowait(text)
                    time.sleep(0.1)
                    continue
                response = self._engine.process_user_input(
                    text,
                    on_chunk=lambda chunk: self._handle_ai_chunk(chunk),
                )
                if response and response.content:
                    self._queues.ai_response.put_nowait(response.content)
                    self._queues.feedback.put_nowait(response.content)
            except Exception as e:
                if self._state.running:
                    logger.error(f"AI request worker error: {e}")
                    self._state.error_count += 1

    def _ai_response_worker(self) -> None:
        while self._state.running:
            try:
                response = self._queues.ai_response.get(timeout=0.3)
                if response is None:
                    continue
                if self._on_ai_response:
                    self._on_ai_response(response)
                self._queues.tts.put_nowait(response)
            except Exception as e:
                if self._state.running:
                    logger.error(f"AI response worker error: {e}")

    def _tts_worker(self) -> None:
        while self._state.running:
            try:
                text = self._queues.tts.get(timeout=0.3)
                if text is None:
                    continue
                self._tts.speak(text)
            except Exception as e:
                if self._state.running:
                    logger.error(f"TTS worker error: {e}")

    def _feedback_worker(self) -> None:
        while self._state.running:
            try:
                _ = self._queues.feedback.get(timeout=0.5)
                if _ is None:
                    continue
                scores = self._scorer.get_scores_dict()
                feedback_items = self._feedback.evaluate(scores)
                if feedback_items and self._on_feedback:
                    self._on_feedback(feedback_items)
                if self._on_scores:
                    self._on_scores(scores)
            except Exception as e:
                if self._state.running:
                    logger.error(f"Feedback worker error: {e}")

    def _handle_ai_chunk(self, chunk: str) -> None:
        if self._on_ai_chunk:
            self._on_ai_chunk(chunk)

    def _notify_state(self) -> None:
        if self._on_state_change:
            try:
                self._on_state_change(self._state)
            except Exception:
                pass
