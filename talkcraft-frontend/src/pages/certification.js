import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { getCertificationLevels, assessCertification, evaluateCertificationSession, generateCertificate } from "@/utils/api";
import { getSummary } from "@/utils/api";
import { useAuth } from "./_app";
import Sidebar from "@/components/Sidebar";

export default function CertificationPage() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();
  const [levels, setLevels] = useState([]);
  const [assessment, setAssessment] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) { router.push("/login"); return; }
    Promise.all([getCertificationLevels(), getSummary()]).then(async ([l, summary]) => {
      setLevels(l.levels || []);
      if (summary?.available) {
        const userStats = { average_score: summary.average_score, total_sessions: summary.total_sessions, filler_rate: 0.04, grammar_accuracy: 0.95 };
        const a = await assessCertification(userStats);
        setAssessment(a);
      }
    }).catch(() => {}).finally(() => setLoading(false));
  }, [isAuthenticated]);

  const handleGenerateCert = async (level) => {
    const result = await generateCertificate(user?.id, level, assessment?.current_level?.score || 0.8);
    if (result.certificate_id) {
      alert(`Certificate generated: ${result.certificate_id}`);
    }
  };

  return (
    <div className="flex min-h-screen bg-black text-white">
      <Sidebar onModeChange={() => {}} />
      <main className="flex-1 p-6 overflow-y-auto">
        <h2 className="text-xl font-semibold mb-6">🏅 Communication Certification</h2>
        {loading ? <p className="text-text-secondary">Loading certification data...</p> : (
          <>
            {assessment && (
              <div className="bg-surface border border-accent/30 rounded-lg p-6 mb-6">
                <p className="text-xs text-text-secondary uppercase tracking-wider mb-2">Current Level</p>
                <p className="text-2xl font-bold text-accent">{assessment.current_level?.name || "Not Certified"}</p>
                <div className="mt-2 bg-black rounded-full h-3">
                  <div className="bg-accent h-3 rounded-full" style={{ width: `${assessment.progress_to_next || 0}%` }} />
                </div>
                {assessment.next_level && (
                  <p className="text-sm text-text-secondary mt-2">
                    Next: {assessment.next_level.name} (need {assessment.next_level.min_score * 100}% · gap: {(assessment.next_level.gap * 100).toFixed(0)}%)
                  </p>
                )}
              </div>
            )}
            <div className="grid grid-cols-4 gap-4">
              {levels.map((l, i) => (
                <div key={l.id} className={`bg-surface border rounded-lg p-5 ${assessment?.achieved_levels?.some(al => al.id === l.id) ? "border-accent" : "border-border opacity-70"}`}>
                  <div className="text-3xl mb-2">
                    {l.id === "bronze" ? "🥉" : l.id === "silver" ? "🥈" : l.id === "gold" ? "🥇" : "💎"}
                  </div>
                  <p className="font-medium text-lg">{l.name}</p>
                  <p className="text-xs text-text-secondary mt-1">{l.description}</p>
                  <p className="text-sm mt-2">Min Score: {(l.min_score * 100).toFixed(0)}%</p>
                  <div className="mt-3">
                    {l.requirements.map((req, j) => (
                      <p key={j} className="text-xs text-text-secondary">• {req}</p>
                    ))}
                  </div>
                  {assessment?.achieved_levels?.some(al => al.id === l.id) && (
                    <button onClick={() => handleGenerateCert(l.id)} className="mt-4 w-full px-3 py-2 bg-accent text-black rounded text-sm font-medium hover:bg-accent/90">
                      Generate Certificate
                    </button>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
