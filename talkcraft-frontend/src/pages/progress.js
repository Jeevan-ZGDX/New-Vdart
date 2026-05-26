import React, { useEffect, useState, useRef } from "react";
import { useRouter } from "next/router";
import { getSummary, getTrends, getWeeklyProgress, getWeaknesses } from "@/utils/api";
import { useAuth } from "./_app";
import Sidebar from "@/components/Sidebar";
import MetricCard from "@/components/MetricCard";
import { Chart, registerables } from "chart.js";
Chart.register(...registerables);

function TrendChart({ data, metric }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || !data) return;
    if (chartRef.current) chartRef.current.destroy();

    const values = data.values || [];
    const isWpm = metric === "average_wpm";
    const ctx = canvasRef.current.getContext("2d");

    chartRef.current = new Chart(ctx, {
      type: "line",
      data: {
        labels: values.map(v => {
          const d = new Date(v.date);
          return `${d.getMonth()+1}/${d.getDate()}`;
        }),
        datasets: [{
          label: metric.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
          data: values.map(v => isWpm ? v.value : v.value * 100),
          borderColor: "#4CAF50",
          backgroundColor: "rgba(76, 175, 80, 0.1)",
          fill: true,
          tension: 0.3,
          pointRadius: 3,
          pointBackgroundColor: "#4CAF50",
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: {
            ticks: { color: "#888", maxTicksLimit: 10 },
            grid: { color: "rgba(255,255,255,0.05)" },
          },
          y: {
            ticks: { color: "#888" },
            grid: { color: "rgba(255,255,255,0.05)" },
            title: {
              display: true,
              text: isWpm ? "WPM" : "Score %",
              color: "#888",
            },
          },
        },
      },
    });

    return () => {
      if (chartRef.current) chartRef.current.destroy();
    };
  }, [data, metric]);

  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <p className="text-text-secondary text-xs uppercase tracking-wider mb-2">
        {metric.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
        {data && (
          <span className={`ml-2 text-xs ${
            data.direction === "improving" ? "text-accent" :
            data.direction === "declining" ? "text-danger" : "text-warning"
          }`}>
            ({data.direction})
          </span>
        )}
      </p>
      <div className="h-48">
        {data && data.values && data.values.length > 0 ? (
          <canvas ref={canvasRef} />
        ) : (
          <div className="flex items-center justify-center h-full text-text-secondary text-sm">
            Not enough data
          </div>
        )}
      </div>
    </div>
  );
}

export default function ProgressPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState(null);
  const [weeklyProgress, setWeeklyProgress] = useState([]);
  const [weaknesses, setWeaknesses] = useState(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    loadData();
  }, [isAuthenticated, days]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [s, t, w, wk] = await Promise.all([
        getSummary().catch(() => null),
        getTrends(days).catch(() => null),
        getWeaknesses().catch(() => null),
        getWeeklyProgress().catch(() => []),
      ]);
      setSummary(s);
      setTrends(t);
      setWeaknesses(w);
      setWeeklyProgress(Array.isArray(wk) ? wk : []);
    } catch {}
    setLoading(false);
  };

  return (
    <div className="flex min-h-screen bg-black text-white">
      <Sidebar onModeChange={() => {}} />
      <main className="flex-1 p-6 overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">📈 Progress & Trends</h2>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-3 py-2 bg-surface border border-border rounded text-sm text-white focus:outline-none focus:border-accent"
          >
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
            <option value={60}>60 days</option>
            <option value={90}>90 days</option>
          </select>
        </div>

        {loading ? (
          <p className="text-text-secondary">Loading progress data...</p>
        ) : (
          <>
            {summary && summary.available && (
              <div className="grid grid-cols-4 gap-4 mb-6">
                <MetricCard label="Current Score" value={`${((summary.latest_score || 0) * 100).toFixed(0)}%`} color="#4CAF50" sub={summary.last_session_mode?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} />
                <MetricCard label="Average Score" value={`${((summary.average_score || 0) * 100).toFixed(0)}%`} color="#2196F3" />
                <MetricCard label="Total Sessions" value={summary.total_sessions || 0} color="#FF9800" />
                <MetricCard label="Practice Time" value={`${summary.total_practice_minutes || 0}m`} color="#9C27B0" />
              </div>
            )}

            {trends && trends.available && (
              <div>
                <h3 className="text-lg font-medium mb-4">Metric Trends</h3>
                <div className="grid grid-cols-2 gap-4 mb-6">
                  {Object.entries(trends.trends || {}).slice(0, 6).map(([metric, data]) => (
                    <TrendChart key={metric} data={data} metric={metric} />
                  ))}
                </div>

                {trends.direction_summary && (
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    {trends.direction_summary.improving?.length > 0 && (
                      <div className="bg-surface border border-accent/30 rounded-lg p-4">
                        <p className="text-xs text-text-secondary uppercase tracking-wider mb-2">✅ Improving</p>
                        {trends.direction_summary.improving.slice(0, 3).map((m, i) => (
                          <p key={i} className="text-sm text-accent">+{m.change?.toFixed(1)}% {m.label}</p>
                        ))}
                      </div>
                    )}
                    {trends.direction_summary.declining?.length > 0 && (
                      <div className="bg-surface border border-danger/30 rounded-lg p-4">
                        <p className="text-xs text-text-secondary uppercase tracking-wider mb-2">📉 Needs Attention</p>
                        {trends.direction_summary.declining.slice(0, 3).map((m, i) => (
                          <p key={i} className="text-sm text-danger">{m.change?.toFixed(1)}% {m.label}</p>
                        ))}
                      </div>
                    )}
                    {trends.direction_summary.stable?.length > 0 && (
                      <div className="bg-surface border border-border rounded-lg p-4">
                        <p className="text-xs text-text-secondary uppercase tracking-wider mb-2">➡️ Stable</p>
                        {trends.direction_summary.stable.slice(0, 3).map((m, i) => (
                          <p key={i} className="text-sm text-text-secondary">{m.label}</p>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {weeklyProgress.length > 0 && (
                  <div className="bg-surface border border-border rounded-lg p-4">
                    <p className="text-text-secondary text-xs uppercase tracking-wider mb-3">Weekly Overview</p>
                    <div className="space-y-2">
                      {weeklyProgress.map((w, i) => (
                        <div key={i} className="flex items-center justify-between p-2 bg-black rounded">
                          <span className="text-sm w-24">{w.week}</span>
                          <div className="flex-1 mx-4 bg-black rounded-full h-2">
                            <div className="bg-accent h-2 rounded-full" style={{ width: `${(w.avg_score || 0) * 100}%` }} />
                          </div>
                          <div className="flex gap-4 text-xs text-text-secondary">
                            <span>{w.sessions} sessions</span>
                            <span>{(w.total_minutes || 0).toFixed(0)}m</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {!trends?.available && (
              <div className="bg-surface border border-border rounded-lg p-6 text-center">
                <p className="text-text-secondary mb-2">Complete more sessions to see your progress trends</p>
                <p className="text-xs text-text-secondary">Data will appear after 3+ completed practice sessions</p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
