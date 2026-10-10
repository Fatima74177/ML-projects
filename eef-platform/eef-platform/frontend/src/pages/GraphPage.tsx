import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { LoadingState, ErrorState } from "../components/Common";

const TYPE_COLORS: Record<string, string> = {
  User: "#38bdf8", Document: "#a78bfa", Device: "#f59e0b", IP: "#f87171", FraudCase: "#ef4444",
};

function simpleLayout(nodes: any[]) {
  // Deterministic circular layout grouped by type -- no external graph library required.
  const byType: Record<string, any[]> = {};
  nodes.forEach((n) => { (byType[n.type] ||= []).push(n); });
  const types = Object.keys(byType);
  const positioned: Record<string, { x: number; y: number }> = {};
  const ringGap = 150;
  types.forEach((type, ti) => {
    const radius = 80 + ti * ringGap;
    const list = byType[type];
    list.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / Math.max(list.length, 1);
      positioned[n.id] = { x: 400 + radius * Math.cos(angle), y: 300 + radius * Math.sin(angle) };
    });
  });
  return positioned;
}

export default function GraphPage() {
  const [identityId, setIdentityId] = useState("1");
  const [graph, setGraph] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [selected, setSelected] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const navigate = useNavigate();

  const load = async () => {
    if (!identityId) return;
    setLoading(true); setError(null); setSelected(null);
    try {
      const [g, a] = await Promise.all([
        api.get(`/graph/user/${identityId}?depth=2`),
        api.get("/graph/analytics"),
      ]);
      setGraph(g);
      setAnalytics(a);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const positions = useMemo(() => (graph ? simpleLayout(graph.nodes) : {}), [graph]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Knowledge Graph</h1>
        <div className="flex items-center gap-2">
          <input value={identityId} onChange={(e) => setIdentityId(e.target.value)} placeholder="Identity ID"
            className="w-32 bg-slate-900 border border-eefborder rounded px-3 py-1.5 text-sm" />
          <button onClick={load} className="text-xs bg-sky-600 hover:bg-sky-500 text-white rounded px-4 py-1.5">Load</button>
        </div>
      </div>

      {error && <ErrorState message={error} />}
      {loading && <LoadingState label="Loading graph..." />}

      {analytics && (
        <div className="grid grid-cols-4 gap-3 text-xs">
          <div className="card"><div className="text-slate-500">Nodes</div><div className="text-lg font-bold">{analytics.node_count}</div></div>
          <div className="card"><div className="text-slate-500">Edges</div><div className="text-lg font-bold">{analytics.edge_count}</div></div>
          <div className="card"><div className="text-slate-500">Connected Components</div><div className="text-lg font-bold">{analytics.connected_components}</div></div>
          <div className="card"><div className="text-slate-500">Suspicious Clusters</div><div className="text-lg font-bold">{analytics.suspicious_clusters?.length || 0}</div></div>
        </div>
      )}

      {graph && (
        <div className="card">
          <div className="flex items-center gap-2 mb-2 text-xs">
            <button onClick={() => setZoom((z) => Math.min(z + 0.2, 3))} className="border border-eefborder rounded px-2 py-1">Zoom +</button>
            <button onClick={() => setZoom((z) => Math.max(z - 0.2, 0.4))} className="border border-eefborder rounded px-2 py-1">Zoom -</button>
            <button onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }} className="border border-eefborder rounded px-2 py-1">Reset</button>
            <div className="flex items-center gap-3 ml-4">
              {Object.entries(TYPE_COLORS).map(([t, c]) => (
                <div key={t} className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: c }} /> {t}</div>
              ))}
            </div>
          </div>

          <div className="overflow-hidden rounded border border-eefborder bg-slate-950" style={{ height: 480 }}
            onMouseDown={(e) => {
              const startX = e.clientX, startY = e.clientY, origin = { ...pan };
              const onMove = (ev: MouseEvent) => setPan({ x: origin.x + (ev.clientX - startX), y: origin.y + (ev.clientY - startY) });
              const onUp = () => { window.removeEventListener("mousemove", onMove); window.removeEventListener("mouseup", onUp); };
              window.addEventListener("mousemove", onMove);
              window.addEventListener("mouseup", onUp);
            }}>
            <svg width="100%" height="100%" viewBox="0 0 800 600">
              <g transform={`translate(${pan.x} ${pan.y}) scale(${zoom})`}>
                {graph.edges.map((e: any, i: number) => {
                  const s = positions[e.source], t = positions[e.target];
                  if (!s || !t) return null;
                  return <line key={i} x1={s.x} y1={s.y} x2={t.x} y2={t.y} stroke="#1f2b45" strokeWidth={1} />;
                })}
                {graph.nodes.map((n: any) => {
                  const p = positions[n.id];
                  if (!p) return null;
                  return (
                    <g key={n.id} transform={`translate(${p.x} ${p.y})`} className="cursor-pointer"
                      onClick={() => {
                        setSelected(n);
                        if (n.type === "User") {
                          const uid = n.id.split(":")[1];
                          if (uid) navigate(`/identities/${uid}`);
                        }
                      }}>
                      <circle r={n.type === "User" ? 14 : 10} fill={TYPE_COLORS[n.type] || "#64748b"}
                        stroke={selected?.id === n.id ? "#fff" : "transparent"} strokeWidth={2} />
                      <text x={0} y={26} textAnchor="middle" fontSize={9} fill="#94a3b8">{n.label}</text>
                    </g>
                  );
                })}
              </g>
            </svg>
          </div>

          {selected && (
            <div className="mt-3 text-xs bg-slate-900 rounded p-3">
              <div className="font-medium text-slate-200 mb-1">{selected.label} ({selected.type})</div>
              <pre className="text-slate-500 overflow-x-auto">{JSON.stringify(selected, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
