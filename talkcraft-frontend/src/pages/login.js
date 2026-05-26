import React, { useState } from "react";
import { useRouter } from "next/router";
import { login as apiLogin, register as apiRegister } from "@/utils/api";
import { useAuth } from "./_app";

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { loginUser, isAuthenticated } = useAuth();

  if (isAuthenticated) {
    router.push("/");
    return null;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      let result;
      if (isLogin) {
        result = await apiLogin(username, password);
      } else {
        result = await apiRegister(username, email, password, displayName);
      }

      if (result.access_token) {
        loginUser(result.access_token, result.user);
        router.push("/");
      } else {
        setError(result.detail || "Authentication failed");
      }
    } catch (err) {
      setError(err.message || "Connection failed. Make sure the coach server is running on port 8004.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center">
      <div className="w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-accent">TalkCraft</h1>
          <p className="text-text-secondary mt-2">Advanced Communication Intelligence</p>
        </div>

        <div className="bg-surface border border-border rounded-lg p-6">
          <div className="flex mb-6">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-2 text-center text-sm font-medium transition-colors ${
                isLogin
                  ? "text-accent border-b-2 border-accent"
                  : "text-text-secondary hover:text-white"
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-2 text-center text-sm font-medium transition-colors ${
                !isLogin
                  ? "text-accent border-b-2 border-accent"
                  : "text-text-secondary hover:text-white"
              }`}
            >
              Register
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-500/50 rounded text-sm text-red-400">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-text-secondary mb-1">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3 py-2 bg-black border border-border rounded text-white focus:outline-none focus:border-accent transition-colors"
                placeholder="Your username"
                required
              />
            </div>

            {!isLogin && (
              <div>
                <label className="block text-sm text-text-secondary mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 bg-black border border-border rounded text-white focus:outline-none focus:border-accent transition-colors"
                  placeholder="your@email.com"
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-sm text-text-secondary mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 bg-black border border-border rounded text-white focus:outline-none focus:border-accent transition-colors"
                placeholder="Min 6 characters"
                required
                minLength={6}
              />
            </div>

            {!isLogin && (
              <div>
                <label className="block text-sm text-text-secondary mb-1">Display Name (optional)</label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full px-3 py-2 bg-black border border-border rounded text-white focus:outline-none focus:border-accent transition-colors"
                  placeholder="How you want to be called"
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 bg-accent text-black font-medium rounded hover:bg-accent/90 transition-colors disabled:opacity-50"
            >
              {loading ? "Please wait..." : isLogin ? "Login" : "Create Account"}
            </button>
          </form>
        </div>

        <div className="mt-6 text-center">
          <a href="/" className="text-text-secondary hover:text-white text-sm transition-colors">
            ← Back to Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
