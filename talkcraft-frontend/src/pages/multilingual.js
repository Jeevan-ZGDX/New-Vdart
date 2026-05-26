import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { getLanguages, startMultilingualSession, processMultilingualText, endMultilingualSession } from "@/utils/api";
import { useAuth } from "./_app";
import Sidebar from "@/components/Sidebar";

export default function MultilingualPage() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();
  const [languages, setLanguages] = useState([]);
  const [selectedLang, setSelectedLang] = useState("en");
  const [session, setSession] = useState(null);
  const [inputText, setInputText] = useState("");
  const [transcript, setTranscript] = useState([]);
  const [feedback, setFeedback] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) { router.push("/login"); return; }
    getLanguages().then(d => setLanguages(d.languages || [])).catch(() => {}).finally(() => setLoading(false));
  }, [isAuthenticated]);

  const handleStart = async () => {
    const result = await startMultilingualSession(user.id, selectedLang);
    if (result.session_started) {
      setSession(result);
      setTranscript([]);
      setFeedback([]);
    }
  };

  const handleSend = async () => {
    if (!inputText.trim() || !session) return;
    const result = await processMultilingualText(user.id, inputText);
    setTranscript(prev => [...prev, { role: "user", text: inputText }]);
    if (result.feedback) {
      setFeedback(prev => [...prev, result.feedback]);
    }
    setInputText("");
  };

  const handleEnd = async () => {
    const result = await endMultilingualSession(user.id);
    setSession(null);
  };

  return (
    <div className="flex min-h-screen bg-black text-white">
      <Sidebar onModeChange={() => {}} />
      <main className="flex-1 p-6 overflow-y-auto">
        <h2 className="text-xl font-semibold mb-6">🌐 Multilingual Coaching</h2>
        {loading ? <p className="text-text-secondary">Loading languages...</p> : (
          <>
            <div className="grid grid-cols-5 gap-3 mb-6">
              {languages.map(lang => (
                <button key={lang.code} onClick={() => setSelectedLang(lang.code)}
                  className={`p-4 rounded-lg border text-center transition-all ${selectedLang === lang.code ? "border-accent bg-accent/10" : "border-border bg-surface hover:border-accent/50"}`}>
                  <p className="text-lg font-bold">{lang.native_name}</p>
                  <p className="text-xs text-text-secondary">{lang.name}</p>
                  <p className="text-xs text-text-secondary mt-1">{lang.difficulty}</p>
                </button>
              ))}
            </div>
            {!session ? (
              <button onClick={handleStart} className="px-6 py-3 bg-accent text-black rounded-lg font-medium hover:bg-accent/90">
                Start {languages.find(l => l.code === selectedLang)?.name || "Language"} Session
              </button>
            ) : (
              <div>
                <div className="bg-surface border border-border rounded-lg p-4 mb-4">
                  <p className="text-accent font-medium">Active Session: {session.language}</p>
                  <p className="text-xs text-text-secondary mt-1">{session.greeting}</p>
                </div>
                <div className="mb-4 space-y-2 max-h-60 overflow-y-auto">
                  {transcript.map((t, i) => (
                    <div key={i} className={`p-3 rounded ${t.role === "user" ? "bg-black border border-border ml-8" : "bg-surface border border-accent/30 mr-8"}`}>
                      <p className="text-xs text-text-secondary mb-1">{t.role === "user" ? "You" : "Coach"}</p>
                      <p className="text-sm">{t.text}</p>
                    </div>
                  ))}
                </div>
                {feedback.length > 0 && (
                  <div className="bg-surface border border-border rounded-lg p-4 mb-4">
                    <p className="text-xs text-text-secondary uppercase tracking-wider mb-2">Feedback</p>
                    {feedback.slice(-3).map((f, i) => (
                      <p key={i} className={`text-sm mb-1 ${f.type === "positive" ? "text-accent" : f.type === "constructive" ? "text-warning" : "text-text-secondary"}`}>
                        {f.message}
                      </p>
                    ))}
                  </div>
                )}
                <div className="flex gap-3">
                  <input value={inputText} onChange={e => setInputText(e.target.value)} onKeyDown={e => e.key === "Enter" && handleSend()}
                    className="flex-1 px-4 py-2 bg-black border border-border rounded text-white focus:outline-none focus:border-accent" placeholder="Type or speak your practice text..." />
                  <button onClick={handleSend} className="px-4 py-2 bg-accent text-black rounded font-medium hover:bg-accent/90">Send</button>
                  <button onClick={handleEnd} className="px-4 py-2 bg-danger text-white rounded hover:bg-danger/90">End Session</button>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
