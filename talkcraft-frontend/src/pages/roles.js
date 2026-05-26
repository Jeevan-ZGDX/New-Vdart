import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { getTrainingRoles, getTrainingRole } from "@/utils/api";
import { useAuth } from "./_app";
import Sidebar from "@/components/Sidebar";

export default function RolesPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const [roles, setRoles] = useState([]);
  const [activeRole, setActiveRole] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) { router.push("/login"); return; }
    getTrainingRoles().then(d => setRoles(d.roles || [])).catch(() => {}).finally(() => setLoading(false));
  }, [isAuthenticated]);

  const handleSelect = async (roleId) => {
    const data = await getTrainingRole(roleId);
    setActiveRole(data);
  };

  return (
    <div className="flex min-h-screen bg-black text-white">
      <Sidebar onModeChange={() => {}} />
      <main className="flex-1 p-6 overflow-y-auto">
        <h2 className="text-xl font-semibold mb-6">👔 Role-Specific Training</h2>
        {loading ? <p className="text-text-secondary">Loading roles...</p> : (
          <>
            <div className="grid grid-cols-3 gap-4 mb-6">
              {roles.map(r => (
                <button key={r.id} onClick={() => handleSelect(r.id)}
                  className={`p-5 rounded-lg border text-left transition-all ${activeRole?.id === r.id ? "border-accent bg-accent/10" : "border-border bg-surface hover:border-accent/50"}`}>
                  <p className="font-medium text-lg">{r.label}</p>
                  <p className="text-sm text-text-secondary mt-1">{r.description}</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {r.focus_areas?.map((fa, i) => (
                      <span key={i} className="text-xs px-2 py-0.5 bg-black border border-border rounded">{fa.replace(/_/g, " ")}</span>
                    ))}
                  </div>
                </button>
              ))}
            </div>
            {activeRole && (
              <div className="bg-surface border border-border rounded-lg p-6">
                <h3 className="text-lg font-medium mb-2">{activeRole.label}</h3>
                <p className="text-text-secondary mb-4">{activeRole.description}</p>
                <p className="text-text-secondary text-xs uppercase tracking-wider mb-3">Practice Scenarios</p>
                {activeRole.scenarios?.length > 0 ? (
                  <div className="space-y-3">
                    {activeRole.scenarios.map((s, i) => (
                      <div key={i} className="bg-black rounded-lg p-4 border border-border">
                        <div className="flex items-center justify-between">
                          <p className="font-medium">{s.title}</p>
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            s.difficulty === "beginner" ? "bg-green-900/50 text-green-400" :
                            s.difficulty === "intermediate" ? "bg-yellow-900/50 text-yellow-400" :
                            "bg-red-900/50 text-red-400"
                          }`}>{s.difficulty}</span>
                        </div>
                        <p className="text-sm text-text-secondary mt-1">{s.description}</p>
                        <p className="text-xs text-text-secondary mt-1">{s.duration_minutes} min</p>
                      </div>
                    ))}
                  </div>
                ) : <p className="text-text-secondary">No scenarios defined</p>}
                <div className="mt-4">
                  <p className="text-text-secondary text-xs uppercase tracking-wider mb-2">System Prompt</p>
                  <pre className="text-xs text-text-secondary bg-black rounded p-3 max-h-32 overflow-y-auto">{activeRole.system_prompt}</pre>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
