import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { calculateBenchmarks, getBenchmarkRoles, getRoleBenchmarkScore } from "@/utils/api";
import { useAuth } from "./_app";
import Sidebar from "@/components/Sidebar";

export default function BenchmarksPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const [benchmarks, setBenchmarks] = useState(null);
  const [roles, setRoles] = useState([]);
  const [selectedRole, setSelectedRole] = useState(null);
  const [roleScore, setRoleScore] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) { router.push("/login"); return; }
    getBenchmarkRoles().then(d => setRoles(d.roles || [])).catch(() => {}).finally(() => setLoading(false));
  }, [isAuthenticated]);

  const sessionData = {
    overall_score: 0.75, clarity_score: 0.7, engagement_score: 0.65,
    confidence_score: 0.72, average_eye_contact: 0.68, average_posture: 0.7,
    average_wpm: 155, filler_rate: 0.035, grammar_errors: 3, word_count: 150,
  };

  const handleCalculate = async () => {
    const result = await calculateBenchmarks(sessionData);
    setBenchmarks(result);
  };

  const handleRoleScore = async (roleId) => {
    setSelectedRole(roleId);
    const result = await getRoleBenchmarkScore(roleId, sessionData);
    setRoleScore(result);
  };

  return (
    <div className="flex min-h-screen bg-black text-white">
      <Sidebar onModeChange={() => {}} />
      <main className="flex-1 p-6 overflow-y-auto">
        <h2 className="text-xl font-semibold mb-6">📊 Communication Benchmarks</h2>
        {loading ? <p className="text-text-secondary">Loading...</p> : (
          <>
            <button onClick={handleCalculate} className="px-6 py-2 bg-accent text-black rounded font-medium hover:bg-accent/90 mb-6">Calculate Benchmarks</button>
            {benchmarks && (
              <div className="mb-6">
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-lg font-medium">Overall: {(benchmarks.overall * 100).toFixed(0)}%</span>
                  <span className={`px-3 py-1 rounded text-sm ${
                    benchmarks.overall_status === "excellent" ? "bg-green-900/50 text-green-400" :
                    benchmarks.overall_status === "good" ? "bg-yellow-900/50 text-yellow-400" : "bg-red-900/50 text-red-400"
                  }`}>{benchmarks.overall_status}</span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(benchmarks.benchmarks || {}).map(([key, b]) => (
                    <div key={key} className="bg-surface border border-border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <p className="font-medium text-sm">{b.label}</p>
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          b.status === "excellent" ? "bg-green-900/50 text-green-400" :
                          b.status === "good" ? "bg-yellow-900/50 text-yellow-400" : "bg-red-900/50 text-red-400"
                        }`}>{b.status}</span>
                      </div>
                      <p className="text-2xl font-bold">{(b.score * 100).toFixed(0)}<span className="text-sm text-text-secondary">/{b.ideal_range?.[1] || 100}</span></p>
                      <p className="text-xs text-text-secondary">Ideal: {b.ideal_range?.[0]}-{b.ideal_range?.[1]} {b.unit}</p>
                      <div className="bg-black rounded-full h-2 mt-2">
                        <div className={`h-2 rounded-full ${
                          b.status === "excellent" ? "bg-accent" : b.status === "good" ? "bg-warning" : "bg-danger"
                        }`} style={{ width: `${(b.score * 100).toFixed(0)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div>
              <p className="text-text-secondary text-xs uppercase tracking-wider mb-3">Role-Specific Scores</p>
              <div className="grid grid-cols-3 gap-3 mb-4">
                {roles.map(r => (
                  <button key={r.id} onClick={() => handleRoleScore(r.id)}
                    className={`p-4 rounded-lg border text-center transition-all ${selectedRole === r.id ? "border-accent bg-accent/10" : "border-border bg-surface hover:border-accent/50"}`}>
                    <p className="font-medium">{r.label}</p>
                  </button>
                ))}
              </div>
              {roleScore && (
                <div className="bg-surface border border-border rounded-lg p-4">
                  <p className="text-accent font-medium mb-3">{roleScore.role_name}: {(roleScore.overall_score * 100).toFixed(0)}%</p>
                  <div className="space-y-2">
                    {Object.entries(roleScore.category_scores || {}).map(([cat, info]) => (
                      <div key={cat} className="flex items-center gap-3">
                        <p className="text-sm w-40">{cat.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}</p>
                        <div className="flex-1 bg-black rounded-full h-2">
                          <div className="bg-accent h-2 rounded-full" style={{ width: `${(info.score * 100).toFixed(0)}%` }} />
                        </div>
                        <p className="text-xs text-text-secondary w-16">{(info.score * 100).toFixed(0)}%</p>
                      </div>
                    ))}
                  </div>
                  {roleScore.recommendations?.length > 0 && (
                    <div className="mt-3">
                      <p className="text-xs text-text-secondary mb-1">Recommendations</p>
                      {roleScore.recommendations.map((r, i) => (
                        <p key={i} className="text-xs text-warning">💡 {r}</p>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
