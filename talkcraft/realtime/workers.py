import time
from queue import Empty
from typing import Optional, Dict, Any
from threading import Thread, Event

from talkcraft.utils.logger import get_logger
from talkcraft.realtime.queues import MonitoredQueue


class AnalysisWorker:
    def __init__(
        self,
        transcription_queue: MonitoredQueue,
        analysis_queue: MonitoredQueue,
        grammar_checker=None,
        filler_detector=None,
        speaking_pace=None,
        speech_patterns=None,
    ):
        self._transcription_queue = transcription_queue
        self._analysis_queue = analysis_queue
        self._grammar_checker = grammar_checker
        self._filler_detector = filler_detector
        self._speaking_pace = speaking_pace
        self._speech_patterns = speech_patterns
        self._thread: Optional[Thread] = None
        self._stop_event = Event()
        self._logger = get_logger("talkcraft.realtime.analysis_worker")

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = Thread(target=self._run, name="AnalysisWorker", daemon=True)
        self._thread.start()
        self._logger.info("Analysis worker started")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)
        self._logger.info("Analysis worker stopped")

    def _run(self):
        while not self._stop_event.is_set():
            try:
                transcription = self._transcription_queue.get(timeout=0.3)
            except Empty:
                continue

            try:
                text = transcription.get("text", "")
                timestamp = transcription.get("timestamp", time.time())
                duration = transcription.get("duration", 0)

                grammar_result = None
                filler_result = None
                pace_result = None
                speech_patterns_result = None

                if self._grammar_checker and text:
                    grammar_result = self._grammar_checker.check(text)

                if self._filler_detector and text:
                    filler_result = self._filler_detector.detect(text)

                if self._speaking_pace and text:
                    pace_result = self._speaking_pace.analyze(
                        text, timestamp, duration
                    )

                pace_wpm = (pace_result.get("current_wpm", 0)
                            if pace_result else 0)

                if self._speech_patterns and text:
                    speech_patterns_result = self._speech_patterns.analyze(
                        text, timestamp, duration, pace_wpm
                    )

                analysis_result = {
                    "timestamp": timestamp,
                    "text": text,
                    "grammar": grammar_result,
                    "filler": filler_result,
                    "pace": pace_result,
                    "speech_patterns": speech_patterns_result,
                    "word_count": len(text.split()) if text else 0,
                    "processing_time": time.time(),
                }

                self._analysis_queue.put_nowait(analysis_result)

            except Exception as e:
                self._logger.error(f"Analysis error: {e}")
            finally:
                self._transcription_queue.task_done()


class FeedbackWorker:
    def __init__(
        self,
        analysis_queue: MonitoredQueue,
        feedback_queue: MonitoredQueue,
        feedback_engine=None,
    ):
        self._analysis_queue = analysis_queue
        self._feedback_queue = feedback_queue
        self._feedback_engine = feedback_engine
        self._thread: Optional[Thread] = None
        self._stop_event = Event()
        self._logger = get_logger("talkcraft.realtime.feedback_worker")

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = Thread(target=self._run, name="FeedbackWorker", daemon=True)
        self._thread.start()
        self._logger.info("Feedback worker started")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)
        self._logger.info("Feedback worker stopped")

    def _run(self):
        while not self._stop_event.is_set():
            try:
                analysis = self._analysis_queue.get(timeout=0.3)
            except Empty:
                continue

            try:
                if self._feedback_engine:
                    feedback = self._feedback_engine.generate(analysis)
                    if feedback:
                        feedback["timestamp"] = time.time()
                        feedback["analysis"] = analysis
                        self._feedback_queue.put_nowait(feedback)
            except Exception as e:
                self._logger.error(f"Feedback generation error: {e}")
            finally:
                self._analysis_queue.task_done()
