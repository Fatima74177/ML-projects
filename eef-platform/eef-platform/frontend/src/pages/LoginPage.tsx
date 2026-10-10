import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("analyst");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username, password);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-eefbg px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-6">
          <div className="text-xl font-bold text-sky-400">EEF Platform</div>
          <div className="text-xs text-slate-500 mt-1">
            Enterprise Digital Identity, Trust &amp; Deepfake Detection
          </div>
        </div>
        <form onSubmit={submit} className="card space-y-4">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Username</label>
            <input
              className="w-full bg-slate-900 border border-eefborder rounded px-3 py-2 text-sm outline-none focus:border-sky-500"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Password</label>
            <input
              type="password"
              className="w-full bg-slate-900 border border-eefborder rounded px-3 py-2 text-sm outline-none focus:border-sky-500"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <div className="text-xs text-red-400 bg-red-950/50 border border-red-800 rounded px-3 py-2">{error}</div>}
          <button
            type="submit"
            disabled={busy}
            className="w-full bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-sm font-medium py-2 rounded"
          >
            {busy ? "Signing in..." : "Sign in"}
          </button>
        </form>
        <div className="mt-4 text-[11px] text-slate-500 card">
          <div className="font-semibold text-slate-400 mb-1">Demo credentials (local dev only):</div>
          <div>admin / Admin@12345</div>
          <div>analyst / Analyst@12345</div>
          <div>viewer / Viewer@12345</div>
        </div>
      </div>
    </div>
  );
}
