import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import { RiskBadge } from "../components/Badges";
import { LoadingState, ErrorState, EmptyState } from "../components/Common";

export default function IdentitiesPage() {
  const [verifications, setVerifications] = useState<any[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const v = await api.get("/identity?limit=100");
        setVerifications(v);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // Build a de-duplicated identity list from verification sessions (Section 22/23).
  const byIdentity = new Map<number, any>();
  for (const v of verifications) {
    if (!byIdentity.has(v.identity_id)) {
      byIdentity.set(v.identity_id, { identity_id: v.identity_id, latest: v, count: 1 });
    } else {
      const entry = byIdentity.get(v.identity_id);
      entry.count += 1;
      if (new Date(v.created_at) > new Date(entry.latest.created_at)) entry.latest = v;
    }
  }
  const rows = Array.from(byIdentity.values()).filter((r) =>
    query ? String(r.identity_id).includes(query) : true
  );

  if (loading) return <LoadingState label="Loading identities..." />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Identities</h1>
        <input
          placeholder="Search by identity ID..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="bg-slate-900 border border-eefborder rounded px-3 py-1.5 text-sm w-64 outline-none focus:border-sky-500"
        />
      </div>

      {rows.length === 0 ? (
        <EmptyState message="No identities found. Run a verification or load demo data." />
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 border-b border-eefborder">
                <th className="py-2 pr-4">Identity ID</th>
                <th className="py-2 pr-4">Verifications</th>
                <th className="py-2 pr-4">Latest Status</th>
                <th className="py-2 pr-4">Latest Trust Score</th>
                <th className="py-2 pr-4">Latest Verification</th>
                <th className="py-2 pr-4"></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.identity_id} className="border-b border-eefborder/50 hover:bg-slate-800/30">
                  <td className="py-2 pr-4 font-medium">#{r.identity_id}</td>
                  <td className="py-2 pr-4">{r.count}</td>
                  <td className="py-2 pr-4">{r.latest.status}</td>
                  <td className="py-2 pr-4">
                    <RiskBadge level={r.latest.trust_score >= 70 ? "LOW" : r.latest.trust_score >= 55 ? "MEDIUM" : r.latest.trust_score >= 40 ? "HIGH" : "CRITICAL"} />
                    <span className="ml-2 text-slate-400">{r.latest.trust_score}</span>
                  </td>
                  <td className="py-2 pr-4 text-slate-500 text-xs">
                    {new Date(r.latest.created_at).toLocaleString()}
                  </td>
                  <td className="py-2 pr-4">
                    <Link to={`/identities/${r.identity_id}`} className="text-sky-400 text-xs hover:underline">
                      View profile &rarr;
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
