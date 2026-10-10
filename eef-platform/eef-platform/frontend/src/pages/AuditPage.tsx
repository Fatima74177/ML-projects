import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { LoadingState, ErrorState, EmptyState } from "../components/Common";

export default function AuditPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [actionFilter, setActionFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const q = actionFilter ? `?action=${actionFilter}` : "";
        setLogs(await api.get(`/audit${q}`));
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [actionFilter]);

  const actions = Array.from(new Set(logs.map((l) => l.action)));

  if (loading) return <LoadingState label="Loading audit log..." />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Audit Log</h1>
          <p className="text-xs text-slate-500">Immutable, append-only. No update/delete endpoint exists by design.</p>
        </div>
        <select value={actionFilter} onChange={(e) => setActionFilter(e.target.value)}
          className="bg-slate-900 border border-eefborder rounded px-3 py-1.5 text-xs">
          <option value="">All actions</option>
          {actions.map((a) => <option key={a} value={a}>{a}</option>)}
        </select>
      </div>

      {logs.length === 0 ? <EmptyState message="No audit entries yet." /> : (
        <div className="card overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-slate-500 border-b border-eefborder">
                <th className="py-2 pr-4">Time</th><th className="py-2 pr-4">Actor</th>
                <th className="py-2 pr-4">Action</th><th className="py-2 pr-4">Resource</th>
                <th className="py-2 pr-4">Result</th><th className="py-2 pr-4">IP</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id} className="border-b border-eefborder/50">
                  <td className="py-1.5 pr-4 text-slate-500">{new Date(l.created_at).toLocaleString()}</td>
                  <td className="py-1.5 pr-4">{l.actor}</td>
                  <td className="py-1.5 pr-4 font-medium">{l.action}</td>
                  <td className="py-1.5 pr-4 text-slate-400">{l.resource}</td>
                  <td className="py-1.5 pr-4">
                    <span className={l.result === "SUCCESS" || l.result === "VERIFIED" ? "text-emerald-400" : "text-red-400"}>{l.result}</span>
                  </td>
                  <td className="py-1.5 pr-4 text-slate-500">{l.ip || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
