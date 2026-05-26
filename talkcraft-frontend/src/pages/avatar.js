import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { getAvatars, createAvatar, setAvatarExpression, getAvatarFrame } from "@/utils/api";
import { useAuth } from "./_app";
import Sidebar from "@/components/Sidebar";

export default function AvatarPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const [avatars, setAvatars] = useState([]);
  const [activeAvatar, setActiveAvatar] = useState(null);
  const [expression, setExpression] = useState("neutral");
  const [frame, setFrame] = useState(null);
  const [loading, setLoading] = useState(true);

  const expressionList = ["neutral", "smiling", "attentive", "thoughtful", "surprised", "nodding", "listening", "observing", "speaking"];

  useEffect(() => {
    if (!isAuthenticated) { router.push("/login"); return; }
    getAvatars().then(d => setAvatars(d.avatars || [])).catch(() => {}).finally(() => setLoading(false));
  }, [isAuthenticated]);

  const handleSelect = async (avatarId) => {
    const result = await createAvatar(avatarId);
    if (!result.error) {
      setActiveAvatar(result);
      setExpression(result.expression || "neutral");
    }
  };

  const handleExpression = async (expr) => {
    setExpression(expr);
    if (activeAvatar) {
      await setAvatarExpression(activeAvatar.id, expr);
      const f = await getAvatarFrame(activeAvatar.id);
      setFrame(f);
    }
  };

  return (
    <div className="flex min-h-screen bg-black text-white">
      <Sidebar onModeChange={() => {}} />
      <main className="flex-1 p-6 overflow-y-auto">
        <h2 className="text-xl font-semibold mb-6">🤖 AI Avatars</h2>
        {loading ? <p className="text-text-secondary">Loading avatars...</p> : (
          <>
            <div className="grid grid-cols-3 gap-4 mb-6">
              {avatars.map(a => (
                <button key={a.id} onClick={() => handleSelect(a.id)}
                  className={`p-6 rounded-lg border text-center transition-all ${activeAvatar?.id === a.id ? "border-accent bg-accent/10" : "border-border bg-surface hover:border-accent/50"}`}>
                  <div className="w-16 h-16 rounded-full mx-auto mb-3 flex items-center justify-center text-2xl" style={{ backgroundColor: a.color + "30", border: `2px solid ${a.color}` }}>
                    {a.role === "communication_coach" ? "🎯" : a.role === "interviewer" ? "💼" : a.role === "audience" ? "👥" : a.role === "debate_opponent" ? "⚔️" : a.role === "evaluator" ? "📋" : "💬"}
                  </div>
                  <p className="font-medium">{a.name}</p>
                  <p className="text-xs text-text-secondary">{a.role.replace(/_/g, " ")}</p>
                  <p className="text-xs text-text-secondary mt-1">{a.personality}</p>
                </button>
              ))}
            </div>
            {activeAvatar && (
              <div className="bg-surface border border-border rounded-lg p-6">
                <div className="flex items-center gap-6 mb-6">
                  <div className="w-24 h-24 rounded-full flex items-center justify-center text-3xl" style={{ backgroundColor: activeAvatar.color + "20", border: `3px solid ${activeAvatar.color}` }}>
                    {activeAvatar.role === "communication_coach" ? "🎯" : activeAvatar.role === "interviewer" ? "💼" : activeAvatar.role === "audience" ? "👥" : activeAvatar.role === "debate_opponent" ? "⚔️" : activeAvatar.role === "evaluator" ? "📋" : "💬"}
                  </div>
                  <div>
                    <h3 className="text-xl font-medium">{activeAvatar.name}</h3>
                    <p className="text-text-secondary">Role: {activeAvatar.role.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}</p>
                    <p className="text-text-secondary">Personality: {activeAvatar.personality}</p>
                    <p className="text-text-secondary">Expression: {activeAvatar.expression || "neutral"}</p>
                  </div>
                </div>
                <div className="mb-4">
                  <p className="text-xs text-text-secondary uppercase tracking-wider mb-2">Expressions</p>
                  <div className="flex flex-wrap gap-2">
                    {expressionList.map(expr => (
                      <button key={expr} onClick={() => handleExpression(expr)}
                        className={`px-3 py-1.5 rounded text-sm border transition-all ${expression === expr ? "border-accent bg-accent/20 text-accent" : "border-border bg-black text-text-secondary hover:text-white"}`}>
                        {expr}
                      </button>
                    ))}
                  </div>
                </div>
                {frame && (
                  <div className="bg-black rounded-lg p-4">
                    <p className="text-xs text-text-secondary mb-2">Animation Frame</p>
                    <pre className="text-xs text-accent">{JSON.stringify(frame.features, null, 2)}</pre>
                  </div>
                )}
              </div>
            )}
            {!activeAvatar && (
              <p className="text-text-secondary text-center py-8">Select an avatar above to interact with it</p>
            )}
          </>
        )}
      </main>
    </div>
  );
}
