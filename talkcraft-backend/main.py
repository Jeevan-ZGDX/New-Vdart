import sys
import os

os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["ABSL_MIN_LOG_LEVEL"] = "2"
os.environ["MEDIAPIPE_DISABLE_GPU"] = "1"

import logging
import threading
import time
import json
import queue

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.orchestrator import MultimodalOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TalkCraftBackend:
    def __init__(self, webcam_device: int = 0, target_fps: int = 12):
        self.orchestrator = MultimodalOrchestrator(
            webcam_device=webcam_device,
            target_fps=target_fps
        )

        self._speech_data = {
            'current_wpm': 120,
            'filler_rate': 0.05,
            'grammar_errors': 0,
            'transcription': ''
        }

        self._running = False
        self._output_queue = queue.Queue(maxsize=50)
        self._monitor_thread = None

    def start(self):
        logger.info("Starting TalkCraft Phase 2 backend...")
        self._running = True
        self.orchestrator.start()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("TalkCraft Phase 2 backend started")

    def stop(self):
        logger.info("Stopping TalkCraft Phase 2 backend...")
        self._running = False
        self.orchestrator.stop()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=3.0)
        logger.info("TalkCraft Phase 2 backend stopped")

    def _monitor_loop(self):
        while self._running:
            try:
                result = self.orchestrator.get_latest_result()
                if result:
                    result['speech'] = self._speech_data.copy()
                    try:
                        self._output_queue.put_nowait(result)
                    except queue.Full:
                        try:
                            self._output_queue.get_nowait()
                            self._output_queue.put_nowait(result)
                        except queue.Full:
                            pass

                time.sleep(0.05)
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(0.1)

    def update_speech_data(self, speech_data: dict):
        self._speech_data.update(speech_data)
        self.orchestrator.update_speech_data(speech_data)

    def get_latest_output(self) -> dict:
        try:
            return self._output_queue.get_nowait()
        except queue.Empty:
            return {}

    def get_status(self) -> dict:
        latest = self.orchestrator.get_latest_result()
        return {
            'running': self._running,
            'webcam_fps': self.orchestrator.webcam.fps,
            'frame_count': self.orchestrator.frame_count,
            'face_detected': latest.get('face_detected', False),
            'confidence_score': latest.get('confidence_score', 0),
            'session_duration': latest.get('session_duration', 0)
        }


def run_dashboard():
    import subprocess
    dashboard_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'app.py')
    subprocess.run([sys.executable, '-m', 'streamlit', 'run', dashboard_path, '--server.port', '8501'])


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='TalkCraft Phase 2 - Multimodal Communication Coach')
    parser.add_argument('--webcam', type=int, default=0, help='Webcam device index')
    parser.add_argument('--fps', type=int, default=12, help='Target processing FPS')
    parser.add_argument('--dashboard', action='store_true', help='Launch Streamlit dashboard')
    args = parser.parse_args()

    if args.dashboard:
        run_dashboard()
    else:
        backend = TalkCraftBackend(webcam_device=args.webcam, target_fps=args.fps)

        try:
            backend.start()
            logger.info("Backend running. Press Ctrl+C to stop.")

            while True:
                status = backend.get_status()
                print(f"\rFPS: {status['webcam_fps']:.1f} | Face: {status['face_detected']} | Confidence: {status['confidence_score']:.0%} | Time: {status['session_duration']:.0f}s", end='', flush=True)
                time.sleep(0.5)

        except KeyboardInterrupt:
            logger.info("\nShutting down...")
        finally:
            backend.stop()
