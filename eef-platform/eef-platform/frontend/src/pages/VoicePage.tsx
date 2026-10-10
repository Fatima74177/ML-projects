import React, { useState } from "react";
import { api } from "../services/api";
import { StatusBadge, ModelTypeTag } from "../components/Badges";
import { ErrorState } from "../components/Common";

export default function VoicePage() {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const analyze = async () => {
    if (!file) return;
    setBusy(true); setError(null); setResult(null);
    try {
      const form = new FormData();
      form.set("audio", file);
      const res = await api.postForm("/voice/analyze", form);
      setResult(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-lg font-semibold">Voice Authentication</h1>
        <p className="text-xs text-slate-500">Real waveform DSP analysis. Transcript is a labeled placeholder pending a production STT integration.</p>
      </div>

      <div className="card space-y-3">
        <input type="file" accept=".wav,.mp3,.m4a,audio/*"
          onChange={(e) => { setFile(e.target.files?.[0] || null); setResult(null); }} className="text-sm" />
        <button onClick={analyze} disabled={!file || busy}
          className="text-xs bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white rounded px-4 py-2">
          {busy ? "Analyzing..." : "Analyze Voice"}
        </button>
      </div>

      {error && <ErrorState message={error} />}

      {result && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <StatusBadge status={result.decision} />
            <div className="flex gap-2">
              <ModelTypeTag type={result.model_type} />
              <ModelTypeTag type={result.transcript_model_type} />
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div><div className="text-xs text-slate-500">Duration</div><div className="font-semibold">{result.duration_seconds}s</div></div>
            <div><div className="text-xs text-slate-500">Sample Rate</div><div className="font-semibold">{result.sample_rate} Hz</div></div>
            <div><div className="text-xs text-slate-500">Speaker Score</div><div className="font-semibold">{result.speaker_score}</div></div>
            <div><div className="text-xs text-slate-500">Audio Quality</div><div className="font-semibold">{result.audio_quality}</div></div>
          </div>
          <div>
            <div className="text-xs text-slate-500 mb-1">Transcript</div>
            <div className="text-xs bg-slate-900 rounded p-3">{result.transcript}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 mb-1">Risk Indicators</div>
            <ul className="text-xs text-slate-300 list-disc list-inside space-y-0.5">
              {result.risk_indicators.map((i: string, idx: number) => <li key={idx}>{i}</li>)}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
