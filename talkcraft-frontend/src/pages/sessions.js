import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { getSessions, getSummary } from "@/utils/api";
import { useAuth } from "./_app";
import Sidebar from "@/components/Sidebar";
import MetricCard from "@/components/MetricCard";

export default function SessionsPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const [sessions, setSessions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    loadData();
  }, [isAuthenticated]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [s, sum] = await Promise.all([
        getSessions(50).catch(() => []),
        getSummary().catch(() => null),
      ]);
      setSessions(Array.isArray(s) ? s : []);
      setSummary(sum);
    } catch {}
    setLoading(false);
  };

  return (
    <div className="flex min-h-screen bg-black text-white">
      <Sidebar onModeChange={() => {}} />
      <main className="flex-1 p-6 overflow-y-auto">
        <h2 className="text-xl font-semibold mb-6">📋 Session History</h2>

        {loading ? (
          <p className="text-text-secondary">Loading sessions...</p>
        ) : (
          <>
            {summary && summary.available && (
              <div className="grid grid-cols-4 gap-4 mb-6">
                <MetricCard label="Total Sessions" value={summary.total_sessions || 0} color="#4CAF50" />
                <MetricCard label="Total Practice" value={`${summary.total_practice_minutes || 0}m`} color="#2196F3" />
                <MetricCard label="Avg Score" value={`${((summary.average_score || 0) * 100).toFixed(0)}%`} color="#FF9800" />
                <MetricCard label="Best Streak" value={`${summary.current_streak?.longest || 0}d`} color="#9C27B0" />
              </div>
            )}

            {sessions.length === 0 ? (
              <div className="bg-surface border border-border rounded-lg p-6 text-center">
                <p className="text-text-secondary">No sessions recorded yet</p>
                <p className="text-xs text-text-secondary mt-2">Complete a practice session and it will appear here</p>
              </div>
            ) : (
              <div className="space-y-3">
                {sessions.map((s) => (
                  <div key={s.session_id} className="bg-surface border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <span className={`text-sm font-medium ${
                          (s.scores?.overall || 0) >= 0.8 ? "text-accent" :
                          (s.scores?.overall || 0) >= 0.6 ? "text-warning" : "text-danger"
                        }`}>
                          {((s.scores?.overall || 0) * 100).toFixed(0)}%
                        </span>
                        <span className="text-sm">{s.mode?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                        {s.topic && <span className="text-xs text-text-secondary">— {s.topic}</span>}
                      </div>
                      <div className="flex items-center gap-4 text-xs text-text-secondary">
                        <span>{s.date?.slice(0, 10)}</span>
                        <span>{s.duration_minutes?.toFixed(0)}m</span>
                        <span>🎯 {s.difficulty?.charAt(0).toUpperCase() + s.difficulty?.slice(1)}</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-3">
                      <div>
                        <p className="text-xs text-text-secondary">WPM</p>
                        <p className="text-sm">{s.avg_wpm?.toFixed(0)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-text-secondary">Fillers</p>
                        <p className="text-sm">{s.filler_rate?.toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-xs text-text-secondary">Grammar</p>
                        <p className="text-sm">{s.grammar_errors} errors</p>
                      </div>
                      <div>
                        <p className="text-xs text-text-secondary">Words</p>
                        <p className="text-sm">{s.word_count}</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-3 mt-2">
                      <div>
                        <p className="text-xs text-text-secondary">Eye Contact</p>
                        <div className="bg-black rounded-full h-1.5 mt-1">
                          <div className="bg-accent h-1.5 rounded-full" style={{ width: `${s.eye_contact || 0}%` }} />
                        </div>
                      </div>
                      <div>
                        <p className="text-xs text-text-secondary">Posture</p>
                        <div className="bg-black rounded-full h-1.5 mt-1">
                          <div className="bg-accent h-1.5 rounded-full" style={{ width: `${s.posture || 0}%` }} />
                        </div>
                      </div>
                      <div>
                        <p className="text-xs text-text-secondary">Confidence</p>
                        <div className="bg-black rounded-full h-1.5 mt-1">
                          <div className="bg-accent h-1.5 rounded-full" style={{ width: `${s.confidence || 0}%` }} />
                        </div>
                      </div>
                    </div>

                    {s.weaknesses && s.weaknesses.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {s.weaknesses.slice(0, 3).map((w, i) => (
                          <span key={i} className={`text-xs px-2 py-0.5 rounded ${
                            w.severity === 'high' ? 'bg-red-900/50 text-red-400' : 'bg-yellow-900/50 text-yellow-400'
                          }`}>
                            {w.label}
                          </span>
                        ))}
                      </div>
                    )}

                    {s.strengths && s.strengths.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {s.strengths.slice(0, 2).map((st, i) => (
                          <span key={i} className="text-xs px-2 py-0.5 rounded bg-green-900/50 text-green-400">
                            ✅ {st.label}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
