import React from "react";

export default function StatusBar({ isRecording, inputMode, sessionDuration }) {
  const statusText = !isRecording
    ? "Idle"
    : inputMode === "file"
    ? "Processing file"
    : "Recording";

  const colorClass = !isRecording
    ? "text-gray-500"
    : "text-red-400";

  return (
    <div className="text-center text-sm text-text-secondary border-t border-border pt-4 mt-6">
      Status: <span className={colorClass}>{statusText}</span>
      {" | "}Mode: {inputMode === "mic" ? "Microphone" : "File"}
      {" | "}Duration: {Math.floor(sessionDuration)}s
    </div>
  );
}
