import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import math
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class FaceAnalyzer:
    def __init__(self):
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'face_landmarker.task')
        if not os.path.exists(model_path):
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            import urllib.request
            url = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'
            logger.info(f"Downloading face landmarker model to {model_path}")
            urllib.request.urlretrieve(url, model_path)

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.landmarker = vision.FaceLandmarker.create_from_options(options)

        self._eye_contact_history = []
        self._history_size = 30
        self._head_pose_history = []
        self._posture_stability_window = 15

    def analyze(self, frame: np.ndarray) -> dict:
        results = {
            'face_detected': False,
            'eye_contact_score': 0.0,
            'gaze_direction': 'center',
            'head_pitch': 0.0,
            'head_yaw': 0.0,
            'head_roll': 0.0,
            'posture_stability': 0.0,
            'face_bbox': None,
            'annotated_frame': frame.copy()
        }

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        detection_result = self.landmarker.detect(mp_image)

        if not detection_result.face_landmarks:
            return results

        results['face_detected'] = True
        landmarks = detection_result.face_landmarks[0]
        h, w, _ = frame.shape

        eye_contact = self._calculate_eye_contact(landmarks, w, h)
        results['eye_contact_score'] = eye_contact['score']
        results['gaze_direction'] = eye_contact['direction']

        head_pose = self._calculate_head_pose(landmarks, w, h)
        results['head_pitch'] = head_pose['pitch']
        results['head_yaw'] = head_pose['yaw']
        results['head_roll'] = head_pose['roll']

        results['posture_stability'] = self._calculate_posture_stability(head_pose)

        results['face_bbox'] = self._get_face_bbox(landmarks, w, h)

        annotated = self._draw_annotations(frame.copy(), landmarks, w, h, results)
        results['annotated_frame'] = annotated

        return results

    def _calculate_eye_contact(self, landmarks, img_w: int, img_h: int) -> dict:
        left_eye_inner = landmarks[33]
        left_eye_outer = landmarks[133]
        left_eye_center = ((left_eye_inner.x + left_eye_outer.x) / 2,
                          (left_eye_inner.y + left_eye_outer.y) / 2)

        right_eye_inner = landmarks[362]
        right_eye_outer = landmarks[263]
        right_eye_center = ((right_eye_inner.x + right_eye_outer.x) / 2,
                           (right_eye_inner.y + right_eye_outer.y) / 2)

        nose_tip = landmarks[1]
        face_center_x = (left_eye_center[0] + right_eye_center[0]) / 2
        face_center_y = (left_eye_center[1] + right_eye_center[1]) / 2

        gaze_offset_x = nose_tip.x - face_center_x
        gaze_offset_y = nose_tip.y - face_center_y

        eye_contact_score = max(0.0, 1.0 - (abs(gaze_offset_x) * 3.0 + abs(gaze_offset_y) * 2.0))
        eye_contact_score = min(1.0, eye_contact_score)

        if abs(gaze_offset_x) < 0.03 and abs(gaze_offset_y) < 0.03:
            direction = 'center'
        elif gaze_offset_x < -0.03:
            direction = 'left'
        elif gaze_offset_x > 0.03:
            direction = 'right'
        elif gaze_offset_y < -0.02:
            direction = 'up'
        else:
            direction = 'down'

        self._eye_contact_history.append(eye_contact_score)
        if len(self._eye_contact_history) > self._history_size:
            self._eye_contact_history.pop(0)

        smoothed_score = sum(self._eye_contact_history) / len(self._eye_contact_history)

        return {'score': smoothed_score, 'direction': direction}

    def _calculate_head_pose(self, landmarks, img_w: int, img_h: int) -> dict:
        nose = landmarks[1]
        chin = landmarks[152]
        left_temple = landmarks[234]
        right_temple = landmarks[454]
        left_eye_inner = landmarks[133]
        right_eye_inner = landmarks[362]

        face_height = math.sqrt((chin.y - nose.y) ** 2 + (chin.x - nose.x) ** 2)
        face_width = math.sqrt((right_temple.x - left_temple.x) ** 2 + (right_temple.y - left_temple.y) ** 2)

        pitch = math.atan2(chin.y - nose.y, face_height) * 180 / math.pi
        yaw = math.atan2(nose.x - (left_temple.x + right_temple.x) / 2, face_width) * 180 / math.pi

        eye_line_angle = math.atan2(right_eye_inner.y - left_eye_inner.y,
                                    right_eye_inner.x - left_eye_inner.x)
        roll = eye_line_angle * 180 / math.pi

        self._head_pose_history.append({'pitch': pitch, 'yaw': yaw, 'roll': roll})
        if len(self._head_pose_history) > self._posture_stability_window:
            self._head_pose_history.pop(0)

        return {'pitch': pitch, 'yaw': yaw, 'roll': roll}

    def _calculate_posture_stability(self, current_pose: dict) -> float:
        if len(self._head_pose_history) < 5:
            return 1.0

        recent = self._head_pose_history[-self._posture_stability_window:]
        pitch_values = [p['pitch'] for p in recent]
        yaw_values = [p['yaw'] for p in recent]
        roll_values = [p['roll'] for p in recent]

        pitch_var = np.var(pitch_values)
        yaw_var = np.var(yaw_values)
        roll_var = np.var(roll_values)

        total_var = pitch_var + yaw_var + roll_var
        stability = max(0.0, 1.0 - (total_var / 50.0))

        return stability

    def _get_face_bbox(self, landmarks, img_w: int, img_h: int) -> tuple:
        x_coords = [p.x for p in landmarks]
        y_coords = [p.y for p in landmarks]
        min_x, max_x = int(min(x_coords) * img_w), int(max(x_coords) * img_w)
        min_y, max_y = int(min(y_coords) * img_h), int(max(y_coords) * img_h)
        return (min_x, min_y, max_x, max_y)

    def _draw_annotations(self, frame, landmarks, img_w: int, img_h: int, results: dict) -> np.ndarray:
        for landmark in landmarks:
            x, y = int(landmark.x * img_w), int(landmark.y * img_h)
            cv2.circle(frame, (x, y), 1, (30, 30, 30), -1)

        nose = landmarks[1]
        nose_x, nose_y = int(nose.x * img_w), int(nose.y * img_h)
        cv2.circle(frame, (nose_x, nose_y), 3, (0, 0, 255), -1)

        eye_color = (0, 255, 0) if results['eye_contact_score'] > 0.6 else (0, 165, 255) if results['eye_contact_score'] > 0.3 else (0, 0, 255)
        cv2.putText(frame, f"Eye: {results['eye_contact_score']:.0%}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, eye_color, 2)

        posture_color = (0, 255, 0) if results['posture_stability'] > 0.7 else (0, 0, 255)
        cv2.putText(frame, f"Posture: {results['posture_stability']:.0%}", (10, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, posture_color, 2)

        cv2.putText(frame, f"Gaze: {results['gaze_direction']}", (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return frame

    def release(self):
        self.landmarker.close()
