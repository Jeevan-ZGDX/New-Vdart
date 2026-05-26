import React, { useState } from "react";
import { startMic, uploadFile, stopEngine } from "@/utils/api";
import { useAuth } from "@/pages/_app";
import Link from "next/link";

export default function Sidebar({ onModeChange }) {
  const [mode, setMode] = useState("mic");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [showNav, setShowNav] = useState(false);
  const { user, isAuthenticated, logoutUser } = useAuth();

  const handleModeChange = (newMode) => {
    setMode(newMode);
    setError("");
    onModeChange(newMode);
  };

  const handleStartMic = async () => {
    try {
      setError("");
      await startMic();
    } catch (e) {
      setError("Failed to start microphone");
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file first");
      return;
    }
    setUploading(true);
    setError("");
    try {
      await uploadFile(file);
    } catch (e) {
      setError(e.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleStop = async () => {
    try {
      setError("");
      await stopEngine();
    } catch (e) {
      setError("Failed to stop");
    }
  };

  return (
    <div className="w-72 bg-surface border-r border-border h-screen p-5 flex flex-col">
      <h1 className="text-xl font-bold mb-1">TalkCraft</h1>
      <p className="text-xs text-text-secondary mb-4">
        AI Communication Intelligence
      </p>

      {isAuthenticated && (
        <div className="mb-4">
          <button
            onClick={() => setShowNav(!showNav)}
            className="w-full flex items-center justify-between px-3 py-2 bg-black border border-border rounded text-sm hover:border-accent transition-colors"
          >
            <span>{user?.display_name || user?.username}</span>
            <span className="text-xs text-text-secondary">{showNav ? '▲' : '▼'}</span>
          </button>
          {showNav && (
            <div className="mt-2 bg-black border border-border rounded overflow-hidden max-h-80 overflow-y-auto">
              <Link href="/" className="block px-4 py-2 text-sm hover:bg-border transition-colors">
                📊 Live Dashboard
              </Link>
              <Link href="/coaching" className="block px-4 py-2 text-sm hover:bg-border transition-colors">
                🎯 Coaching
              </Link>
              <Link href="/progress" className="block px-4 py-2 text-sm hover:bg-border transition-colors">
                📈 Progress
              </Link>
              <Link href="/achievements" className="block px-4 py-2 text-sm hover:bg-border transition-colors">
                🏆 Achievements
              </Link>
              <Link href="/sessions" className="block px-4 py-2 text-sm hover:bg-border transition-colors">
                📋 Sessions
              </Link>
              <div className="border-t border-border my-1"></div>
              <Link href="/multilingual" className="block px-4 py-2 text-sm hover:bg-border transition-colors">
                🌐 Multilingual
              </Link>
              <Link href="/collaboration" className="block px-4 py-2 text-sm hover:bg-border transition-colors">
                👥 Collaboration
              </Link>
              <Link href="/avatar" className="block px-4 py-2 text-sm hover:bg-border transition-colors">
                🤖 AI Avatars
              </Link>
              <Link href="/recruiter" className="block px-4 py-2 text-sm hover:bg-border transition-colors">
                💼 Interview Sim
              </Link>
              <Link href="/roles" className="block px-4 py-2 text-sm hover:bg-border transition-colors">
                👔 Role Training
              </Link>
              <Link href="/certification" className="block px-4 py-2 text-sm hover:bg-border transition-colors">
                🏅 Certification
              </Link>
              <Link href="/benchmarks" className="block px-4 py-2 text-sm hover:bg-border transition-colors">
                📊 Benchmarks
              </Link>
              <Link href="/enterprise" className="block px-4 py-2 text-sm hover:bg-border transition-colors">
                🏢 Enterprise
              </Link>
              <div className="border-t border-border my-1"></div>
              <button
                onClick={logoutUser}
                className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-border transition-colors"
              >
                🚪 Logout
              </button>
            </div>
          )}
        </div>
      )}

      {!isAuthenticated && (
        <Link
          href="/login"
          className="block mb-4 px-3 py-2 text-center bg-accent text-black text-sm font-medium rounded hover:bg-accent/90 transition-colors"
        >
          Login / Register
        </Link>
      )}

      <h2 className="text-sm font-semibold uppercase tracking-wide text-text-secondary mb-3">
        Input Mode
      </h2>

      <div className="space-y-2 mb-6">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            name="mode"
            checked={mode === "mic"}
            onChange={() => handleModeChange("mic")}
            className="accent-green-500"
          />
          <span className="text-sm">Microphone</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            name="mode"
            checked={mode === "file"}
            onChange={() => handleModeChange("file")}
            className="accent-green-500"
          />
          <span className="text-sm">Audio File</span>
        </label>
      </div>

      {mode === "mic" ? (
        <button
          onClick={handleStartMic}
          className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded transition-colors mb-2"
        >
          Start Microphone
        </button>
      ) : (
        <div className="space-y-3">
          <input
            type="file"
            accept=".wav,.mp3,.flac,.ogg,.m4a"
            onChange={(e) => setFile(e.target.files[0])}
            className="w-full text-sm text-gray-400 file:mr-3 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-green-600 file:text-white hover:file:bg-green-700 cursor-pointer"
          />
          {file && (
            <p className="text-xs text-text-secondary">
              {file.name} ({(file.size / 1024).toFixed(1)} KB)
            </p>
          )}
          <button
            onClick={handleUpload}
            disabled={uploading || !file}
            className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold py-2 px-4 rounded transition-colors"
          >
            {uploading ? "Processing..." : "Process File"}
          </button>
        </div>
      )}

      <button
        onClick={handleStop}
        className="w-full bg-gray-700 hover:bg-gray-600 text-white font-semibold py-2 px-4 rounded transition-colors mt-3"
      >
        Stop
      </button>

      {error && (
        <p className="text-red-400 text-sm mt-3">{error}</p>
      )}

      <div className="mt-auto text-xs text-text-secondary space-y-1">
        <p>TalkCraft v4.0</p>
        <p>CPU-optimized</p>
        <p>Phase 4: Coaching</p>
      </div>
    </div>
  );
}
