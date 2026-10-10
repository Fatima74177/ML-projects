import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import { ModelTypeTag } from "../components/Badges";
import { LoadingState, ErrorState } from "../components/Common";

export default function SettingsPage() {
  const { user } = useAuth();
  const [models, setModels] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [m, u] = await Promise.all([
          api.get("/models/status"),
          api.get("/users").catch(() => []),
        ]);
        setModels(m.models);
        setUsers(u);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <LoadingState label="Loading settings..." />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold">Settings</h1>
        <p className="text-xs text-slate-500">Model registry, account, and platform users.</p>
      </div>

      <section className="card">
        <div className="text-sm font-medium mb-1">Your Account</div>
        <div className="text-xs text-slate-400">
          {user?.full_name} ({user?.username}) &middot; {user?.email} &middot; role <b>{user?.role}</b>
        </div>
      </section>

      <section className="card">
        <div className="text-sm font-medium mb-3">AI Model Registry (Section 41)</div>
        <p className="text-xs text-slate-500 mb-3">
          Every AI component reports its honest classification. REAL_MODEL = genuine trained/algorithmic model on real
          input. HEURISTIC = deterministic, explainable signal processing standing in for a model that needs
          offline-unreachable weights. DEMO_SIMULATION = placeholder pending a production integration.
        </p>
        <div className="space-y-2">
          {models.map((m) => (
            <div key={m.component} className="flex items-center justify-between border-b border-eefborder/50 pb-2 text-xs">
              <div>
                <div className="font-medium text-slate-200">{m.component}</div>
                <div className="text-slate-500">{m.model_name} {m.model_version !== "n/a" && `v${m.model_version}`}</div>
                <div className="text-slate-600 mt-0.5">{m.notes}</div>
              </div>
              <div className="flex items-center gap-2 shrink-0 ml-4">
                <ModelTypeTag type={m.model_type} />
                <span className="text-emerald-400">{m.status}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {users.length > 0 && (
        <section className="card">
          <div className="text-sm font-medium mb-3">Platform Users</div>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-slate-500 border-b border-eefborder">
                <th className="py-2 pr-4">Username</th><th className="py-2 pr-4">Email</th>
                <th className="py-2 pr-4">Role</th><th className="py-2 pr-4">Active</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u: any) => (
                <tr key={u.id} className="border-b border-eefborder/50">
                  <td className="py-1.5 pr-4">{u.username}</td>
                  <td className="py-1.5 pr-4 text-slate-400">{u.email}</td>
                  <td className="py-1.5 pr-4">{u.role}</td>
                  <td className="py-1.5 pr-4">{u.is_active ? "Yes" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
