import React, { useState } from "react";
import { api } from "../services/api";
import { ModelTypeTag } from "../components/Badges";
import { ErrorState } from "../components/Common";

export default function DocumentsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const analyze = async () => {
    if (!file) return;
    setBusy(true); setError(null); setResult(null);
    try {
      const form = new FormData();
      form.set("document", file);
      const res = await api.postForm("/documents/analyze", form);
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
        <h1 className="text-lg font-semibold">Document Intelligence</h1>
        <p className="text-xs text-slate-500">Real Tesseract OCR + deterministic field extraction. Never claims legal document authenticity.</p>
      </div>

      <div className="card space-y-3">
        <input type="file" accept="image/*" onChange={(e) => {
          const f = e.target.files?.[0] || null;
          setFile(f);
          setResult(null);
          if (f) setPreview(URL.createObjectURL(f));
        }} className="text-sm" />
        {preview && <img src={preview} alt="preview" className="max-h-64 rounded border border-eefborder" />}
        <button onClick={analyze} disabled={!file || busy}
          className="text-xs bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white rounded px-4 py-2">
          {busy ? "Running OCR..." : "Analyze Document"}
        </button>
      </div>

      {error && <ErrorState message={error} />}

      {result && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium">Analysis Result</div>
            <ModelTypeTag type={result.model_type} />
          </div>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div><div className="text-xs text-slate-500">Document Score</div><div className="font-semibold">{result.document_score}</div></div>
            <div><div className="text-xs text-slate-500">OCR Confidence</div><div className="font-semibold">{result.ocr_confidence}</div></div>
            <div><div className="text-xs text-slate-500">Image Quality</div><div className="font-semibold">{result.quality_score}</div></div>
          </div>
          <div>
            <div className="text-xs text-slate-500 mb-1">Extracted Fields</div>
            <table className="text-xs w-full">
              <tbody>
                {Object.entries(result.extracted_fields || {}).map(([k, v]) => (
                  <tr key={k} className="border-b border-eefborder/50">
                    <td className="py-1 pr-4 text-slate-500">{k}</td>
                    <td className="py-1 text-slate-200">{String(v)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {result.anomalies?.length > 0 && (
            <div>
              <div className="text-xs text-slate-500 mb-1">Anomalies Detected</div>
              <ul className="text-xs text-amber-400 list-disc list-inside space-y-0.5">
                {result.anomalies.map((a: string, i: number) => <li key={i}>{a}</li>)}
              </ul>
            </div>
          )}
          <div>
            <div className="text-xs text-slate-500 mb-1">Raw OCR Text</div>
            <pre className="text-xs bg-slate-900 rounded p-3 overflow-x-auto whitespace-pre-wrap">{result.ocr_text}</pre>
          </div>
          <div className="text-[11px] text-slate-500 italic">{result.note}</div>
        </div>
      )}
    </div>
  );
}
