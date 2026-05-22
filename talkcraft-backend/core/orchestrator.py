import cv2
import numpy as np
import threading
import time
import logging
from core.pipeline import PipelineQueue, PipelineStage, ProcessingPipeline
from core.webcam import WebcamCapture
from analyzers.face_analyzer import FaceAnalyzer
from analyzers.hand_analyzer import HandGestureAnalyzer
from engines.confidence_engine import ConfidenceEngine
from engines.feedback_engine import FeedbackEngine

logger = logging.getLogger(__name__)


class MultimodalOrchestrator:
    def __init__(self, webcam_device: int = 0, target_fps: int = 12):
        self.webcam = WebcamCapture(device_index=webcam_device, target_fps=target_fps)
        self.face_analyzer = FaceAnalyzer()
        self.hand_analyzer = HandGestureAnalyzer()
        self.confidence_engine = ConfidenceEngine()
        self.feedback_engine = FeedbackEngine()

        self.pipeline = ProcessingPipeline()

        self._vision_queue = PipelineQueue(maxsize=15)
        self._fusion_queue = PipelineQueue(maxsize=10)
        self._output_queue = PipelineQueue(maxsize=10)

        self._latest_result = {}
        self._result_lock = threading.Lock()
        self._running = False
        self._session_start_time = None
        self._frame_count = 0

        self._setup_pipeline()

    def _setup_pipeline(self):
        webcam_stage = PipelineStage(
            name='webcam',
            process_fn=lambda x: x,
            input_queue=self.webcam.output_queue,
            output_queue=self._vision_queue
        )

        vision_stage = PipelineStage(
            name='vision',
            process_fn=self._process_vision,
            input_queue=self._vision_queue,
            output_queue=self._fusion_queue
        )

        fusion_stage = PipelineStage(
            name='fusion',
            process_fn=self._process_fusion,
            input_queue=self._fusion_queue,
            output_queue=self._output_queue
        )

        self.pipeline.add_stage(webcam_stage)
        self.pipeline.add_stage(vision_stage)
        self.pipeline.add_stage(fusion_stage)

    def _process_vision(self, frame_data: tuple) -> dict:
        timestamp, frame = frame_data
        face_results = self.face_analyzer.analyze(frame)
        hand_results = self.hand_analyzer.analyze(frame)

        return {
            'timestamp': timestamp,
            'frame': frame,
            'face': face_results,
            'hands': hand_results
        }

    def _process_fusion(self, vision_data: dict) -> dict:
        combined = {
            'face_detected': vision_data['face']['face_detected'],
            'eye_contact_score': vision_data['face']['eye_contact_score'],
            'gaze_direction': vision_data['face']['gaze_direction'],
            'head_pitch': vision_data['face']['head_pitch'],
            'head_yaw': vision_data['face']['head_yaw'],
            'head_roll': vision_data['face']['head_roll'],
            'posture_stability': vision_data['face']['posture_stability'],
            'hands_detected': vision_data['hands']['hands_detected'],
            'hand_activity': vision_data['hands']['hand_activity'],
            'gestures': vision_data['hands']['gestures']
        }

        confidence = self.confidence_engine.calculate(combined)
        combined.update(confidence)

        feedback = self.feedback_engine.generate_feedback(combined)
        combined['feedback'] = feedback

        annotated_frame = self._create_overlay(
            vision_data['frame'],
            vision_data['face']['annotated_frame'],
            vision_data['hands']['annotated_frame'],
            combined
        )
        combined['annotated_frame'] = annotated_frame
        combined['raw_frame'] = vision_data['frame']

        session_duration = 0
        if self._session_start_time:
            session_duration = time.time() - self._session_start_time
        combined['session_duration'] = session_duration

        with self._result_lock:
            self._latest_result = combined.copy()

        self._frame_count += 1

        return combined

    def _create_overlay(self, raw_frame, face_frame, hand_frame, data: dict) -> np.ndarray:
        overlay = face_frame.copy()

        h, w, _ = overlay.shape

        panel_h = 120
        panel = np.zeros((panel_h, w, 3), dtype=np.uint8)
        panel[:] = (30, 30, 30)

        confidence_score = data.get('confidence_score', 0.5)
        confidence_level = data.get('confidence_level', 'moderate')

        if confidence_score >= 0.7:
            conf_color = (0, 255, 0)
        elif confidence_score >= 0.4:
            conf_color = (0, 165, 255)
        else:
            conf_color = (0, 0, 255)

        cv2.putText(panel, f"Confidence: {confidence_score:.0%} ({confidence_level})",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, conf_color, 2)

        cv2.putText(panel, f"Eye: {data.get('eye_contact_score', 0):.0%} | Posture: {data.get('posture_stability', 0):.0%}",
                    (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.putText(panel, f"Hands: {data.get('hands_detected', 0)} | Activity: {data.get('hand_activity', 0):.0%}",
                    (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.putText(panel, f"Pitch: {data.get('head_pitch', 0):.1f} | Yaw: {data.get('head_yaw', 0):.1f} | Roll: {data.get('head_roll', 0):.1f}",
                    (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        fps_text = f"FPS: {self.webcam.fps:.1f}"
        cv2.putText(panel, fps_text, (w - 100, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        duration = data.get('session_duration', 0)
        mins, secs = int(duration) // 60, int(duration) % 60
        cv2.putText(panel, f"Time: {mins:02d}:{secs:02d}", (w - 100, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        combined = np.vstack([overlay, panel])

        feedback = data.get('feedback', [])
        if feedback:
            latest_feedback = feedback[0]['message']
            fb_height = 30
            fb_panel = np.zeros((fb_height, w, 3), dtype=np.uint8)
            fb_panel[:] = (20, 20, 40)
            cv2.putText(fb_panel, f"> {latest_feedback}", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 100), 1)
            combined = np.vstack([combined, fb_panel])

        return combined

    def start(self):
        self._running = True
        self._session_start_time = time.time()
        self.webcam.start()
        self.pipeline.start()
        logger.info("Multimodal orchestrator started")

    def stop(self):
        self._running = False
        self.pipeline.stop()
        self.webcam.stop()
        self.face_analyzer.release()
        self.hand_analyzer.release()
        logger.info("Multimodal orchestrator stopped")

    def get_latest_result(self) -> dict:
        with self._result_lock:
            return self._latest_result.copy()

    def get_output(self) -> dict:
        return self._output_queue.get(block=False, timeout=0.01)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def frame_count(self) -> int:
        return self._frame_count

    def update_speech_data(self, speech_data: dict):
        with self._result_lock:
            if self._latest_result:
                self.confidence_engine.calculate(self._latest_result, speech_data)
