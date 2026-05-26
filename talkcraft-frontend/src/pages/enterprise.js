import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { getOrgOverview, getTeamDashboard, getUserGrowth, getEnterpriseFeatures } from "@/utils/api";
import { useAuth } from "./_app";
import Sidebar from "@/components/Sidebar";

export default function EnterprisePage() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();
  const [features, setFeatures] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) { router.push("/login"); return; }
    getEnterpriseFeatures().then(d => setFeatures(d)).catch(() => {}).finally(() => setLoading(false));
  }, [isAuthenticated]);

  return (
    <div className="flex min-h-screen bg-black text-white">
      <Sidebar onModeChange={() => {}} />
      <main className="flex-1 p-6 overflow-y-auto">
        <h2 className="text-xl font-semibold mb-6">🏢 Enterprise Dashboard</h2>
        {loading ? <p className="text-text-secondary">Loading...</p> : (
          <div>
            <div className="bg-surface border border-border rounded-lg p-6 mb-6">
              <p className="text-lg font-medium mb-2">TalkCraft Enterprise v5.0</p>
              <p className="text-text-secondary mb-4">Advanced AI Communication Ecosystem — All features available</p>
              {features?.features && (
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(features.features).map(([key, feat]) => (
                    <div key={key} className="bg-black rounded-lg p-4 border border-border">
                      <div className="flex items-center justify-between mb-2">
                        <p className="font-medium capitalize">{key.replace(/_/g, " ")}</p>
                        <span className={`text-xs px-2 py-0.5 rounded ${feat.enabled ? "bg-green-900/50 text-green-400" : "bg-red-900/50 text-red-400"}`}>
                          {feat.enabled ? "Active" : "Inactive"}
                        </span>
                      </div>
                      {feat.languages && <p className="text-xs text-text-secondary">Languages: {feat.languages.join(", ")}</p>}
                      {feat.avatars && <p className="text-xs text-text-secondary">Avatars: {feat.avatars.join(", ")}</p>}
                      {feat.levels && <p className="text-xs text-text-secondary">Levels: {feat.levels.join(", ")}</p>}
                      {feat.roles && <p className="text-xs text-text-secondary">Roles: {feat.roles}</p>}
                      {feat.categories && <p className="text-xs text-text-secondary">Categories: {feat.categories}</p>}
                      {feat.interview_types && <p className="text-xs text-text-secondary">Interview Types: {feat.interview_types}</p>}
                      {feat.max_participants && <p className="text-xs text-text-secondary">Max per room: {feat.max_participants}</p>}
                      {feat.max_teams && <p className="text-xs text-text-secondary">Max teams: {feat.max_teams}</p>}
                      {feat.scenarios && <p className="text-xs text-text-secondary">Scenarios: {feat.scenarios}</p>}
                      {feat.personas && <p className="text-xs text-text-secondary">Personas: {feat.personas}</p>}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-surface border border-border rounded-lg p-5">
                <p className="text-2xl font-bold text-accent">5</p>
                <p className="text-sm text-text-secondary">Languages Supported</p>
              </div>
              <div className="bg-surface border border-border rounded-lg p-5">
                <p className="text-2xl font-bold text-accent">6</p>
                <p className="text-sm text-text-secondary">AI Avatars</p>
              </div>
              <div className="bg-surface border border-border rounded-lg p-5">
                <p className="text-2xl font-bold text-accent">10</p>
                <p className="text-sm text-text-secondary">Max Room Capacity</p>
              </div>
              <div className="bg-surface border border-border rounded-lg p-5">
                <p className="text-2xl font-bold text-accent">4</p>
                <p className="text-sm text-text-secondary">Certification Levels</p>
              </div>
              <div className="bg-surface border border-border rounded-lg p-5">
                <p className="text-2xl font-bold text-accent">6</p>
                <p className="text-sm text-text-secondary">Role Profiles</p>
              </div>
              <div className="bg-surface border border-border rounded-lg p-5">
                <p className="text-2xl font-bold text-accent">7</p>
                <p className="text-sm text-text-secondary">Benchmark Categories</p>
              </div>
              <div className="bg-surface border border-border rounded-lg p-5">
                <p className="text-2xl font-bold text-accent">5</p>
                <p className="text-sm text-text-secondary">Interview Types</p>
              </div>
              <div className="bg-surface border border-border rounded-lg p-5">
                <p className="text-2xl font-bold text-accent">4</p>
                <p className="text-sm text-text-secondary">Recruiter Personas</p>
              </div>
              <div className="bg-surface border border-border rounded-lg p-5">
                <p className="text-2xl font-bold text-accent">10</p>
                <p className="text-sm text-text-secondary">Training Scenarios</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
