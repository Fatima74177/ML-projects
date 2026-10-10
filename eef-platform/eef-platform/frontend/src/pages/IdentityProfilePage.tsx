import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../services/api";
import { RiskBadge, StatusBadge, ModelTypeTag } from "../components/Badges";
import { LoadingState, ErrorState, EmptyState } from "../components/Common";

export default function IdentityProfilePage() {
  const { id } = useParams();
  const identityId = Number(id);
  const [verifications, setVerifications] = useState<any[]>([]);
  const [trust, setTrust] = useState<any>(null);
  const [graph, setGraph] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [fraudCases, setFraudCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [allVerifs, graphData, allAlerts, allCases] = await Promise.all([
          api.get("/identity?limit=200"),
          api.get(`/graph/user/${identityId}`),
          api.get("/alerts?limit=200"),
          api.get("/fraud/cases"),
        ]);
        const mine = allVerifs.filter((v: any) => v.identity_id === identityId);
        setVerifications(mine);
        setGraph(graphData);
        setAlerts(allAlerts.filter((a: any) => a.identity_id === identityId));
        setFraudCases(allCases.filter((c: any) => (c.related_identities || []).includes(identityId)));
        try {
          setTrust(await api.get(`/trust/identity/${identityId}`));
        } catch {
          setTrust(null);
        }
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [identityId]);

  if (loading) return <LoadingState label="Loading identity profile..." />;
  if (error) return <ErrorState message={error} />;

  const latest = verifications[0];
  const userNode = graph?.nodes?.find((n: any) => n.id === `user:${identityId}`);
  const deviceNodes = (graph?.nodes || []).filter((n: any) => n.type === "Device");
  const ipNodes = (graph?.nodes || []).filter((n: any) => n.type === "IP");
  const docNodes = (graph?.nodes || []).filter((n: any) => n.type === "Document");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">{userNode?.label || `Identity #${identityId}`}</h1>
          <p className="text-xs text-slate-500">Identity ID #{identityId}</p>
        </div>
        {trust && <RiskBadge level={trust.risk_level} />}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card">
          <div className="text-xs text-slate-500 mb-1">Trust Score</div>
          <div className="text-2xl font-bold">{trust?.trust_score ?? "n/a"}</div>
        </div>
        <div className="card">
          <div className="text-xs text-slate-500 mb-1">Verification Sessions</div>
          <div className="text-2xl font-bold">{verifications.length}</div>
        </div>
        <div className="card">
          <div className="text-xs text-slate-500 mb-1">Open Fraud Cases / Alerts</div>
          <div className="text-2xl font-bold">{fraudCases.length} / {alerts.length}</div>
        </div>
      </div>

      <section className="card">
        <div className="text-sm font-medium mb-3">Verification History</div>
        {verifications.length === 0 ? <EmptyState message="No verification sessions on record." /> : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 border-b border-eefborder">
                <th className="py-2 pr-4">ID</th><th className="py-2 pr-4">Status</th>
                <th className="py-2 pr-4">Trust</th><th className="py-2 pr-4">Face Match</th>
                <th className="py-2 pr-4">Liveness</th><th className="py-2 pr-4">Document</th>
                <th className="py-2 pr-4">Date</th>
              </tr>
            </thead>
            <tbody>
              {verifications.map((v) => (
                <tr key={v.id} className="border-b border-eefborder/50">
                  <td className="py-2 pr-4">#{v.id}</td>
                  <td className="py-2 pr-4"><StatusBadge status={v.status} /></td>
                  <td className="py-2 pr-4">{v.trust_score}</td>
                  <td className="py-2 pr-4">{v.identity_match_score}</td>
                  <td className="py-2 pr-4">{v.liveness_score}</td>
                  <td className="py-2 pr-4">{v.document_score}</td>
                  <td className="py-2 pr-4 text-xs text-slate-500">{new Date(v.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {latest?.explanation && (
        <section className="card">
          <div className="text-sm font-medium mb-3">Latest Decision Explanation</div>
          <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside">
            {(latest.explanation.decision_reasoning || []).map((r: string, i: number) => <li key={i}>{r}</li>)}
          </ul>
        </section>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <section className="card">
          <div className="text-sm font-medium mb-2">Devices ({deviceNodes.length})</div>
          {deviceNodes.map((d: any) => <div key={d.id} className="text-xs text-slate-400 py-0.5">{d.label}</div>)}
        </section>
        <section className="card">
          <div className="text-sm font-medium mb-2">IP Addresses ({ipNodes.length})</div>
          {ipNodes.map((d: any) => <div key={d.id} className="text-xs text-slate-400 py-0.5">{d.label} {d.high_risk && <span className="badge badge-high ml-1">high-risk</span>}</div>)}
        </section>
        <section className="card">
          <div className="text-sm font-medium mb-2">Documents ({docNodes.length})</div>
          {docNodes.map((d: any) => <div key={d.id} className="text-xs text-slate-400 py-0.5">{d.label} ({d.doc_type})</div>)}
        </section>
      </div>

      <section className="card">
        <div className="text-sm font-medium mb-3">Alerts</div>
        {alerts.length === 0 ? <EmptyState message="No alerts for this identity." /> : (
          <div className="space-y-2">
            {alerts.map((a) => (
              <div key={a.id} className="flex items-center justify-between text-xs border-b border-eefborder/50 pb-2">
                <div>
                  <span className="font-medium text-slate-200">{a.type.replace(/_/g, " ")}</span>
                  <span className="text-slate-500 ml-2">{a.description}</span>
                </div>
                <StatusBadge status={a.status} />
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
