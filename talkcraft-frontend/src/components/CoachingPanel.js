import React, { useEffect, useState } from "react";

export default function CoachingPanel({ summary, weaknesses, coachingFocus, recommendations }) {
  const [activeSection, setActiveSection] = useState("overview");

  if (!summary) {
    return (
      <div className="bg-surface border border-border rounded-lg p-6">
        <p className="text-text-secondary">Loading coaching data...</p>
      </div>
    );
  }

  const sections = {
    overview: { label: "Overview", icon: "📊" },
    weaknesses: { label: "Weaknesses", icon: "🎯" },
    coaching: { label: "Coaching", icon: "🤖" },
    practice: { label: "Practice", icon: "💪" },
  };

  return (
    <div>
      <div className="flex gap-2 mb-4 flex-wrap">
        {Object.entries(sections).map(([key, { label, icon }]) => (
          <button
            key={key}
            onClick={() => setActiveSection(key)}
            className={`px-4 py-2 text-sm rounded transition-colors ${
              activeSection === key
                ? "bg-accent text-black font-medium"
                : "bg-surface border border-border text-text-secondary hover:text-white"
            }`}
          >
            {icon} {label}
          </button>
        ))}
      </div>

      {activeSection === "overview" && (
        <div>
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div className="bg-surface border border-border rounded-lg p-4">
              <p className="text-text-secondary text-xs uppercase tracking-wider">Total Sessions</p>
              <p className="text-2xl font-bold mt-1">{summary.total_sessions || 0}</p>
            </div>
            <div className="bg-surface border border-border rounded-lg p-4">
              <p className="text-text-secondary text-xs uppercase tracking-wider">Practice Time</p>
              <p className="text-2xl font-bold mt-1">{summary.total_practice_minutes || 0}m</p>
            </div>
            <div className="bg-surface border border-border rounded-lg p-4">
              <p className="text-text-secondary text-xs uppercase tracking-wider">Avg Score</p>
              <p className="text-2xl font-bold mt-1 text-accent">{((summary.average_score || 0) * 100).toFixed(0)}%</p>
            </div>
            <div className="bg-surface border border-border rounded-lg p-4">
              <p className="text-text-secondary text-xs uppercase tracking-wider">Streak</p>
              <p className="text-2xl font-bold mt-1 text-warning">
                {summary.current_streak?.current || 0}d
                <span className="text-xs text-text-secondary"> / {summary.current_streak?.longest || 0}d best</span>
              </p>
            </div>
          </div>

          {summary.improvement_pct !== undefined && (
            <div className="bg-surface border border-border rounded-lg p-4">
              <p className="text-text-secondary text-xs uppercase tracking-wider mb-1">Overall Improvement</p>
              <div className="flex items-center gap-4">
                <div className="flex-1 bg-black rounded-full h-3">
                  <div
                    className="bg-accent h-3 rounded-full transition-all"
                    style={{ width: `${Math.max(0, Math.min(100, (summary.average_score || 0) * 100))}%` }}
                  />
                </div>
                <span className={`text-lg font-bold ${summary.improvement >= 0 ? 'text-accent' : 'text-danger'}`}>
                  {summary.improvement_pct > 0 ? '+' : ''}{summary.improvement_pct?.toFixed(1)}%
                </span>
              </div>
              <p className="text-text-secondary text-xs mt-2">
                {summary.improvement >= 0 ? 'Improving' : 'Declining'} — Last session: {summary.last_session_mode || 'N/A'} ({((summary.latest_score || 0) * 100).toFixed(0)}%)
              </p>
            </div>
          )}

          {recommendations && recommendations.length > 0 && (
            <div className="mt-4 bg-surface border border-border rounded-lg p-4">
              <p className="text-text-secondary text-xs uppercase tracking-wider mb-3">Today's Practice</p>
              <div className="space-y-2">
                {recommendations.map((rec, i) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-black rounded">
                    <div>
                      <p className="text-sm">{rec.title}</p>
                      <p className="text-xs text-text-secondary">{rec.duration_minutes} min · {rec.difficulty?.charAt(0).toUpperCase() + rec.difficulty?.slice(1)}</p>
                    </div>
                    <span className={rec.completed ? 'text-accent' : 'text-text-secondary'}>
                      {rec.completed ? '✅' : '⏳'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeSection === "weaknesses" && weaknesses && (
        <div>
          {weaknesses.available === false ? (
            <div className="bg-surface border border-border rounded-lg p-6">
              <p className="text-text-secondary">{weaknesses.message || "Not enough data to detect weaknesses"}</p>
            </div>
          ) : (
            <div>
              {weaknesses.strengths && weaknesses.strengths.length > 0 && (
                <div className="mb-4">
                  <p className="text-text-secondary text-xs uppercase tracking-wider mb-3">Strengths</p>
                  <div className="grid grid-cols-2 gap-3">
                    {weaknesses.strengths.map((s, i) => (
                      <div key={i} className="bg-surface border border-accent/30 rounded-lg p-3">
                        <p className="text-sm font-medium text-accent">{s.label}</p>
                        <p className="text-xs text-text-secondary">Score: {(s.average_score * 100).toFixed(0)}% · {s.trend}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {weaknesses.weaknesses && weaknesses.weaknesses.length > 0 && (
                <div>
                  <p className="text-text-secondary text-xs uppercase tracking-wider mb-3">Areas to Improve</p>
                  <div className="space-y-3">
                    {weaknesses.weaknesses.map((w, i) => (
                      <div key={i} className="bg-surface border border-border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <p className="font-medium">{w.label}</p>
                          <span className={`text-xs px-2 py-1 rounded ${
                            w.status === 'critical' ? 'bg-red-900/50 text-red-400' :
                            w.status === 'weak' ? 'bg-orange-900/50 text-orange-400' :
                            'bg-yellow-900/50 text-yellow-400'
                          }`}>
                            {w.status?.toUpperCase()}
                          </span>
                        </div>
                        <div className="bg-black rounded-full h-2 mb-2">
                          <div
                            className={`h-2 rounded-full transition-all ${
                              w.average_score >= 0.6 ? 'bg-accent' :
                              w.average_score >= 0.4 ? 'bg-warning' : 'bg-danger'
                            }`}
                            style={{ width: `${(w.average_score * 100).toFixed(0)}%` }}
                          />
                        </div>
                        <div className="flex justify-between text-xs text-text-secondary">
                          <span>Score: {(w.average_score * 100).toFixed(0)}%</span>
                          <span>Trend: {w.trend}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeSection === "coaching" && coachingFocus && (
        <div>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-surface border border-border rounded-lg p-4">
              <p className="text-text-secondary text-xs uppercase tracking-wider">Difficulty Level</p>
              <p className="text-xl font-bold mt-1">{coachingFocus.difficulty?.charAt(0).toUpperCase() + coachingFocus.difficulty?.slice(1)}</p>
            </div>
            <div className="bg-surface border border-border rounded-lg p-4">
              <p className="text-text-secondary text-xs uppercase tracking-wider">Coaching Style</p>
              <p className="text-xl font-bold mt-1">{coachingFocus.coaching_style?.style?.charAt(0).toUpperCase() + coachingFocus.coaching_style?.style?.slice(1)}</p>
            </div>
          </div>

          {coachingFocus.coaching_style && (
            <div className="bg-surface border border-border rounded-lg p-4 mb-4">
              <p className="text-text-secondary text-xs uppercase tracking-wider mb-3">Coaching Profile</p>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-xs text-text-secondary">Complexity</p>
                  <p className="text-sm font-medium">{coachingFocus.coaching_style.complexity?.charAt(0).toUpperCase() + coachingFocus.coaching_style.complexity?.slice(1)}</p>
                </div>
                <div>
                  <p className="text-xs text-text-secondary">Feedback</p>
                  <p className="text-sm font-medium">{coachingFocus.coaching_style.feedback_frequency?.charAt(0).toUpperCase() + coachingFocus.coaching_style.feedback_frequency?.slice(1)}</p>
                </div>
                <div>
                  <p className="text-xs text-text-secondary">Encouragement</p>
                  <p className="text-sm font-medium">{coachingFocus.coaching_style.encouragement?.charAt(0).toUpperCase() + coachingFocus.coaching_style.encouragement?.slice(1)}</p>
                </div>
              </div>
            </div>
          )}

          {coachingFocus.recommended_mode && (
            <div className="bg-surface border border-accent/30 rounded-lg p-4">
              <p className="text-xs text-text-secondary uppercase tracking-wider mb-1">Recommended Mode</p>
              <p className="text-lg font-medium text-accent">
                {coachingFocus.recommended_mode.mode?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </p>
              <p className="text-xs text-text-secondary mt-1">{coachingFocus.recommended_mode.reason}</p>
            </div>
          )}

          {coachingFocus.focus_areas && coachingFocus.focus_areas.length > 0 && (
            <div className="mt-4">
              <p className="text-text-secondary text-xs uppercase tracking-wider mb-3">Priority Focus Areas</p>
              <div className="space-y-2">
                {coachingFocus.focus_areas.map((area, i) => (
                  <div key={i} className="p-3 bg-black border border-border rounded text-sm">
                    ⚠️ {area.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeSection === "practice" && (
        <div className="bg-surface border border-border rounded-lg p-6">
          <p className="text-text-secondary text-xs uppercase tracking-wider mb-3">Daily Practice Tips</p>
          <div className="space-y-3">
            <div className="p-3 bg-black rounded">
              <p className="text-sm font-medium">🎯 Focus on Weakest Area First</p>
              <p className="text-xs text-text-secondary mt-1">Spend the first 5 minutes of each session on your weakest communication skill.</p>
            </div>
            <div className="p-3 bg-black rounded">
              <p className="text-sm font-medium">⏱️ Short & Consistent</p>
              <p className="text-xs text-text-secondary mt-1">10 minutes of daily practice is more effective than 1 hour once a week.</p>
            </div>
            <div className="p-3 bg-black rounded">
              <p className="text-sm font-medium">📝 Review Session Analysis</p>
              <p className="text-xs text-text-secondary mt-1">After each session, review your weaknesses and adjust your focus for next time.</p>
            </div>
            <div className="p-3 bg-black rounded">
              <p className="text-sm font-medium">🔄 Mix Conversation Modes</p>
              <p className="text-xs text-text-secondary mt-1">Try different modes (interview, casual, debate) to develop versatile skills.</p>
            </div>
            <div className="p-3 bg-black rounded">
              <p className="text-sm font-medium">📈 Track Your Progress</p>
              <p className="text-xs text-text-secondary mt-1">Watch your trend graphs to stay motivated — small improvements add up!</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
