const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const COACH_URL = process.env.NEXT_PUBLIC_COACH_URL || "http://localhost:8004";
const VISION_URL = process.env.NEXT_PUBLIC_VISION_URL || "http://localhost:8765";

function getToken() {
  if (typeof window !== "undefined") {
    return localStorage.getItem("talkcraft_token");
  }
  return null;
}

async function authFetch(url, options = {}) {
  const token = getToken();
  const headers = { ...options.headers };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(url, { ...options, headers });
  return res;
}

// Speech API
export async function startMic() {
  const res = await fetch(`${API_URL}/start-mic`, { method: "POST" });
  return res.json();
}

export async function uploadFile(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/start-file`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function stopEngine() {
  const res = await fetch(`${API_URL}/stop`, { method: "POST" });
  return res.json();
}

export async function getState() {
  const res = await fetch(`${API_URL}/state`);
  return res.json();
}

// Auth API
export async function login(username, password) {
  const res = await authFetch(`${COACH_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return res.json();
}

export async function register(username, email, password, displayName) {
  const res = await authFetch(`${COACH_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username,
      email,
      password,
      display_name: displayName,
    }),
  });
  return res.json();
}

export async function getProfile() {
  const res = await authFetch(`${COACH_URL}/api/auth/me`);
  return res.json();
}

// Coaching API
export async function getDashboardOverview() {
  const res = await authFetch(`${COACH_URL}/api/dashboard/overview`);
  return res.json();
}

export async function getCoachingFocus() {
  const res = await authFetch(`${COACH_URL}/api/coaching/focus`);
  return res.json();
}

export async function getImprovementPlan() {
  const res = await authFetch(`${COACH_URL}/api/coaching/plan`);
  return res.json();
}

export async function generatePlan() {
  const res = await authFetch(`${COACH_URL}/api/coaching/plan/generate`, {
    method: "POST",
  });
  return res.json();
}

export async function getRecommendations() {
  const res = await authFetch(`${COACH_URL}/api/coaching/recommendations`);
  return res.json();
}

export async function generateRecommendations() {
  const res = await authFetch(`${COACH_URL}/api/coaching/recommendations/generate`, {
    method: "POST",
  });
  return res.json();
}

export async function getAchievements() {
  const res = await authFetch(`${COACH_URL}/api/achievements`);
  return res.json();
}

export async function checkAchievements() {
  const res = await authFetch(`${COACH_URL}/api/achievements/check`, {
    method: "POST",
  });
  return res.json();
}

export async function getSessions(limit = 20) {
  const res = await authFetch(`${COACH_URL}/api/analytics/sessions?limit=${limit}`);
  return res.json();
}

export async function getWeeklyProgress() {
  const res = await authFetch(`${COACH_URL}/api/analytics/weekly-progress`);
  return res.json();
}

export async function getTrends(days = 30) {
  const res = await authFetch(`${COACH_URL}/api/analytics/trends?days=${days}`);
  return res.json();
}

export async function getWeaknesses() {
  const res = await authFetch(`${COACH_URL}/api/analytics/weaknesses`);
  return res.json();
}

export async function getSummary() {
  const res = await authFetch(`${COACH_URL}/api/analytics/summary`);
  return res.json();
}

export async function createSession(sessionData) {
  const res = await authFetch(`${COACH_URL}/api/sessions/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(sessionData),
  });
  return res.json();
}

export async function getDifficulty() {
  const res = await authFetch(`${COACH_URL}/api/coaching/difficulty`);
  return res.json();
}

export async function getLearningPaths() {
  const res = await authFetch(`${COACH_URL}/api/coaching/paths`);
  return res.json();
}

// === Phase 5: Enterprise API ===
const ENTERPRISE_URL = process.env.NEXT_PUBLIC_ENTERPRISE_URL || "http://localhost:8005";

async function enterpriseFetch(path, options = {}) {
  const res = await fetch(`${ENTERPRISE_URL}${path}`, options);
  return res.json();
}

// Multilingual
export async function getLanguages() {
  return enterpriseFetch("/api/multilingual/languages");
}

export async function startMultilingualSession(userId, language = "en") {
  return enterpriseFetch(`/api/multilingual/session/start?user_id=${userId}&language=${language}`, { method: "POST" });
}

export async function processMultilingualText(userId, text) {
  return enterpriseFetch(`/api/multilingual/session/process?user_id=${userId}&text=${encodeURIComponent(text)}`, { method: "POST" });
}

export async function endMultilingualSession(userId) {
  return enterpriseFetch(`/api/multilingual/session/end?user_id=${userId}`, { method: "POST" });
}

// Avatars
export async function getAvatars() {
  return enterpriseFetch("/api/avatars");
}

export async function createAvatar(avatarId, customName = null) {
  let url = `/api/avatars/create?avatar_id=${avatarId}`;
  if (customName) url += `&custom_name=${encodeURIComponent(customName)}`;
  return enterpriseFetch(url, { method: "POST" });
}

