import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { getAchievements, checkAchievements } from "@/utils/api";
import { useAuth } from "./_app";
import Sidebar from "@/components/Sidebar";

export default function AchievementsPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);

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
      const result = await getAchievements();
      setData(result);
    } catch {}
    setLoading(false);
  };

  const handleCheck = async () => {
    setChecking(true);
    try {
      const result = await checkAchievements();
      if (result.new_achievements?.length > 0) {
        alert(`🏆 New achievements unlocked: ${result.new_achievements.map(a => a.title).join(", ")}`);
        loadData();
      } else {
        alert("No new achievements. Keep practicing!");
      }
    } catch {}
    setChecking(false);
  };

  const badgeCategories = {
    milestone: "🎯 Milestones",
    time: "⏱️ Time Invested",
    streak: "🔥 Consistency",
    skill: "💪 Skill Mastery",
    excellence: "🏅 Excellence",
    improvement: "📈 Improvement",
    exploration: "🌍 Exploration",
    mode_specific: "🎭 Mode Specific",
  };

  return (
    <div className="flex min-h-screen bg-black text-white">
      <Sidebar onModeChange={() => {}} />
      <main className="flex-1 p-6 overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">🏆 Achievements</h2>
          <button
            onClick={handleCheck}
            disabled={checking}
            className="px-4 py-2 bg-accent text-black text-sm font-medium rounded hover:bg-accent/90 transition-colors disabled:opacity-50"
          >
            {checking ? "Checking..." : "🔍 Check for New"}
          </button>
        </div>

        {loading ? (
          <p className="text-text-secondary">Loading achievements...</p>
        ) : data ? (
          <>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-surface border border-border rounded-lg p-4 text-center">
                <p className="text-3xl font-bold text-accent">{data.total_unlocked}</p>
                <p className="text-xs text-text-secondary mt-1">Unlocked</p>
              </div>
              <div className="bg-surface border border-border rounded-lg p-4 text-center">
                <p className="text-3xl font-bold">{data.total_available}</p>
                <p className="text-xs text-text-secondary mt-1">Total Available</p>
              </div>
              <div className="bg-surface border border-border rounded-lg p-4 text-center">
                <p className="text-3xl font-bold text-warning">{data.progress_pct}%</p>
                <p className="text-xs text-text-secondary mt-1">Complete</p>
              </div>
            </div>

            <div className="bg-black rounded-full h-3 mb-6">
              <div className="bg-accent h-3 rounded-full transition-all" style={{ width: `${data.progress_pct}%` }} />
            </div>

            {data.categories && (
              <div className="grid grid-cols-4 gap-3 mb-6">
                {Object.entries(data.categories).map(([cat, info]) => (
                  <div key={cat} className="bg-surface border border-border rounded-lg p-3 text-center">
                    <p className="text-xs text-text-secondary">{cat.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</p>
                    <p className="text-lg font-bold mt-1">{info.unlocked}/{info.total}</p>
                    <div className="bg-black rounded-full h-1.5 mt-2">
                      <div className="bg-accent h-1.5 rounded-full" style={{ width: `${(info.unlocked / Math.max(1, info.total)) * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {data.badges && (
              <div>
                {Object.entries(badgeCategories).map(([catKey, catLabel]) => {
                  const catBadges = data.badges.filter(b => b.category === catKey);
                  if (catBadges.length === 0) return null;
                  return (
                    <div key={catKey} className="mb-6">
                      <h3 className="text-sm font-medium text-text-secondary mb-3">{catLabel}</h3>
                      <div className="grid grid-cols-4 gap-3">
                        {catBadges.map((badge, i) => (
                          <div
                            key={i}
                            className={`p-4 rounded-lg border transition-all ${
                              badge.unlocked
                                ? "bg-surface border-accent/30 hover:border-accent"
                                : "bg-black border-border opacity-60 hover:opacity-80"
                            }`}
                          >
                            <div className="text-2xl mb-2">
                              {badge.unlocked ? "🏆" : "🔒"}
                            </div>
                            <p className="font-medium text-sm">{badge.title}</p>
                            <p className="text-xs text-text-secondary mt-1">{badge.description}</p>
                            {badge.unlocked && badge.unlocked_at && (
                              <p className="text-xs text-accent mt-2">
                                {new Date(badge.unlocked_at).toLocaleDateString()}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        ) : (
          <div className="bg-surface border border-border rounded-lg p-6 text-center">
            <p className="text-text-secondary">Unable to load achievements</p>
          </div>
        )}
      </main>
    </div>
  );
}
