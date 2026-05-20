import sys
import os
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List

import streamlit as st

_ex_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _ex_project_root not in sys.path:
    sys.path.insert(0, _ex_project_root)

from talkcraft.utils.config import config
from talkcraft.utils.logger import get_logger
from talkcraft.realtime.event_manager import event_manager, EventType


logger = get_logger("talkcraft.ui")


class SharedState:
    def __init__(self):
        self._lock = threading.Lock()
        self.transcription_text = ""
        self.transcription_history: List[str] = []
        self.current_wpm = 0.0
        self.average_wpm = 0.0
        self.pace_status = "normal"
        self.filler_count = 0
        self.filler_rate = 0.0
        self.grammar_errors = 0
        self.feedback_messages: List[Dict[str, Any]] = []
        self.is_recording = False
        self.session_duration = 0.0
        self.total_words = 0
        self.input_mode = "mic"
        self.file_progress = 0.0
        self.status_message = "Ready"

    def update_transcription(self, text: str):
        with self._lock:
            self.transcription_text = text
            self.transcription_history.append(text)
            if len(self.transcription_history) > config.ui.max_transcription_history:
                self.transcription_history.pop(0)

    def update_metrics(self, analysis: Dict[str, Any]):
        with self._lock:
            if analysis.get("pace"):
                self.current_wpm = analysis["pace"].get("current_wpm", 0)
                self.average_wpm = analysis["pace"].get("average_wpm", 0)
                self.pace_status = analysis["pace"].get("status", "normal")
                self.total_words = analysis["pace"].get("total_words", 0)

            if analysis.get("filler"):
                self.filler_count = analysis["filler"].get("total_fillers", 0)
                self.filler_rate = analysis["filler"].get("filler_rate", 0)

            if analysis.get("grammar"):
                self.grammar_errors = analysis["grammar"].get("error_count", 0)

    def update_feedback(self, feedback: Dict[str, Any]):
        with self._lock:
            messages = feedback.get("messages", [])
            for msg in messages:
                self.feedback_messages.append(msg)
            if len(self.feedback_messages) > 20:
                self.feedback_messages = self.feedback_messages[-20:]

    def get_state(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "transcription_text": self.transcription_text,
                "transcription_history": list(self.transcription_history),
                "current_wpm": self.current_wpm,
                "average_wpm": self.average_wpm,
                "pace_status": self.pace_status,
                "filler_count": self.filler_count,
                "filler_rate": self.filler_rate,
                "grammar_errors": self.grammar_errors,
                "feedback_messages": list(self.feedback_messages),
                "is_recording": self.is_recording,
                "session_duration": self.session_duration,
                "total_words": self.total_words,
                "input_mode": self.input_mode,
                "file_progress": self.file_progress,
                "status_message": self.status_message,
            }


shared_state = SharedState()


@st.cache_resource
def get_engine():
    from talkcraft.engine import TalkCraftEngine
    return TalkCraftEngine()


def render_sidebar():
    with st.sidebar:
        st.markdown("## TalkCraft")
        st.markdown("---")
        st.markdown("### Input Mode")

        mode = st.radio(
            "Select input source",
            options=["Microphone", "Audio File"],
            index=0,
            key="input_mode_radio",
            help="Choose between live microphone or uploaded audio file",
        )

        st.markdown("---")
        engine = get_engine()

        if mode == "Microphone":
            if st.button("Start Microphone", type="primary", use_container_width=True):
                engine.start_mic()

            if st.button("Stop", type="secondary", use_container_width=True):
                engine.stop()

            st.markdown("---")
            st.markdown("### Audio Settings")
            st.caption(f"Sample Rate: {config.audio.sample_rate} Hz")
            st.caption(f"Chunk Size: {config.audio.chunk_duration}s")
            st.caption(f"Model: {config.transcription.model_size}")

        else:
            uploaded_file = st.file_uploader(
                "Upload an audio file",
                type=["wav", "mp3", "flac", "ogg", "m4a"],
                help="Supported: WAV, MP3, FLAC, OGG, M4A",
            )

            if uploaded_file is not None:
                file_details = {
                    "Filename": uploaded_file.name,
                    "File size": f"{uploaded_file.size / 1024:.1f} KB",
                    "Type": uploaded_file.type,
                }
                st.json(file_details)

                temp_dir = Path(_ex_project_root) / ".talkcraft_temp"
                temp_dir.mkdir(exist_ok=True)
                temp_path = temp_dir / uploaded_file.name

                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Process File", type="primary", use_container_width=True):
                        success = engine.start_file(str(temp_path))
                        if not success:
                            st.error("Failed to load audio file. Check format compatibility.")
                with col2:
                    if st.button("Stop", type="secondary", use_container_width=True):
                        engine.stop()

                st.markdown("---")
                st.caption(
                    "File processing runs in real-time simulation. "
                    "Larger files take proportionally longer."
                )

        st.markdown("---")
        st.caption("TalkCraft v1.0 — Phase 1")
        st.caption("CPU-only inference")


