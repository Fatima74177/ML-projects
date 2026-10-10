import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { RiskBadge, StatusBadge } from "../components/Badges";
import { LoadingState, ErrorState, EmptyState } from "../components/Common";
import { useAuth } from "../hooks/useAuth";

export default function FraudPage() {
  const { user } = useAuth();
  const canInvestigate = user?.role !== "VIEWER";
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [noteText, setNoteText] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      setCases(await api.get("/fraud/cases"));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const scan = async () => {
    setScanning(true);
    try {
      await api.post("/fraud/scan");
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setScanning(false);
    }
  };

  const addNote = async (caseId: number) => {
    if (!noteText.trim()) return;
    await api.post(`/fraud/cases/${caseId}/notes`, { note: noteText });
    setNoteText("");
    await load();
  };

  const updateStatus = async (caseId: number, status: string) => {
    await api.patch(`/fraud/cases/${caseId}/status`, { status });
    await load();
  };

  if (loading) return <LoadingState label="Loading fraud cases..." />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Fraud Intelligence</h1>
          <p className="text-xs text-slate-500">Shared documents/devices/IPs, repeated failures, and identity reuse -- detected via real SQL aggregation.</p>
        </div>
        {canInvestigate && (
          <button onClick={scan} disabled={scanning} className="text-xs bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white rounded px-4 py-2">
            {scanning ? "Scanning..." : "Re-scan for fraud signals"}
          </button>
        )}
      </div>

      {cases.length === 0 ? <EmptyState message="No fraud cases found." /> : (
        <div className="space-y-3">
          {cases.map((c) => (
            <div key={c.id} className="card">
              <div className="flex items-center justify-between cursor-pointer" onClick={() => setExpanded(expanded === c.id ? null : c.id)}>
                <div className="flex items-center gap-3">
                  <span className="font-medium text-sm">Case #{c.id}</span>
                  <RiskBadge level={c.severity} />
                  <StatusBadge status={c.status} />
                  <span className="text-xs text-slate-500">{(c.signals || []).join(", ")}</span>
                </div>
                <span className="text-xs text-slate-500">{c.related_identities?.length || 0} identities</span>
              </div>
              {expanded === c.id && (
                <div className="mt-3 pt-3 border-t border-eefborder space-y-3 text-xs">
                  <div><span className="text-slate-500">Related identities:</span> {(c.related_identities || []).join(", ") || "none"}</div>
                  <div><span className="text-slate-500">Related devices:</span> {(c.related_devices || []).join(", ") || "none"}</div>
                  <div><span className="text-slate-500">Related documents:</span> {(c.related_documents || []).join(", ") || "none"}</div>
                  <div>
                    <span className="text-slate-500">Investigation notes:</span>
                    <ul className="list-disc list-inside mt-1">
                      {(c.investigation_notes || []).map((n: string, i: number) => <li key={i}>{n}</li>)}
                    </ul>
                  </div>
                  {canInvestigate && (
                    <>
                      <div className="flex gap-2 pt-2">
                        <input value={noteText} onChange={(e) => setNoteText(e.target.value)} placeholder="Add investigation note..."
                          className="flex-1 bg-slate-900 border border-eefborder rounded px-2 py-1 text-xs" />
                        <button onClick={() => addNote(c.id)} className="border border-eefborder rounded px-3 py-1 text-xs hover:bg-slate-800">Add Note</button>
                      </div>
                      <div className="flex gap-2 pt-1">
                        {["OPEN", "INVESTIGATING", "CLOSED"].map((s) => (
                          <button key={s} onClick={() => updateStatus(c.id, s)}
                            className={`px-3 py-1 rounded border text-xs ${c.status === s ? "border-sky-500 text-sky-300" : "border-eefborder text-slate-400"}`}>
                            {s}
                          </button>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
