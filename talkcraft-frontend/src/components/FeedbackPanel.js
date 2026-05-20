import React from "react";

export default function FeedbackPanel({ messages }) {
  return (
    <div>
      <h3 className="text-lg font-semibold mb-2">Real-Time Feedback</h3>
      {messages.length > 0 ? (
        <div className="space-y-2">
          {messages.slice(-5).reverse().map((msg, i) => (
            <div
              key={i}
              className="bg-[#2d2d2d] border-l-[3px] border-warning rounded-r px-3 py-2 text-sm"
            >
              {msg.message || msg}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-gray-500 italic text-sm">
          Feedback will appear here during your session
        </div>
      )}
    </div>
  );
}
