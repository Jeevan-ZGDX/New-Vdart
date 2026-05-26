import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import {
  getCoachingFocus, getImprovementPlan, generatePlan,
  getRecommendations, generateRecommendations, getDifficulty,
} from "@/utils/api";
import { useAuth } from "./_app";
import Sidebar from "@/components/Sidebar";
import MetricCard from "@/components/MetricCard";

export default function CoachingPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const [focus, setFocus] = useState(null);
  const [plan, setPlan] = useState(null);
  const [recs, setRecs] = useState([]);
  const [difficulty, setDifficulty] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("focus");

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
      const [f, p, r, d] = await Promise.all([
        getCoachingFocus().catch(() => null),
        getImprovementPlan().catch(() => null),
        getRecommendations().catch(() => []),
        getDifficulty().catch(() => null),
      ]);
      setFocus(f);
      setPlan(p);
      setRecs(Array.isArray(r) ? r : []);
      setDifficulty(d);
    } catch {}
    setLoading(false);
  };

  const handleGeneratePlan = async () => {
    const newPlan = await generatePlan();
    if (newPlan) setPlan(newPlan);
  };

  const handleGenerateRecs = async () => {
    const newRecs = await generateRecommendations();
    if (Array.isArray(newRecs)) setRecs(newRecs);
  };

  return (
    <div className="flex min-h-screen bg-black text-white">
      <Sidebar onModeChange={() => {}} />
      <main className="flex-1 p-6 overflow-y-auto">
        <h2 className="text-xl font-semibold mb-6">🎯 Personalized Coaching</h2>

        <div className="flex gap-2 mb-6">
          {["focus", "plan", "practice", "difficulty"].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm rounded transition-colors ${
                tab === t
                  ? "bg-accent text-black font-medium"
                  : "bg-surface border border-border text-text-secondary hover:text-white"
              }`}
            >
              {t === "focus" ? "🤖 Focus" : t === "plan" ? "📋 Plan" : t === "practice" ? "💪 Practice" : "📊 Difficulty"}
            </button>
          ))}
          <button onClick={loadData} className="ml-auto px-3 py-2 text-sm bg-surface border border-border rounded text-text-secondary hover:text-white transition-colors">
            🔄 Refresh
          </button>
        </div>

        {loading ? (
          <p className="text-text-secondary">Loading coaching data...</p>
        ) : (
          <>
            {tab === "focus" && focus && (
              <div>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-surface border border-border rounded-lg p-4">
                    <p className="text-text-secondary text-xs uppercase tracking-wider">Difficulty</p>
                    <p className="text-2xl font-bold mt-1 text-accent">{focus.difficulty?.charAt(0).toUpperCase() + focus.difficulty?.slice(1)}</p>
                  </div>
                  <div className="bg-surface border border-border rounded-lg p-4">
                    <p className="text-text-secondary text-xs uppercase tracking-wider">Coaching Style</p>
                    <p className="text-2xl font-bold mt-1">{focus.coaching_style?.style?.charAt(0).toUpperCase() + focus.coaching_style?.style?.slice(1)}</p>
                  </div>
                </div>

                {focus.coaching_style && (
                  <div className="bg-surface border border-border rounded-lg p-4 mb-4">
                    <p className="text-text-secondary text-xs uppercase tracking-wider mb-3">Coaching Profile</p>
                    <div className="grid grid-cols-4 gap-4">
                      <div><p className="text-xs text-text-secondary">Complexity</p><p className="font-medium">{focus.coaching_style.complexity?.charAt(0).toUpperCase() + focus.coaching_style.complexity?.slice(1)}</p></div>
                      <div><p className="text-xs text-text-secondary">Feedback</p><p className="font-medium">{focus.coaching_style.feedback_frequency?.charAt(0).toUpperCase() + focus.coaching_style.feedback_frequency?.slice(1)}</p></div>
                      <div><p className="text-xs text-text-secondary">Encouragement</p><p className="font-medium">{focus.coaching_style.encouragement?.charAt(0).toUpperCase() + focus.coaching_style.encouragement?.slice(1)}</p></div>
                      <div><p className="text-xs text-text-secondary">Trend</p><p className="font-medium">{focus.trend?.charAt(0).toUpperCase() + focus.trend?.slice(1)}</p></div>
                    </div>
                    <p className="text-xs text-text-secondary mt-3 italic">{focus.coaching_style.description}</p>
                  </div>
                )}

                {focus.recommended_mode && (
                  <div className="bg-surface border border-accent/30 rounded-lg p-4 mb-4">
                    <p className="text-xs text-text-secondary uppercase tracking-wider">Recommended Mode</p>
                    <p className="text-lg font-medium text-accent mt-1">
                      {focus.recommended_mode.mode?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </p>
                    <p className="text-xs text-text-secondary">{focus.recommended_mode.reason}</p>
                  </div>
                )}

                {focus.focus_areas?.length > 0 && (
                  <div className="bg-surface border border-border rounded-lg p-4">
                    <p className="text-text-secondary text-xs uppercase tracking-wider mb-3">Priority Focus Areas</p>
                    {focus.focus_areas.map((area, i) => (
                      <div key={i} className="flex items-center gap-2 p-2 border-b border-border last:border-0">
                        <span className="text-warning">⚠️</span>
                        <span>{area.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {tab === "plan" && (
              <div>
                {plan ? (
                  <div className="bg-surface border border-border rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-medium">{plan.title}</h3>
                        <p className="text-sm text-text-secondary">{plan.description}</p>
                      </div>
                      <span className="text-sm px-3 py-1 bg-accent/20 text-accent rounded">{plan.difficulty?.charAt(0).toUpperCase() + plan.difficulty?.slice(1)}</span>
                    </div>

                    {plan.progress_pct !== undefined && (
                      <div className="mb-4">
                        <div className="flex justify-between text-xs text-text-secondary mb-1">
                          <span>Progress</span>
                          <span>{plan.progress_pct}%</span>
                        </div>
                        <div className="bg-black rounded-full h-2">
                          <div className="bg-accent h-2 rounded-full" style={{ width: `${plan.progress_pct}%` }} />
                        </div>
                      </div>
                    )}

                    {plan.focus_areas?.length > 0 && (
                      <div className="mb-4">
                        <p className="text-text-secondary text-xs uppercase tracking-wider mb-2">Focus Areas</p>
                        <div className="flex gap-2 flex-wrap">
                          {plan.focus_areas.map((area, i) => (
                            <span key={i} className="px-3 py-1 bg-black border border-border rounded text-sm">
                              🎯 {area.label || area.area?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {plan.exercises?.length > 0 && (
                      <div className="mb-4">
                        <p className="text-text-secondary text-xs uppercase tracking-wider mb-2">Exercises</p>
                        <div className="space-y-2">
                          {plan.exercises.map((ex, i) => (
                            <div key={i} className="p-3 bg-black rounded">
                              <div className="flex items-center justify-between">
                                <p className="font-medium text-sm">{ex.name}</p>
                                <span className="text-xs text-text-secondary">{ex.duration_minutes} min</span>
                              </div>
                              <p className="text-xs text-text-secondary mt-1">{ex.description}</p>
                              <span className={`text-xs mt-1 inline-block px-2 py-0.5 rounded ${
                                ex.difficulty === 'beginner' ? 'bg-green-900/50 text-green-400' :
                                ex.difficulty === 'intermediate' ? 'bg-yellow-900/50 text-yellow-400' :
                                'bg-red-900/50 text-red-400'
                              }`}>{ex.difficulty?.charAt(0).toUpperCase() + ex.difficulty?.slice(1)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="flex gap-3 mt-4">
                      <button onClick={handleGeneratePlan} className="px-4 py-2 bg-accent text-black rounded text-sm font-medium hover:bg-accent/90 transition-colors">
                        🔄 Regenerate Plan
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="bg-surface border border-border rounded-lg p-6 text-center">
                    <p className="text-text-secondary mb-4">No active improvement plan</p>
                    <button onClick={handleGeneratePlan} className="px-6 py-2 bg-accent text-black rounded font-medium hover:bg-accent/90 transition-colors">
                      Generate Plan
                    </button>
                  </div>
                )}
              </div>
            )}

            {tab === "practice" && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <p className="text-text-secondary text-xs uppercase tracking-wider">Today's Recommendations</p>
                  <button onClick={handleGenerateRecs} className="px-3 py-1 text-sm bg-surface border border-border rounded text-text-secondary hover:text-white transition-colors">
                    Generate New
                  </button>
                </div>

                {recs.length > 0 ? (
                  <div className="space-y-3">
                    {recs.map((rec, i) => (
                      <div key={i} className="bg-surface border border-border rounded-lg p-4 flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className={rec.completed ? 'text-accent' : 'text-warning'}>{rec.completed ? '✅' : '⚡'}</span>
                            <p className="font-medium">{rec.title}</p>
                          </div>
                          <p className="text-xs text-text-secondary mt-1">{rec.description}</p>
                          <div className="flex gap-2 mt-2">
                            <span className="text-xs text-text-secondary">{rec.duration_minutes} min</span>
                            <span className={`text-xs px-2 py-0.5 rounded ${
                              rec.difficulty === 'beginner' ? 'bg-green-900/50 text-green-400' :
                              rec.difficulty === 'intermediate' ? 'bg-yellow-900/50 text-yellow-400' :
                              'bg-red-900/50 text-red-400'
                            }`}>{rec.difficulty?.charAt(0).toUpperCase() + rec.difficulty?.slice(1)}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-surface border border-border rounded-lg p-6 text-center">
                    <p className="text-text-secondary">No recommendations yet</p>
                    <button onClick={handleGenerateRecs} className="mt-3 px-4 py-2 bg-accent text-black rounded text-sm font-medium hover:bg-accent/90 transition-colors">
                      Generate Recommendations
                    </button>
                  </div>
                )}

                <div className="mt-6 bg-surface border border-border rounded-lg p-4">
                  <p className="text-text-secondary text-xs uppercase tracking-wider mb-3">Practice Tips</p>
                  <div className="space-y-2 text-sm">
                    <p>🎯 Focus on your weakest area first each session</p>
                    <p>⏱️ 10 min daily &gt; 1 hour weekly</p>
                    <p>📝 Review session analysis after each practice</p>
                    <p>🔄 Mix different conversation modes</p>
                    <p>📈 Track your progress to stay motivated</p>
                  </div>
                </div>
              </div>
            )}

            {tab === "difficulty" && difficulty && (
              <div>
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <MetricCard label="Current Level" value={difficulty.level?.charAt(0).toUpperCase() + difficulty.level?.slice(1)} color="#4CAF50" />
                  <MetricCard label="Trend" value={difficulty.trend?.charAt(0).toUpperCase() + difficulty.trend?.slice(1)} color={difficulty.trend === 'improving' ? '#4CAF50' : difficulty.trend === 'declining' ? '#f44336' : '#FF9800'} />
                  <MetricCard label="Sessions Analyzed" value={difficulty.sessions_analyzed || 0} color="#888" />
                </div>

                <div className="bg-surface border border-border rounded-lg p-4 mb-4">
                  <p className="text-text-secondary text-xs uppercase tracking-wider mb-1">Reason</p>
                  <p className="text-sm">{difficulty.reason || "N/A"}</p>
                </div>

                {difficulty.avg_recent_score !== undefined && (
                  <div className="bg-surface border border-border rounded-lg p-4">
                    <p className="text-text-secondary text-xs uppercase tracking-wider mb-2">Recent Performance</p>
                    <div className="bg-black rounded-full h-4">
                      <div className="bg-accent h-4 rounded-full flex items-center justify-center text-xs font-medium" style={{ width: `${difficulty.avg_recent_score * 100}%` }}>
                        {(difficulty.avg_recent_score * 100).toFixed(0)}%
                      </div>
                    </div>
                    <p className="text-xs text-text-secondary mt-2">All-time average: {(difficulty.avg_all_time_score * 100).toFixed(0)}%</p>
                  </div>
                )}

                {difficulty.changed && (
                  <div className="mt-4 p-4 bg-accent/10 border border-accent/30 rounded-lg">
                    <p className="text-accent font-medium">🎉 Difficulty adapted from {difficulty.previous_level?.charAt(0).toUpperCase() + difficulty.previous_level?.slice(1)} to {difficulty.level?.charAt(0).toUpperCase() + difficulty.level?.slice(1)}!</p>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