export async function setAvatarExpression(avatarId, expression) {
  return enterpriseFetch(`/api/avatars/${avatarId}/expression?expression=${expression}`, { method: "POST" });
}

export async function getAvatarFrame(avatarId) {
  return enterpriseFetch(`/api/avatars/${avatarId}/frame`);
}

// Collaboration
export async function createRoom(name, roomType = "mock_interview", hostUserId = 0, hostUsername = "host") {
  return enterpriseFetch(
    `/api/collaboration/rooms/create?name=${encodeURIComponent(name)}&room_type=${roomType}&host_user_id=${hostUserId}&host_username=${encodeURIComponent(hostUsername)}`,
    { method: "POST" }
  );
}

export async function listRooms(status = null) {
  let url = "/api/collaboration/rooms";
  if (status) url += `?status=${status}`;
  return enterpriseFetch(url);
}

export async function getRoom(roomId) {
  return enterpriseFetch(`/api/collaboration/rooms/${roomId}`);
}

export async function joinRoom(roomId, userId, username) {
  return enterpriseFetch(`/api/collaboration/rooms/${roomId}/join?user_id=${userId}&username=${encodeURIComponent(username)}`, { method: "POST" });
}

export async function leaveRoom(roomId, userId) {
  return enterpriseFetch(`/api/collaboration/rooms/${roomId}/leave?user_id=${userId}`, { method: "POST" });
}

export async function startRoom(roomId, userId) {
  return enterpriseFetch(`/api/collaboration/rooms/${roomId}/start?user_id=${userId}`, { method: "POST" });
}

export async function endRoom(roomId, userId) {
  return enterpriseFetch(`/api/collaboration/rooms/${roomId}/end?user_id=${userId}`, { method: "POST" });
}

export async function getRoomAnalytics(roomId) {
  return enterpriseFetch(`/api/collaboration/rooms/${roomId}/analytics`);
}

// Enterprise
export async function getTeamDashboard(teamId) {
  return enterpriseFetch(`/api/enterprise/teams/${teamId}/dashboard`);
}

export async function getOrgOverview(orgId) {
  return enterpriseFetch(`/api/enterprise/organizations/${orgId}/overview`);
}

export async function getUserGrowth(userId) {
  return enterpriseFetch(`/api/enterprise/users/${userId}/growth`);
}

// Behavioral
export async function analyzeBehavioralPatterns(sessions) {
  return enterpriseFetch("/api/behavioral/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(sessions),
  });
}

export async function getBehavioralProfile(userId) {
  return enterpriseFetch(`/api/behavioral/profile/${userId}`);
}

export async function getPatternDefinitions() {
  return enterpriseFetch("/api/behavioral/patterns");
}

// Certification
export async function getCertificationLevels() {
  return enterpriseFetch("/api/certification/levels");
}

export async function assessCertification(userStats) {
  return enterpriseFetch("/api/certification/assess", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(userStats),
  });
}

export async function evaluateCertificationSession(sessionData) {
  return enterpriseFetch("/api/certification/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(sessionData),
  });
}

export async function generateCertificate(userId, level, score) {
  return enterpriseFetch(`/api/certification/certificate/generate?user_id=${userId}&level=${level}&score=${score}`, { method: "POST" });
}

// Benchmarks
export async function calculateBenchmarks(sessionData) {
  return enterpriseFetch("/api/benchmarks/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(sessionData),
  });
}

export async function getBenchmarkRoles() {
  return enterpriseFetch("/api/benchmarks/roles");
}

export async function getRoleBenchmarkScore(roleId, sessionData) {
  return enterpriseFetch(`/api/benchmarks/roles/${roleId}/score`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(sessionData),
  });
}

// Role Training
export async function getTrainingRoles() {
  return enterpriseFetch("/api/roles");
}

export async function getTrainingRole(roleId) {
  return enterpriseFetch(`/api/roles/${roleId}`);
}

// Recruiter
export async function getInterviewTypes() {
  return enterpriseFetch("/api/recruiter/interview-types");
}

export async function getRecruiterPersonas() {
  return enterpriseFetch("/api/recruiter/personas");
}

export async function getInterviewQuestions(interviewType = "general", count = 3) {
  return enterpriseFetch(`/api/recruiter/questions?interview_type=${interviewType}&count=${count}`);
}

export async function evaluateInterviewResponse(response, question, metrics) {
  return enterpriseFetch("/api/recruiter/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ response, question, metrics }),
  });
}

// Dashboard
export async function getEnterpriseFeatures() {
  return enterpriseFetch("/api/dashboard/features");
}

// Recordings
export async function saveRecording(userId, sessionType, data) {
  return enterpriseFetch("/api/recordings/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, session_type: sessionType, ...data }),
  });
}

export async function getUserRecordings(userId) {
  return enterpriseFetch(`/api/recordings/user/${userId}`);
}
