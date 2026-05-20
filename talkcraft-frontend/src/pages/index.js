import React, { useState, useEffect, useCallback, useRef } from "react";
import Sidebar from "@/components/Sidebar";
import MetricCard from "@/components/MetricCard";
import TranscriptionBox from "@/components/TranscriptionBox";
import FeedbackPanel from "@/components/FeedbackPanel";
import StatusBar from "@/components/StatusBar";
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

export default function Dashboard() {
  const [state, setState] = useState(defaultState);
  const wsRef = useRef(null);

  useEffect(() => {
    getState()
      .then((data) => setState((prev) => ({ ...prev, ...data })))
      .catch(() => {});

    wsRef.current = connectWebSocket((data) => {
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

        <hr className="border-border mb-6" />

        <div className="grid grid-cols-2 gap-6">
          <TranscriptionBox
            text={state.transcription_text}
            history={state.transcription_history}
            isRecording={state.is_recording}
            inputMode={state.input_mode}
          />
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
