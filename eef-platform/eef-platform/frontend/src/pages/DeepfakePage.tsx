import React, { useState } from "react";
import { api } from "../services/api";
import { ModelTypeTag } from "../components/Badges";
import { ErrorState } from "../components/Common";

export default function DeepfakePage() {
  const [mediaType, setMediaType] = useState<"IMAGE" | "VIDEO">("IMAGE");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const analyze = async () => {
    if (!file) return;
    setBusy(true); setError(null); setResult(null);
    try {
      const form = new FormData();
      form.set("file", file);
      const res = await api.postForm(`/deepfake/analyze?media_type=${mediaType}`, form);
      setResult(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const pct = (v: number) => `${Math.round((v || 0) * 100)}%`;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-lg font-semibold">Deepfake Detection</h1>
        <p className="text-xs text-slate-500">Forensic signal analysis (frequency-domain, boundary, compression, temporal). Prototype -- every result requires human review.</p>
      </div>

      <div className="card space-y-3">
        <div className="flex gap-2 text-xs">
          {(["IMAGE", "VIDEO"] as const).map((t) => (
            <button key={t} onClick={() => { setMediaType(t); setFile(null); setResult(null); }}
              className={`px-3 py-1.5 rounded border ${mediaType === t ? "border-sky-500 text-sky-300 bg-sky-950" : "border-eefborder text-slate-400"}`}>
              {t}
            </button>
          ))}
        </div>
        <input type="file" accept={mediaType === "IMAGE" ? "image/*" : "video/*"}
          onChange={(e) => { setFile(e.target.files?.[0] || null); setResult(null); }} className="text-sm" />
        <button onClick={analyze} disabled={!file || busy}
          className="text-xs bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white rounded px-4 py-2">
          {busy ? "Analyzing..." : "Run Deepfake Analysis"}
        </button>
      </div>

      {error && <ErrorState message={error} />}

      {result && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium">{result.disclaimer}</div>
            <ModelTypeTag type={result.model_type} />
          </div>

          <div className="flex items-center gap-6">
            <div className="w-32 h-32 rounded-full border-8 flex items-center justify-center text-2xl font-bold"
              style={{ borderColor: result.deepfake_probability >= 0.6 ? "#ef4444" : result.deepfake_probability >= 0.4 ? "#f59e0b" : "#10b981" }}>
              {pct(result.deepfake_probability)}
            </div>
            <div className="text-sm space-y-1">
              <div><span className="text-slate-500">Deepfake probability:</span> {result.deepfake_probability}</div>
              <div><span className="text-slate-500">Real probability:</span> {result.real_probability}</div>
              <div><span className="text-slate-500">Confidence:</span> {result.confidence}</div>
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-500 mb-1">Indicators</div>
            <ul className="text-xs text-slate-300 list-disc list-inside space-y-0.5">
              {result.indicators.map((i: string, idx: number) => <li key={idx}>{i}</li>)}
            </ul>
          </div>

          {result.frame_results?.length > 0 && (
            <div>
              <div className="text-xs text-slate-500 mb-2">Frame Timeline ({result.frame_results.length} sampled frames)</div>
              <div className="flex gap-0.5 h-16 items-end">
                {result.frame_results.map((f: any) => (
                  <div key={f.frame_number} title={`frame ${f.frame_number}: score ${f.score}`}
                    className="flex-1 bg-sky-600 rounded-t"
                    style={{ height: `${Math.max(4, f.score * 100)}%`, backgroundColor: f.score >= 0.6 ? "#ef4444" : f.score >= 0.4 ? "#f59e0b" : "#38bdf8" }} />
                ))}
              </div>
            </div>
          )}

          <div className="text-xs text-slate-500">
            Metadata: {Object.entries(result.metadata || {}).map(([k, v]) => `${k}=${v}`).join("  |  ")}
          </div>
        </div>
      )}
    </div>
  );
}
