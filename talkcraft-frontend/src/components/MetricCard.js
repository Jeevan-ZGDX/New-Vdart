import React from "react";

export default function MetricCard({ label, value, unit, color = "#4CAF50", sub }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <div className="text-xs text-text-secondary uppercase tracking-wide">
        {label}
      </div>
      <div className="text-3xl font-bold mt-1" style={{ color }}>
        {value}
      </div>
      {sub && <div className="text-xs text-text-secondary mt-1">{sub}</div>}
      {unit && (
        <div className="text-xs text-text-secondary mt-1">{unit}</div>
      )}
    </div>
  );
}
