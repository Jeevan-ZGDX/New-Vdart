import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { listRooms, createRoom, joinRoom, leaveRoom, startRoom, endRoom, getRoomAnalytics } from "@/utils/api";
import { useAuth } from "./_app";
import Sidebar from "@/components/Sidebar";

export default function CollaborationPage() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();
  const [rooms, setRooms] = useState([]);
  const [activeRoom, setActiveRoom] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [createName, setCreateName] = useState("");
  const [createType, setCreateType] = useState("mock_interview");
  const [createTopic, setCreateTopic] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) { router.push("/login"); return; }
    refreshRooms();
  }, [isAuthenticated]);

  const refreshRooms = async () => {
    const data = await listRooms();
    setRooms(data.rooms || []);
    setLoading(false);
  };

  const handleCreate = async () => {
    if (!createName) return;
    const result = await createRoom(createName, createType, user?.id || 0, user?.username || "user");
    if (!result.error) {
      setCreateName("");
      refreshRooms();
    }
  };

  const handleJoin = async (roomId) => {
    const result = await joinRoom(roomId, user?.id || 0, user?.username || "user");
    if (!result.error) {
      const room = await getRoom(roomId);
      setActiveRoom(room);
    }
  };

  const handleLeave = async () => {
    if (activeRoom) {
      await leaveRoom(activeRoom.room_id, user?.id || 0);
      setActiveRoom(null);
      setAnalytics(null);
      refreshRooms();
    }
  };

  const handleStart = async () => {
    if (activeRoom) {
      const result = await startRoom(activeRoom.room_id, user?.id || 0);
      if (!result.error) {
        const room = await getRoom(activeRoom.room_id);
        setActiveRoom(room);
      }
    }
  };

  const handleEnd = async () => {
    if (activeRoom) {
      const result = await endRoom(activeRoom.room_id, user?.id || 0);
      if (!result.error) {
        const analysis = await getRoomAnalytics(activeRoom.room_id);
        setAnalytics(analysis);
      }
    }
  };

  const roomTypes = [
    { id: "mock_interview", label: "Mock Interview", icon: "💼" },
    { id: "group_discussion", label: "Group Discussion", icon: "🗣️" },
    { id: "debate", label: "Debate", icon: "⚔️" },
    { id: "presentation", label: "Presentation", icon: "📽️" },
    { id: "casual", label: "Casual Practice", icon: "💬" },
  ];

  return (
    <div className="flex min-h-screen bg-black text-white">
      <Sidebar onModeChange={() => {}} />
      <main className="flex-1 p-6 overflow-y-auto">
        <h2 className="text-xl font-semibold mb-6">👥 Collaborative Sessions</h2>
        {loading ? <p className="text-text-secondary">Loading rooms...</p> : activeRoom ? (
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-medium">{activeRoom.name}</h3>
                <p className="text-xs text-text-secondary">
                  {activeRoom.type} · {activeRoom.participant_count}/{activeRoom.max_participants} participants · {activeRoom.status}
                </p>
              </div>
              <div className="flex gap-2">
                {activeRoom.status === "waiting" && <button onClick={handleStart} className="px-4 py-2 bg-accent text-black rounded font-medium hover:bg-accent/90">Start</button>}
                {activeRoom.status === "active" && <button onClick={handleEnd} className="px-4 py-2 bg-warning text-black rounded font-medium hover:bg-warning/90">End</button>}
                <button onClick={handleLeave} className="px-4 py-2 bg-danger text-white rounded hover:bg-danger/90">Leave</button>
              </div>
            </div>
            {activeRoom.participants?.length > 0 && (
              <div className="bg-surface border border-border rounded-lg p-4 mb-4">
                <p className="text-xs text-text-secondary uppercase tracking-wider mb-2">Participants</p>
                <div className="grid grid-cols-4 gap-3">
                  {activeRoom.participants.map((p, i) => (
                    <div key={i} className="bg-black rounded p-3 text-center">
                      <p className="font-medium">{p.username}</p>
                      <p className="text-xs text-text-secondary">{p.role}</p>
                      {p.is_speaking && <p className="text-xs text-accent mt-1">🔴 Speaking</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {analytics && (
              <div className="bg-surface border border-border rounded-lg p-4">
                <p className="text-accent font-medium mb-3">📊 Session Analytics</p>
                <div className="grid grid-cols-2 gap-4">
                  <div><p className="text-xs text-text-secondary">Total Words</p><p className="text-lg">{analytics.total_words || 0}</p></div>
                  <div><p className="text-xs text-text-secondary">Avg Engagement</p><p className="text-lg">{(analytics.avg_engagement * 100 || 0).toFixed(0)}%</p></div>
                </div>
                {analytics.rankings?.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs text-text-secondary mb-2">Rankings</p>
                    {analytics.rankings.map((r, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm py-1">
                        <span className="text-warning">#{i + 1}</span>
                        <span>{r.username}</span>
                        <span className="text-text-secondary">Score: {(r.score * 100 || 0).toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div>
            <div className="bg-surface border border-border rounded-lg p-4 mb-6">
              <p className="text-text-secondary text-xs uppercase tracking-wider mb-3">Create New Room</p>
              <div className="grid grid-cols-5 gap-2 mb-3">
                {roomTypes.map(rt => (
                  <button key={rt.id} onClick={() => setCreateType(rt.id)}
                    className={`p-3 rounded text-center text-sm border transition-all ${createType === rt.id ? "border-accent bg-accent/10" : "border-border bg-black hover:border-accent/50"}`}>
                    <span className="text-lg">{rt.icon}</span>
                    <p className="text-xs mt-1">{rt.label}</p>
                  </button>
                ))}
              </div>
              <div className="flex gap-3">
                <input value={createName} onChange={e => setCreateName(e.target.value)} placeholder="Room name..." className="flex-1 px-4 py-2 bg-black border border-border rounded text-white focus:outline-none focus:border-accent" />
                <input value={createTopic} onChange={e => setCreateTopic(e.target.value)} placeholder="Topic (optional)..." className="flex-1 px-4 py-2 bg-black border border-border rounded text-white focus:outline-none focus:border-accent" />
                <button onClick={handleCreate} className="px-6 py-2 bg-accent text-black rounded font-medium hover:bg-accent/90">Create Room</button>
              </div>
            </div>
            <p className="text-text-secondary text-xs uppercase tracking-wider mb-3">Available Rooms ({rooms.length})</p>
            {rooms.length === 0 ? (
              <p className="text-text-secondary">No rooms available. Create one to get started!</p>
            ) : (
              <div className="space-y-3">
                {rooms.map(room => (
                  <div key={room.room_id} className="bg-surface border border-border rounded-lg p-4 flex items-center justify-between">
                    <div>
                      <p className="font-medium">{room.name}</p>
                      <p className="text-xs text-text-secondary">{room.type} · {room.participant_count}/{room.max_participants} · {room.status}</p>
                      {room.topic && <p className="text-xs text-text-secondary mt-1">Topic: {room.topic}</p>}
                    </div>
                    <button onClick={() => handleJoin(room.room_id)} className="px-4 py-2 bg-accent text-black rounded text-sm font-medium hover:bg-accent/90">Join</button>
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
