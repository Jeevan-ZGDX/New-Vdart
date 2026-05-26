import React from "react";

export default function AchievementCard({ achievements }) {
  if (!achievements) {
    return (
      <div className="bg-surface border border-border rounded-lg p-6">
        <p className="text-text-secondary text-xs uppercase tracking-wider mb-4">Achievements</p>
        <p className="text-text-secondary">Login to track achievements</p>
      </div>
    );
  }

  const { total_unlocked = 0, total_available = 0, recent_unlocked = [], badges = [], progress_pct = 0 } = achievements;

  return (
    <div className="bg-surface border border-border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <p className="text-text-secondary text-xs uppercase tracking-wider">Achievements</p>
        <span className="text-sm text-accent">{total_unlocked}/{total_available}</span>
      </div>

      <div className="bg-black rounded-full h-2 mb-4">
        <div
          className="bg-accent h-2 rounded-full transition-all"
          style={{ width: `${progress_pct}%` }}
        />
      </div>

      {recent_unlocked && recent_unlocked.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-text-secondary mb-2">Recently Unlocked</p>
          <div className="space-y-2">
            {recent_unlocked.map((ach, i) => (
              <div key={i} className="flex items-center gap-3 p-2 bg-black rounded">
                <span className="text-lg">🏆</span>
                <div>
                  <p className="text-sm font-medium">{ach.title}</p>
                  <p className="text-xs text-text-secondary">{ach.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {badges && badges.length > 0 && (
        <div>
          <p className="text-xs text-text-secondary mb-2">All Badges</p>
          <div className="grid grid-cols-4 gap-2">
            {badges.slice(0, 12).map((badge, i) => (
              <div
                key={i}
                className={`p-2 rounded text-center text-xs transition-colors ${
                  badge.unlocked
                    ? "bg-accent/10 border border-accent/30"
                    : "bg-black border border-border opacity-50"
                }`}
                title={badge.description}
              >
                <div className="text-lg mb-1">
                  {badge.unlocked ? "🏆" : "🔒"}
                </div>
                <p className="text-[10px] leading-tight">{badge.title}</p>
              </div>
            ))}
          </div>
          {badges.length > 12 && (
            <p className="text-xs text-text-secondary mt-2">
              +{badges.length - 12} more badges
            </p>
          )}
        </div>
      )}

      {!badges || badges.length === 0 && (
        <p className="text-text-secondary text-sm">
          Complete sessions to unlock achievements and track your progress!
        </p>
      )}
    </div>
  );
}
