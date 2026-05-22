import streamlit as st
import cv2
import numpy as np
import time
import logging
from core.orchestrator import MultimodalOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="TalkCraft - Communication Coach", layout="wide")

st.title("TalkCraft - Real-Time Communication Coach")
st.markdown("Phase 2: Multimodal Communication Analysis")


@st.cache_resource
def init_orchestrator():
    orchestrator = MultimodalOrchestrator(webcam_device=0, target_fps=12)
    return orchestrator


if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = None
if 'running' not in st.session_state:
    st.session_state.running = False
if 'metrics_history' not in st.session_state:
    st.session_state.metrics_history = {
        'eye_contact': [],
        'posture': [],
        'confidence': [],
        'hand_activity': []
    }


col1, col2, col3 = st.columns([3, 1, 1])

with col3:
    if st.button("Start Session", type="primary", disabled=st.session_state.running):
        try:
            orchestrator = init_orchestrator()
            orchestrator.start()
            st.session_state.orchestrator = orchestrator
            st.session_state.running = True
            st.success("Session started!")
        except Exception as e:
            st.error(f"Failed to start: {e}")

    if st.button("Stop Session", type="secondary", disabled=not st.session_state.running):
        if st.session_state.orchestrator:
            st.session_state.orchestrator.stop()
            st.session_state.orchestrator = None
        st.session_state.running = False
        st.session_state.metrics_history = {
            'eye_contact': [],
            'posture': [],
            'confidence': [],
            'hand_activity': []
        }
        st.info("Session stopped")


placeholder = st.empty()

if st.session_state.running and st.session_state.orchestrator:
    orchestrator = st.session_state.orchestrator

    col_video, col_metrics = st.columns([2, 1])

    with col_video:
        video_placeholder = st.empty()

    with col_metrics:
        st.subheader("Live Metrics")

        eye_contact_metric = st.empty()
        posture_metric = st.empty()
        confidence_metric = st.empty()
        hand_metric = st.empty()
        gaze_metric = st.empty()
        head_pose_metric = st.empty()

        st.subheader("Feedback")
        feedback_container = st.empty()

        st.subheader("Session Stats")
        stats_container = st.empty()

    max_iterations = 500
    iteration = 0

    while st.session_state.running and iteration < max_iterations:
        try:
            result = orchestrator.get_latest_result()

            if result and result.get('face_detected', False):
                annotated_frame = result.get('annotated_frame')

                if annotated_frame is not None:
                    frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                    video_placeholder.image(frame_rgb, use_container_width=True)

                eye_score = result.get('eye_contact_score', 0)
                posture_score = result.get('posture_stability', 0)
                confidence_score = result.get('confidence_score', 0)
                hand_activity = result.get('hand_activity', 0)

                st.session_state.metrics_history['eye_contact'].append(eye_score)
                st.session_state.metrics_history['posture'].append(posture_score)
                st.session_state.metrics_history['confidence'].append(confidence_score)
                st.session_state.metrics_history['hand_activity'].append(hand_activity)

                history_len = 50
                for key in st.session_state.metrics_history:
                    if len(st.session_state.metrics_history[key]) > history_len:
                        st.session_state.metrics_history[key] = st.session_state.metrics_history[key][-history_len:]

                eye_contact_metric.metric("Eye Contact", f"{eye_score:.0%}", delta=None)
                posture_metric.metric("Posture Stability", f"{posture_score:.0%}", delta=None)
                confidence_metric.metric("Confidence", f"{confidence_score:.0%}", delta=result.get('confidence_level', ''))
                hand_metric.metric("Hand Activity", f"{hand_activity:.0%}", delta=None)

                gaze_metric.text(f"**Gaze:** {result.get('gaze_direction', 'unknown').title()}")

                pitch = result.get('head_pitch', 0)
                yaw = result.get('head_yaw', 0)
                roll = result.get('head_roll', 0)
                head_pose_metric.text(f"**Head Pose:** P:{pitch:.1f}° Y:{yaw:.1f}° R:{roll:.1f}°")

                feedback = result.get('feedback', [])
                if feedback:
                    feedback_text = "\n\n".join([f"- {f['message']}" for f in feedback[:3]])
                    feedback_container.info(feedback_text)
                else:
                    feedback_container.text("No feedback at this moment")

                duration = result.get('session_duration', 0)
                mins, secs = int(duration) // 60, int(duration) % 60
                frames = orchestrator.frame_count
                fps = orchestrator.webcam.fps

                stats_container.text(f"Duration: {mins:02d}:{secs:02d}\nFrames: {frames}\nFPS: {fps:.1f}")

            else:
                video_placeholder.warning("No face detected. Please position yourself in front of the camera.")

            time.sleep(0.08)
            iteration += 1

        except Exception as e:
            logger.error(f"Error in dashboard loop: {e}")
            time.sleep(0.1)
            iteration += 1

else:
    st.info("Click 'Start Session' to begin real-time communication analysis.")

    st.markdown("""
    ### Features:
    - **Eye Contact Tracking**: Real-time gaze direction and eye contact percentage
    - **Head Posture Analysis**: Pitch, yaw, roll tracking with stability scoring
    - **Hand Gesture Detection**: Activity level and basic gesture classification
    - **Confidence Scoring**: Multimodal confidence based on all inputs
    - **Live Feedback**: Actionable suggestions to improve communication

    ### Tips:
    - Position yourself so your face is clearly visible
    - Look at the camera for better eye contact scores
    - Keep your head relatively steady
    - Use natural hand gestures
    """)
