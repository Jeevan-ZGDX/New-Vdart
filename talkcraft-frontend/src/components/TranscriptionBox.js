import React from "react";

export default function TranscriptionBox({ text, history, isRecording, inputMode }) {
  const placeholder = !isRecording
    ? "Waiting for speech..."
    : inputMode === "mic"
    ? "Listening..."
    : "Processing file...";

  return (
    <div>
      <h3 className="text-lg font-semibold mb-2">Live Transcription</h3>
      <div className="bg-surface border border-border rounded-lg p-4 min-h-[120px] text-lg leading-relaxed">
        {text || <span className="text-gray-500 italic">{placeholder}</span>}
      </div>
      {history.length > 0 && (
        <details className="mt-3">
          <summary className="text-sm text-text-secondary cursor-pointer hover:text-gray-300">
            Recent Transcription History
          </summary>
          <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
            {history
              .slice(-10)
              .reverse()
              .map((t, i) => (
                <div key={i} className="text-sm text-gray-400 border-b border-border pb-1">
                  {t}
                </div>
              ))}
          </div>
        </details>
      )}
    </div>
  );
}
