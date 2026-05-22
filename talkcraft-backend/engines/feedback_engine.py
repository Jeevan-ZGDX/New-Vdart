import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FeedbackEngine:
    def __init__(self):
        self._feedback_history = []
        self._max_history = 20
        self._cooldown_seconds = 5
        self._last_feedback_time = {}
        self._feedback_rules = self._init_rules()

    def _init_rules(self) -> list:
        return [
            {
                'id': 'eye_contact_low',
                'condition': lambda d: d.get('eye_contact_score', 1) < 0.3,
                'message': 'Look more at the camera for better eye contact',
                'priority': 2,
                'cooldown': 8
            },
            {
                'id': 'eye_contact_good',
                'condition': lambda d: d.get('eye_contact_score', 0) > 0.8,
                'message': 'Great eye contact! Keep it up',
                'priority': 1,
                'cooldown': 15
            },
            {
                'id': 'posture_unstable',
                'condition': lambda d: d.get('posture_stability', 1) < 0.4,
                'message': 'Try to keep your head steady and maintain good posture',
                'priority': 2,
                'cooldown': 10
            },
            {
                'id': 'head_tilt',
                'condition': lambda d: abs(d.get('head_pitch', 0)) > 15,
                'message': 'Avoid tilting your head too much',
                'priority': 2,
                'cooldown': 8
            },
            {
                'id': 'gaze_averted',
                'condition': lambda d: d.get('gaze_direction', 'center') not in ['center'],
                'message_func': lambda d: f"Your gaze is directed {d.get('gaze_direction', 'away')}, try looking forward",
                'priority': 1,
                'cooldown': 6
            },
            {
                'id': 'pace_too_fast',
                'condition': lambda d: d.get('current_wpm', 120) > 160,
                'message': 'Slow down your speaking pace',
                'priority': 2,
                'cooldown': 10
            },
            {
                'id': 'pace_too_slow',
                'condition': lambda d: d.get('current_wpm', 120) < 90,
                'message': 'Try to speak a bit faster',
                'priority': 2,
                'cooldown': 10
            },
            {
                'id': 'filler_words',
                'condition': lambda d: d.get('filler_rate', 0) > 0.08,
                'message': 'Reduce filler words - pause instead of saying um/uh',
                'priority': 2,
                'cooldown': 12
            },
            {
                'id': 'hand_overactive',
                'condition': lambda d: d.get('hand_activity', 0.5) > 0.7,
                'message': 'Reduce excessive hand movements',
                'priority': 1,
                'cooldown': 8
            },
            {
                'id': 'hand_underactive',
                'condition': lambda d: d.get('hands_detected', 0) == 0 and d.get('hand_activity', 1) < 0.1,
                'message': 'Use natural hand gestures to emphasize points',
                'priority': 1,
                'cooldown': 15
            },
            {
                'id': 'confidence_low',
                'condition': lambda d: d.get('confidence_score', 1) < 0.4,
                'message': 'Focus on posture and eye contact to boost confidence',
                'priority': 3,
                'cooldown': 12
            },
            {
                'id': 'confidence_high',
                'condition': lambda d: d.get('confidence_score', 0) > 0.8,
                'message': 'Excellent communication presence!',
                'priority': 1,
                'cooldown': 20
            }
        ]

    def generate_feedback(self, combined_data: dict) -> list:
        feedback_items = []
        current_time = datetime.now().timestamp()

        sorted_rules = sorted(self._feedback_rules, key=lambda r: r['priority'])

        for rule in sorted_rules:
            try:
                if rule['condition'](combined_data):
                    rule_id = rule['id']
                    last_time = self._last_feedback_time.get(rule_id, 0)

                    if current_time - last_time >= rule['cooldown']:
                        message = rule.get('message_func', lambda d: rule['message'])(combined_data)
                        feedback_items.append({
                            'message': message,
                            'priority': rule['priority'],
                            'rule_id': rule_id,
                            'timestamp': current_time
                        })
                        self._last_feedback_time[rule_id] = current_time
            except Exception as e:
                logger.error(f"Error evaluating feedback rule {rule['id']}: {e}")

        feedback_items.sort(key=lambda x: x['priority'])

        for item in feedback_items:
            self._feedback_history.append(item)
            if len(self._feedback_history) > self._max_history:
                self._feedback_history.pop(0)

        return feedback_items

    def get_history(self, limit: int = 10) -> list:
        return self._feedback_history[-limit:]

    def clear_history(self):
        self._feedback_history.clear()
        self._last_feedback_time.clear()

    @property
    def feedback_count(self) -> int:
        return len(self._feedback_history)