def render_dashboard():
    st.set_page_config(
        page_title="TalkCraft - Real-Time Communication Coach",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if "first_render" not in st.session_state:
        st.session_state.first_render = True

    render_sidebar()

    engine = get_engine()
    engine.poll_updates()

    state = shared_state.get_state()

    st.markdown("""
    <style>
    .main-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: #1e1e1e;
        border-radius: 8px;
        padding: 16px;
        margin: 4px 0;
        border: 1px solid #333;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #4CAF50;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #888;
        text-transform: uppercase;
    }
    .transcript-box {
        background: #1e1e1e;
        border-radius: 8px;
        padding: 16px;
        min-height: 120px;
        border: 1px solid #333;
        font-size: 1.1rem;
        line-height: 1.6;
    }
    .feedback-item {
        background: #2d2d2d;
        border-left: 3px solid #FF9800;
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 0 4px 4px 0;
        font-size: 0.9rem;
    }
    .status-recording {
        color: #f44336;
        font-weight: 600;
    }
    .status-idle {
        color: #888;
    }
    .status-file {
        color: #2196F3;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title">TalkCraft — Real-Time Communication Coach</div>',
                unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    pace_color = "#4CAF50"
    if state["pace_status"] == "too_fast":
        pace_color = "#f44336"
    elif state["pace_status"] == "too_slow":
        pace_color = "#FF9800"

    with col1:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">Speaking Pace</div>'
            f'<div class="metric-value" style="color:{pace_color};">'
            f'{state["current_wpm"]:.0f}</div>'
            f'<div style="font-size:0.8rem;">WPM (avg: {state["average_wpm"]:.0f})</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">Filler Words</div>'
            f'<div class="metric-value" style="color:{"#f44336" if state["filler_rate"] > 10 else "#4CAF50"};">'
            f'{state["filler_count"]}</div>'
            f'<div style="font-size:0.8rem;">Rate: {state["filler_rate"]:.1f}%</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">Grammar Issues</div>'
            f'<div class="metric-value" style="color:{"#f44336" if state["grammar_errors"] > 0 else "#4CAF50"};">'
            f'{state["grammar_errors"]}</div>'
            f'<div style="font-size:0.8rem;">detected</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">Session</div>'
            f'<div class="metric-value">{state["total_words"]}</div>'
            f'<div style="font-size:0.8rem;">words spoken</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    trans_col, feedback_col = st.columns([2, 1])

    with trans_col:
        st.markdown("### Live Transcription")
        placeholder = (
            "Waiting for speech..." if not state["is_recording"]
            else "Listening..." if state["input_mode"] == "mic"
            else "Processing file..."
        )
        st.markdown(
            f'<div class="transcript-box">'
            f'{state["transcription_text"] if state["transcription_text"] else placeholder}'
            f'</div>',
            unsafe_allow_html=True,
        )

        with st.expander("Recent Transcription History"):
            history = state["transcription_history"][-10:]
            if history:
                for t in reversed(history):
                    st.text(t)
            else:
                st.caption("No transcription history yet")

    with feedback_col:
        st.markdown("### Real-Time Feedback")
        if state["feedback_messages"]:
            for msg in reversed(state["feedback_messages"][-5:]):
                message = msg.get("message", "")
                st.markdown(
                    f'<div class="feedback-item">{message}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div style="color:#666;font-style:italic;">'
                "Feedback will appear here during your session"
                "</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    status_text = "Recording" if state["is_recording"] else "Idle"
    status_class = "status-recording" if state["is_recording"] else "status-idle"
    if state["input_mode"] == "file" and state["is_recording"]:
        status_text = "Processing file"
        status_class = "status-file"

    st.markdown(
        f'<div style="text-align:center;">'
        f'Status: <span class="{status_class}">{status_text}</span>'
        f' | Mode: {"Microphone" if state["input_mode"] == "mic" else "File"}'
        f' | Duration: {state["session_duration"]:.0f}s'
        f'</div>',
        unsafe_allow_html=True,
    )

    time.sleep(config.ui.refresh_interval_ms / 1000.0)
    st.rerun()


if __name__ == "__main__":
    render_dashboard()
