import React, { useState, useEffect, useCallback, useRef } from "react";
import Sidebar from "@/components/Sidebar";
import MetricCard from "@/components/MetricCard";
import TranscriptionBox from "@/components/TranscriptionBox";
import FeedbackPanel from "@/components/FeedbackPanel";
import StatusBar from "@/components/StatusBar";
import WebcamView from "@/components/WebcamView";
import { connectWebSocket } from "@/utils/websocket";
import { getState } from "@/utils/api";

const defaultState = {
  transcription_text: "",
  transcription_history: [],
  current_wpm: 0,
  average_wpm: 0,
  pace_status: "normal",
  filler_count: 0,
  filler_rate: 0,
  grammar_errors: 0,
  feedback_messages: [],
  is_recording: false,
  session_duration: 0,
  total_words: 0,
  input_mode: "mic",
  eye_contact_score: 0,
  gaze_direction: "center",
  posture_stability: 0,
  head_pitch: 0,
  head_yaw: 0,
  head_roll: 0,
  hands_detected: 0,
  hand_activity: 0,
  gestures: [],
  confidence_score: 0,
  confidence_level: "moderate",
  face_detected: false,
};

function paceColor(status) {
  if (status === "too_fast") return "#f44336";
  if (status === "too_slow") return "#FF9800";
  return "#4CAF50";
}

function rateColor(rate) {
  return rate > 10 ? "#f44336" : "#4CAF50";
}

function errorColor(count) {
  return count > 0 ? "#f44336" : "#4CAF50";
}

function confidenceColor(level) {
  const colors = {
    excellent: "#4CAF50",
    good: "#8BC34A",
    moderate: "#FF9800",
    needs_improvement: "#FF5722",
    low: "#f44336",
  };
  return colors[level] || "#888888";
}

function gazeColor(direction) {
  return direction === "center" ? "#4CAF50" : "#FF9800";
}

export default function Dashboard() {
  const [state, setState] = useState(defaultState);
  const wsRef = useRef(null);

  useEffect(() => {
    getState()
      .then((data) => setState((prev) => ({ ...prev, ...data })))
      .catch(() => {});

    wsRef.current = connectWebSocket((data) => {
      if (data.type === "multimodal_update") {
        setState((prev) => ({
          ...prev,
          face_detected: data.face_detected ?? prev.face_detected,
          eye_contact_score: data.eye_contact_score ?? prev.eye_contact_score,
          gaze_direction: data.gaze_direction ?? prev.gaze_direction,
          posture_stability: data.posture_stability ?? prev.posture_stability,
          head_pitch: data.head_pitch ?? prev.head_pitch,
          head_yaw: data.head_yaw ?? prev.head_yaw,
          head_roll: data.head_roll ?? prev.head_roll,
          hands_detected: data.hands_detected ?? prev.hands_detected,
          hand_activity: data.hand_activity ?? prev.hand_activity,
          gestures: data.gestures ?? prev.gestures,
          confidence_score: data.confidence_score ?? prev.confidence_score,
          confidence_level: data.confidence_level ?? prev.confidence_level,
          feedback_messages: data.feedback_messages ?? prev.feedback_messages,
          session_duration: data.session_duration ?? prev.session_duration,
        }));
      } else {
        setState((prev) => ({
          ...prev,
          transcription_text: data.transcription_text ?? prev.transcription_text,
          transcription_history: data.transcription_history ?? prev.transcription_history,
          current_wpm: data.current_wpm ?? prev.current_wpm,
          average_wpm: data.average_wpm ?? prev.average_wpm,
          pace_status: data.pace_status ?? prev.pace_status,
          filler_count: data.filler_count ?? prev.filler_count,
          filler_rate: data.filler_rate ?? prev.filler_rate,
          grammar_errors: data.grammar_errors ?? prev.grammar_errors,
          feedback_messages: data.feedback_messages ?? prev.feedback_messages,
          is_recording: data.is_recording ?? prev.is_recording,
          session_duration: data.session_duration ?? prev.session_duration,
          total_words: data.total_words ?? prev.total_words,
          input_mode: data.input_mode ?? prev.input_mode,
        }));
      }
    });

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const handleModeChange = useCallback((mode) => {
    setState((prev) => ({ ...prev, input_mode: mode }));
  }, []);

  return (
    <div className="flex min-h-screen bg-black text-white">
      <Sidebar onModeChange={handleModeChange} />

      <main className="flex-1 p-6 overflow-y-auto">
        <h2 className="text-xl font-semibold mb-4">Speech Analysis</h2>
        <div className="grid grid-cols-4 gap-4 mb-6">
          <MetricCard
            label="Speaking Pace"
            value={state.current_wpm.toFixed(0)}
            unit="WPM"
            color={paceColor(state.pace_status)}
            sub={`avg: ${state.average_wpm.toFixed(0)}`}
          />
          <MetricCard
            label="Filler Words"
            value={state.filler_count}
            unit={`Rate: ${state.filler_rate.toFixed(1)}%`}
            color={rateColor(state.filler_rate)}
          />
          <MetricCard
            label="Grammar Issues"
            value={state.grammar_errors}
            unit="detected"
            color={errorColor(state.grammar_errors)}
          />
          <MetricCard
            label="Session"
            value={state.total_words}
            unit="words spoken"
            color="#4CAF50"
          />
        </div>

        <h2 className="text-xl font-semibold mb-4">Communication Presence</h2>
        <div className="grid grid-cols-4 gap-4 mb-6">
          <MetricCard
            label="Eye Contact"
            value={`${(state.eye_contact_score * 100).toFixed(0)}%`}
            unit={`Gaze: ${state.gaze_direction}`}
            color={gazeColor(state.gaze_direction)}
          />
          <MetricCard
            label="Posture"
            value={`${(state.posture_stability * 100).toFixed(0)}%`}
            unit={`P:${state.head_pitch.toFixed(0)}° Y:${state.head_yaw.toFixed(0)}° R:${state.head_roll.toFixed(0)}°`}
            color={state.posture_stability > 0.7 ? "#4CAF50" : "#f44336"}
          />
          <MetricCard
            label="Hand Activity"
            value={`${(state.hand_activity * 100).toFixed(0)}%`}
            unit={`Hands: ${state.hands_detected}`}
            color={state.hand_activity > 0.2 && state.hand_activity < 0.6 ? "#4CAF50" : "#FF9800"}
          />
          <MetricCard
            label="Confidence"
            value={`${(state.confidence_score * 100).toFixed(0)}%`}
            unit={state.confidence_level.replace('_', ' ')}
            color={confidenceColor(state.confidence_level)}
          />
        </div>

        <hr className="border-border mb-6" />

        <div className="grid grid-cols-2 gap-6">
          <div>
            <WebcamView isRunning={state.is_recording} />
            <div className="mt-4">
              <TranscriptionBox
                text={state.transcription_text}
                history={state.transcription_history}
                isRecording={state.is_recording}
                inputMode={state.input_mode}
              />
            </div>
          </div>
          <FeedbackPanel messages={state.feedback_messages} />
        </div>

        <StatusBar
          isRecording={state.is_recording}
          inputMode={state.input_mode}
          sessionDuration={state.session_duration}
        />
      </main>
    </div>
  );
}
