import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ConfidenceEngine:
    def __init__(self):
        self._weights = {
            'eye_contact': 0.30,
            'posture_stability': 0.25,
            'speech_pace': 0.20,
            'filler_rate': 0.15,
            'hand_gesture': 0.10
        }

        self._score_history = []
        self._history_size = 50
        self._smoothed_score = 0.5

        self._component_scores = {
            'eye_contact': 0.5,
            'posture_stability': 0.5,
            'speech_pace': 0.5,
            'filler_rate': 0.5,
            'hand_gesture': 0.5
        }

    def calculate(self, vision_data: dict, speech_data: Optional[dict] = None) -> dict:
        eye_score = vision_data.get('eye_contact_score', 0.5)
        posture_score = vision_data.get('posture_stability', 0.5)
        face_detected = vision_data.get('face_detected', False)

        if not face_detected:
            eye_score = 0.0
            posture_score = 0.0

        self._component_scores['eye_contact'] = eye_score
        self._component_scores['posture_stability'] = posture_score

        if speech_data:
            wpm = speech_data.get('current_wpm', 120)
            filler_rate = speech_data.get('filler_rate', 0.0)

            if 100 <= wpm <= 150:
                pace_score = 1.0
            elif 80 <= wpm < 100 or 150 < wpm <= 170:
                pace_score = 0.7
            elif 60 <= wpm < 80 or 170 < wpm <= 200:
                pace_score = 0.4
            else:
                pace_score = 0.2

            self._component_scores['speech_pace'] = pace_score

            if filler_rate < 0.03:
                filler_score = 1.0
            elif filler_rate < 0.07:
                filler_score = 0.7
            elif filler_rate < 0.12:
                filler_score = 0.4
            else:
                filler_score = 0.2

            self._component_scores['filler_rate'] = filler_score

        hand_activity = vision_data.get('hand_activity', 0.5)
        if 0.2 <= hand_activity <= 0.6:
            gesture_score = 1.0
        elif hand_activity < 0.1:
            gesture_score = 0.5
        else:
            gesture_score = 0.6

        self._component_scores['hand_gesture'] = gesture_score

        raw_score = sum(
            self._component_scores[key] * self._weights[key]
            for key in self._weights
        )

        self._score_history.append(raw_score)
        if len(self._score_history) > self._history_size:
            self._score_history.pop(0)

        self._smoothed_score = sum(self._score_history) / len(self._score_history)

        confidence_level = self._get_confidence_level(self._smoothed_score)

        return {
            'confidence_score': self._smoothed_score,
            'confidence_level': confidence_level,
            'component_scores': self._component_scores.copy(),
            'weights': self._weights.copy()
        }

    def _get_confidence_level(self, score: float) -> str:
        if score >= 0.85:
            return 'excellent'
        elif score >= 0.70:
            return 'good'
        elif score >= 0.50:
            return 'moderate'
        elif score >= 0.30:
            return 'needs_improvement'
        else:
            return 'low'

    def get_component_scores(self) -> dict:
        return self._component_scores.copy()

    def reset(self):
        self._score_history.clear()
        self._smoothed_score = 0.5
        self._component_scores = {key: 0.5 for key in self._component_scores}
