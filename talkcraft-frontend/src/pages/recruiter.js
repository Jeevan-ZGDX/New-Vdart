import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { getInterviewTypes, getRecruiterPersonas, getInterviewQuestions, evaluateInterviewResponse } from "@/utils/api";
import { useAuth } from "./_app";
import Sidebar from "@/components/Sidebar";

export default function RecruiterPage() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();
  const [types, setTypes] = useState([]);
  const [personas, setPersonas] = useState([]);
  const [selectedType, setSelectedType] = useState("general");
  const [selectedPersona, setSelectedPersona] = useState("professional");
  const [questions, setQuestions] = useState([]);
  const [currentQ, setCurrentQ] = useState(0);
  const [response, setResponse] = useState("");
  const [evaluations, setEvaluations] = useState([]);
  const [started, setStarted] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) { router.push("/login"); return; }
    Promise.all([getInterviewTypes(), getRecruiterPersonas()]).then(([t, p]) => {
      setTypes(t.interview_types || []);
      setPersonas(p.personas || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [isAuthenticated]);

  const handleStart = async () => {
    const qs = await getInterviewQuestions(selectedType, 5);
    setQuestions(qs.questions || []);
    setCurrentQ(0);
    setEvaluations([]);
    setStarted(true);
  };

  const handleSubmit = async () => {
    if (!response.trim()) return;
    const q = questions[currentQ];
    const metrics = { clarity_score: 0.7, confidence_score: 0.6, filler_rate: 0.04, avg_wpm: 150 };
    const evalResult = await evaluateInterviewResponse(response, q, metrics);
    setEvaluations(prev => [...prev, evalResult]);
    setResponse("");
    if (currentQ < questions.length - 1) {
      setCurrentQ(prev => prev + 1);
    }
  };

  return (
    <div className="flex min-h-screen bg-black text-white">
      <Sidebar onModeChange={() => {}} />
      <main className="flex-1 p-6 overflow-y-auto">
        <h2 className="text-xl font-semibold mb-6">💼 Recruiter Interview Simulator</h2>
        {loading ? <p className="text-text-secondary">Loading...</p> : !started ? (
          <div>
            <div className="mb-6">
              <p className="text-text-secondary text-xs uppercase tracking-wider mb-3">Interview Type</p>
              <div className="grid grid-cols-5 gap-3">
                {types.map(t => (
                  <button key={t.id} onClick={() => setSelectedType(t.id)}
                    className={`p-4 rounded-lg border text-center transition-all ${selectedType === t.id ? "border-accent bg-accent/10" : "border-border bg-surface hover:border-accent/50"}`}>
                    <p className="font-medium text-sm">{t.label}</p>
                    <p className="text-xs text-text-secondary mt-1">{t.difficulty}</p>
                  </button>
                ))}
              </div>
            </div>
            <div className="mb-6">
              <p className="text-text-secondary text-xs uppercase tracking-wider mb-3">Recruiter Persona</p>
              <div className="grid grid-cols-4 gap-3">
                {personas.map(p => (
                  <button key={p.id} onClick={() => setSelectedPersona(p.id)}
                    className={`p-4 rounded-lg border text-center transition-all ${selectedPersona === p.id ? "border-accent bg-accent/10" : "border-border bg-surface hover:border-accent/50"}`}>
                    <p className="font-medium text-sm">{p.name}</p>
                    <p className="text-xs text-text-secondary mt-1">{p.style}</p>
                  </button>
                ))}
              </div>
            </div>
            <button onClick={handleStart} className="px-8 py-3 bg-accent text-black rounded-lg font-medium hover:bg-accent/90 text-lg">Start Interview Simulation</button>
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-text-secondary">Question {currentQ + 1} of {questions.length}</p>
              <button onClick={() => setStarted(false)} className="px-3 py-1 text-sm bg-surface border border-border rounded text-text-secondary hover:text-white">End Simulation</button>
            </div>
            <div className="bg-surface border border-accent/30 rounded-lg p-6 mb-4">
              <p className="text-accent font-medium mb-2">Interviewer:</p>
              <p className="text-lg">{questions[currentQ]}</p>
            </div>
            <textarea value={response} onChange={e => setResponse(e.target.value)} rows={4}
              className="w-full px-4 py-3 bg-black border border-border rounded text-white focus:outline-none focus:border-accent mb-3" placeholder="Type your answer..." />
            <button onClick={handleSubmit} className="px-6 py-2 bg-accent text-black rounded font-medium hover:bg-accent/90">Submit Response</button>
            {evaluations.length > 0 && (
              <div className="mt-6 space-y-3">
                <p className="text-text-secondary text-xs uppercase tracking-wider">Evaluations</p>
                {evaluations.map((ev, i) => (
                  <div key={i} className="bg-surface border border-border rounded-lg p-4">
                    <p className="text-xs text-text-secondary mb-1">Q: {ev.question}</p>
                    <p className="text-sm">Score: {(ev.composite_score * 100).toFixed(0)}% · Clarity: {(ev.clarity_score * 100).toFixed(0)}% · Confidence: {(ev.confidence_score * 100).toFixed(0)}%</p>
                    <p className="text-xs text-text-secondary mt-1">Quality: {ev.response_quality} · STAR: {ev.star_structure_detected ? "✅" : "❌"} · Words: {ev.response_length}</p>
                    {ev.feedback?.length > 0 && ev.feedback.map((f, j) => (
                      <p key={j} className="text-xs text-warning mt-1">💡 {f}</p>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
