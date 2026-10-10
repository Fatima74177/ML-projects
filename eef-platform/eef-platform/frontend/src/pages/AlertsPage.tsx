import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import { RiskBadge, StatusBadge } from "../components/Badges";
import { LoadingState, ErrorState, EmptyState } from "../components/Common";
import { useAuth } from "../hooks/useAuth";

const STATUSES = ["OPEN", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"];

export default function AlertsPage() {
  const { user } = useAuth();
  const canInvestigate = user?.role !== "VIEWER";
  const [alerts, setAlerts] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const q = statusFilter ? `?status=${statusFilter}` : "";
      setAlerts(await api.get(`/alerts${q}`));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [statusFilter]);

  const updateStatus = async (id: number, status: string) => {
    await api.patch(`/alerts/${id}/status`, { status });
    await load();
  };

  if (loading) return <LoadingState label="Loading alerts..." />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Alert Center</h1>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-slate-900 border border-eefborder rounded px-3 py-1.5 text-xs">
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {alerts.length === 0 ? <EmptyState message="No alerts match this filter." /> : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 border-b border-eefborder">
                <th className="py-2 pr-4">Type</th><th className="py-2 pr-4">Severity</th>
                <th className="py-2 pr-4">Identity</th><th className="py-2 pr-4">Description</th>
                <th className="py-2 pr-4">Status</th><th className="py-2 pr-4">Created</th>
                {canInvestigate && <th className="py-2 pr-4"></th>}
              </tr>
            </thead>
            <tbody>
              {alerts.map((a) => (
                <tr key={a.id} className="border-b border-eefborder/50">
                  <td className="py-2 pr-4 text-xs font-medium">{a.type.replace(/_/g, " ")}</td>
                  <td className="py-2 pr-4"><RiskBadge level={a.severity} /></td>
                  <td className="py-2 pr-4 text-xs">
                    {a.identity_id ? <Link to={`/identities/${a.identity_id}`} className="text-sky-400 hover:underline">#{a.identity_id}</Link> : "-"}
                  </td>
                  <td className="py-2 pr-4 text-xs text-slate-400 max-w-xs truncate">{a.description}</td>
                  <td className="py-2 pr-4"><StatusBadge status={a.status} /></td>
                  <td className="py-2 pr-4 text-xs text-slate-500">{new Date(a.created_at).toLocaleDateString()}</td>
                  {canInvestigate && (
                    <td className="py-2 pr-4">
                      <select value={a.status} onChange={(e) => updateStatus(a.id, e.target.value)}
                        className="bg-slate-900 border border-eefborder rounded px-2 py-1 text-[11px]">
                        {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                      </select>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
