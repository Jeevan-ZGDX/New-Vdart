import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class HandGestureAnalyzer:
    def __init__(self):
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'gesture_recognizer.task')
        if not os.path.exists(model_path):
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            import urllib.request
            url = 'https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task'
            logger.info(f"Downloading gesture recognizer model to {model_path}")
            urllib.request.urlretrieve(url, model_path)

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.GestureRecognizerOptions(
            base_options=base_options,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.recognizer = vision.GestureRecognizer.create_from_options(options)

        self._activity_history = []
        self._history_size = 20
        self._last_hand_positions = {}
        self._gesture_labels = {
            0: 'none',
            1: 'pointing',
            2: 'open_palm',
            3: 'fist',
            4: 'thumbs_up'
        }

    def analyze(self, frame: np.ndarray) -> dict:
        results = {
            'hands_detected': 0,
            'hand_activity': 0.0,
            'gestures': [],
            'hand_positions': [],
            'annotated_frame': frame.copy()
        }

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        detection_result = self.recognizer.recognize(mp_image)

        if not detection_result.hand_landmarks:
            self._activity_history.append(0.0)
            if len(self._activity_history) > self._history_size:
                self._activity_history.pop(0)
            return results

        h, w, _ = frame.shape
        annotated = frame.copy()
        hand_count = len(detection_result.hand_landmarks)
        results['hands_detected'] = hand_count

        total_movement = 0.0
        for idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
            hand_type = detection_result.handedness[idx][0].category_name

            gesture = self._classify_gesture(hand_landmarks)
            results['gestures'].append({
                'hand': hand_type,
                'gesture': gesture,
                'label': self._gesture_labels.get(gesture, 'unknown')
            })

            center = self._get_hand_center(hand_landmarks, w, h)
            results['hand_positions'].append(center)

            movement = self._calculate_hand_movement(idx, center)
            total_movement += movement

            for landmark in hand_landmarks:
                x, y = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(annotated, (x, y), 3, (0, 255, 0), -1)

            gesture_color = (0, 255, 0) if gesture == 2 else (0, 165, 255)
            cv2.putText(annotated, f"{hand_type}: {self._gesture_labels[gesture]}",
                        (int(center[0]) + 10, int(center[1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, gesture_color, 2)

        avg_movement = total_movement / max(hand_count, 1)
        self._activity_history.append(min(1.0, avg_movement / 0.3))
        if len(self._activity_history) > self._history_size:
            self._activity_history.pop(0)

        results['hand_activity'] = sum(self._activity_history) / len(self._activity_history)
        results['annotated_frame'] = annotated

        return results

    def _classify_gesture(self, hand_landmarks) -> int:
        thumb_tip = hand_landmarks[4]
        index_tip = hand_landmarks[8]
        middle_tip = hand_landmarks[12]
        ring_tip = hand_landmarks[16]
        pinky_tip = hand_landmarks[20]
        wrist = hand_landmarks[0]
        index_mcp = hand_landmarks[5]
        middle_mcp = hand_landmarks[9]

        fingers_extended = 0
        if index_tip.y < index_mcp.y:
            fingers_extended += 1
        if middle_tip.y < middle_mcp.y:
            fingers_extended += 1
        if ring_tip.y < hand_landmarks[13].y:
            fingers_extended += 1
        if pinky_tip.y < hand_landmarks[17].y:
            fingers_extended += 1

        thumb_extended = abs(thumb_tip.x - index_tip.x) > 0.05

        if fingers_extended == 0 and not thumb_extended:
            return 3

        if fingers_extended == 1 and thumb_extended:
            if index_tip.y < middle_mcp.y:
                return 1

        if fingers_extended >= 3 and thumb_extended:
            return 2

        if thumb_tip.y < wrist.y and fingers_extended == 0:
            return 4

        return 0

    def _get_hand_center(self, hand_landmarks, img_w: int, img_h: int) -> tuple:
        x_coords = [p.x for p in hand_landmarks]
        y_coords = [p.y for p in hand_landmarks]
        center_x = sum(x_coords) / len(x_coords) * img_w
        center_y = sum(y_coords) / len(y_coords) * img_h
        return (center_x, center_y)

    def _calculate_hand_movement(self, hand_idx: int, current_pos: tuple) -> float:
        if hand_idx not in self._last_hand_positions:
            self._last_hand_positions[hand_idx] = current_pos
            return 0.0

        last_pos = self._last_hand_positions[hand_idx]
        dx = current_pos[0] - last_pos[0]
        dy = current_pos[1] - last_pos[1]
        distance = np.sqrt(dx ** 2 + dy ** 2)

        self._last_hand_positions[hand_idx] = current_pos
        return distance

    def release(self):
        self.recognizer.close()
