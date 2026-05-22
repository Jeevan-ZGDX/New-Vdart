import time
import threading
from typing import Dict, List, Optional

import streamlit as st

from talkcraft_ai.utils.config import config
from talkcraft_ai.utils.logger import get_logger
from talkcraft_ai.conversation.engine import ConversationEngine
from talkcraft_ai.conversation.modes import MODES, get_topics_for_mode
from talkcraft_ai.conversation.memory import ConversationMemory
from talkcraft_ai.scoring.conversation_scorer import ConversationScorer
from talkcraft_ai.feedback.live_feedback import LiveFeedbackEngine, FeedbackItem
from talkcraft_ai.audio.tts_engine import TTSEngine
from talkcraft_ai.agents.llm_client import LLMClient
from talkcraft_ai.realtime.pipelines import ConversationPipeline

logger = get_logger("dashboard")

st.set_page_config(
    page_title="TalkCraft AI — Phase 3",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.llm = LLMClient()
        st.session_state.tts = TTSEngine()
        st.session_state.scorer = ConversationScorer()
        st.session_state.feedback = LiveFeedbackEngine()
        st.session_state.engine = ConversationEngine(
            st.session_state.llm, st.session_state.scorer
        )
        st.session_state.pipeline = ConversationPipeline(
            st.session_state.engine,
            st.session_state.tts,
            st.session_state.scorer,
            st.session_state.feedback,
        )
        st.session_state.conversation_active = False
        st.session_state.transcript: List[Dict] = []
        st.session_state.ai_response = ""
        st.session_state.scores = {}
        st.session_state.feedback_items: List[FeedbackItem] = []
        st.session_state.last_refresh = time.time()
        st.session_state.mode = "casual_conversation"
        st.session_state.topic = ""
        st.session_state.current_ai_message = ""
        _setup_callbacks()

    if "user_input" not in st.session_state:
        st.session_state.user_input = ""
    if "show_followups" not in st.session_state:
        st.session_state.show_followups = False
    if "followup_questions" not in st.session_state:
        st.session_state.followup_questions = []
    if "difficulty_level" not in st.session_state:
        st.session_state.difficulty_level = "intermediate"
    if "session_summary" not in st.session_state:
        st.session_state.session_summary = {}


def _setup_callbacks():
    eng = st.session_state.engine
    eng.set_callbacks(
        on_difficulty_change=lambda old, new: setattr(
            st.session_state, "difficulty_level", new
        ),
    )

    pipe = st.session_state.pipeline
    pipe.set_callbacks(
        on_transcription=_on_transcription,
        on_ai_chunk=_on_ai_chunk,
        on_ai_response=_on_ai_response,
        on_feedback=_on_feedback_pipe,
        on_scores=_on_scores_pipe,
    )


def _on_transcription(text: str):
    st.session_state.transcript.append({"role": "user", "content": text})
    if len(st.session_state.transcript) > 100:
        st.session_state.transcript = st.session_state.transcript[-50:]


def _on_ai_chunk(chunk: str):
    st.session_state.current_ai_message += chunk


def _on_ai_response(text: str):
    st.session_state.transcript.append({"role": "assistant", "content": text})
    st.session_state.current_ai_message = ""


def _on_feedback_pipe(items: List[FeedbackItem]):
    st.session_state.feedback_items.extend(items)
    if len(st.session_state.feedback_items) > 100:
        st.session_state.feedback_items = st.session_state.feedback_items[-50:]


def _on_scores_pipe(scores: Dict):
    st.session_state.scores = scores


def start_conversation():
    if st.session_state.conversation_active:
        return
    eng = st.session_state.engine
    eng.set_mode(st.session_state.mode, st.session_state.topic)
    greeting = eng.start_conversation()
    st.session_state.pipeline.start()
    st.session_state.conversation_active = True
    st.session_state.transcript.clear()
    st.session_state.feedback_items.clear()
    st.session_state.scores = {}
    st.session_state.current_ai_message = ""
    if greeting:
        st.session_state.transcript.append({"role": "assistant", "content": greeting.content})


def stop_conversation():
    if not st.session_state.conversation_active:
        return
    summary = st.session_state.engine.stop_conversation()
    st.session_state.pipeline.stop()
    st.session_state.conversation_active = False
    st.session_state.session_summary = summary
    st.session_state.tts.stop()


def send_message():
    text = st.session_state.user_input.strip()
    if not text:
        return
    st.session_state.pipeline.receive_transcription(text)
    st.session_state.user_input = ""


def generate_followups():
    eng = st.session_state.engine
    questions = eng.generate_followup_questions(3)
    st.session_state.followup_questions = questions
    st.session_state.show_followups = True


def select_followup(question: str):
    st.session_state.user_input = question
    st.session_state.show_followups = False


def render_sidebar():
    with st.sidebar:
        st.markdown(
            "<h1 style='text-align: center; color: #4CAF50;'>🎙️ TalkCraft AI</h1>",
            unsafe_allow_html=True,
        )
        st.markdown("<p style='text-align: center; color: #888;'>Phase 3 — Conversation Intelligence</p>", unsafe_allow_html=True)
        st.divider()
        mode_options = {v.name: k for k, v in MODES.items()}
        selected_mode_name = st.selectbox(
            "Conversation Mode",
            options=list(mode_options.keys()),
            index=1,
            key="mode_selector",
        )
        st.session_state.mode = mode_options[selected_mode_name]
        topics = get_topics_for_mode(st.session_state.mode)
        topic = st.selectbox("Topic (optional)", options=[""] + topics, key="topic_selector")
        st.session_state.topic = topic if topic else ""
        st.divider()
        st.markdown("### Controls")
        col1, col2 = st.columns(2)
        with col1:
            if not st.session_state.conversation_active:
                if st.button("▶️ Start", use_container_width=True, type="primary"):
                    start_conversation()
                    st.rerun()
            else:
                if st.button("⏹️ Stop", use_container_width=True, type="secondary"):
                    stop_conversation()
                    st.rerun()
        with col2:
            if st.session_state.conversation_active:
                if st.button("💡 Follow-ups", use_container_width=True):
                    generate_followups()
                    st.rerun()
        st.divider()
        st.markdown("### Mode Description")
        mode_info = MODES.get(st.session_state.mode)
        if mode_info:
            st.caption(mode_info.description)
            with st.expander("Evaluation Focus"):
                for focus in mode_info.evaluation_focus:
                    st.markdown(f"- {focus}")
        st.divider()
        st.caption(f"Difficulty: **{st.session_state.difficulty_level}**")
        st.caption(f"LLM: {st.session_state.llm.model}")
        st.caption(f"TTS: {'Enabled' if st.session_state.tts.enabled else 'Disabled'}")


def render_transcript():
    st.markdown("### 💬 Conversation Transcript")
    transcript_container = st.container(height=400, border=True)
    with transcript_container:
        if not st.session_state.transcript:
            st.caption("Start a conversation to see the transcript here.")
        for msg in st.session_state.transcript[-30:]:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                st.markdown(
                    f"<div style='background: #2d2d2d; padding: 8px 12px; "
                    f"border-radius: 8px; margin: 4px 0; border-left: 3px solid #4CAF50;'>"
                    f"<strong style='color: #4CAF50;'>You:</strong> {content}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div style='background: #1e3a2e; padding: 8px 12px; "
                    f"border-radius: 8px; margin: 4px 0; border-left: 3px solid #81C784;'>"
                    f"<strong style='color: #81C784;'>AI:</strong> {content}</div>",
                    unsafe_allow_html=True,
                )
        if st.session_state.current_ai_message:
            st.markdown(
                f"<div style='background: #1e3a2e; padding: 8px 12px; "
                f"border-radius: 8px; margin: 4px 0; border-left: 3px solid #81C784;'>"
                f"<strong style='color: #81C784;'>AI:</strong> {st.session_state.current_ai_message}"
                f"<span style='color: #666;'>▌</span></div>",
                unsafe_allow_html=True,
            )


def render_input():
    st.markdown("### ✏️ Your Response")
    col1, col2 = st.columns([5, 1])
    with col1:
        st.text_input(
            "Type your message",
            key="user_input",
            placeholder="Type your message here...",
            label_visibility="collapsed",
            on_change=send_message,
            disabled=not st.session_state.conversation_active,
        )
    with col2:
        st.button("Send", on_click=send_message, disabled=not st.session_state.conversation_active)
    if st.session_state.show_followups and st.session_state.followup_questions:
        st.markdown("#### Suggested Follow-ups")
        cols = st.columns(len(st.session_state.followup_questions))
        for i, q in enumerate(st.session_state.followup_questions):
            with cols[i]:
                st.button(q, on_click=select_followup, args=(q,))


def render_metrics():
    scores = st.session_state.scores
    if not scores:
        return
    st.markdown("### 📊 Communication Metrics")
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        overall = scores.get("overall", 0)
        st.metric("Overall Score", f"{overall:.0%}", delta=scores.get("trend", ""))
    with mcol2:
        st.metric("Clarity", f"{scores.get('clarity', 0):.0%}")
    with mcol3:
        st.metric("Engagement", f"{scores.get('engagement', 0):.0%}")
    with mcol4:
        st.metric("Confidence", f"{scores.get('confidence', 0):.0%}")
    mcol5, mcol6, mcol7, mcol8 = st.columns(4)
    with mcol5:
        st.metric("Grammar", f"{scores.get('grammar', 0):.0%}")
    with mcol6:
        st.metric("Pace", f"{scores.get('pace', 0):.0%}")
    with mcol7:
        st.metric("Eye Contact", f"{scores.get('eye_contact', 0):.0%}")
    with mcol8:
        filler = scores.get("filler", 0)
        st.metric("Fillers", f"{filler:.0%}", delta_color="inverse")


def render_feedback():
    st.markdown("### 🔔 Live Feedback")
    fb_container = st.container(height=250, border=True)
    with fb_container:
        if not st.session_state.feedback_items:
            st.caption("Feedback will appear here during conversation.")
        for item in st.session_state.feedback_items[-15:]:
            sev = item.severity
            if sev == "critical":
                icon, color = "🔴", "#f44336"
            elif sev == "warning":
                icon, color = "🟡", "#FF9800"
            elif sev == "positive":
                icon, color = "🟢", "#4CAF50"
            else:
                icon, color = "🔵", "#2196F3"
            st.markdown(
                f"<div style='background: #2d2d2d; padding: 6px 10px; "
                f"border-radius: 6px; margin: 3px 0; border-left: 3px solid {color};'>"
                f"{icon} <strong>{item.category.title()}:</strong> {item.message}</div>",
                unsafe_allow_html=True,
            )


def render_session_summary():
    if not st.session_state.session_summary:
        return
    summary = st.session_state.session_summary
    with st.expander("📋 Session Summary", expanded=True):
        sc = summary.get("scores", {})
        scol1, scol2, scol3, scol4 = st.columns(4)
        with scol1:
            st.metric("Total Turns", summary.get("total_turns", 0))
        with scol2:
            st.metric("Duration", f"{summary.get('duration', 0):.0f}s")
        with scol3:
            st.metric("Avg Score", f"{sc.get('average', 0):.0%}")
        with scol4:
            st.metric("Best Score", f"{sc.get('best', 0):.0%}")
        st.markdown(f"**Final Overall Score:** {sc.get('overall', 0):.0%}")
        st.markdown(f"**Trend:** {sc.get('trend', 'stable').title()}")
        st.markdown(f"**Difficulty Reached:** {summary.get('difficulty', 'intermediate').title()}")


def render_confidence_visualization():
    scores = st.session_state.scores
    if not scores or not scores.get("overall"):
        return
    st.markdown("### 📈 Confidence & Performance")
    cols = st.columns(5)
    metrics_to_show = [
        ("Overall", "overall", "#4CAF50"),
        ("Clarity", "clarity", "#2196F3"),
        ("Engagement", "engagement", "#FF9800"),
        ("Grammar", "grammar", "#9C27B0"),
        ("Pace", "pace", "#00BCD4"),
    ]
    for col, (label, key, color) in zip(cols, metrics_to_show):
        val = scores.get(key, 0)
        col.markdown(
            f"<div style='text-align:center;'>"
            f"<div style='font-size: 12px; color: #888;'>{label}</div>"
            f"<div style='font-size: 28px; font-weight: bold; color: {color};'>{val:.0%}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


def main():
    init_session_state()
    render_sidebar()
    main_col, right_col = st.columns([3, 2])
    with main_col:
        render_transcript()
        render_input()
        if st.session_state.conversation_active:
            if st.button("💡 Generate Follow-up Questions"):
                generate_followups()
        if st.session_state.show_followups and st.session_state.followup_questions:
            st.markdown("#### Suggested Follow-ups")
            for q in st.session_state.followup_questions:
                st.button(f"❓ {q}", on_click=select_followup, args=(q,))
    with right_col:
        render_metrics()
        render_confidence_visualization()
        render_feedback()
        if not st.session_state.conversation_active and st.session_state.session_summary:
            render_session_summary()
    time.sleep(config.dashboard.refresh_interval_ms / 2000.0)



