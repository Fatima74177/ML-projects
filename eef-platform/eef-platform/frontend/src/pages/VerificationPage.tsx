import React, { useState } from "react";
import { api } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import { StatusBadge, ModelTypeTag } from "../components/Badges";
import { ErrorState } from "../components/Common";

const DOC_TYPES = ["NATIONAL_ID", "PASSPORT", "DRIVING_LICENSE", "EMPLOYEE_ID", "RESIDENCE_PERMIT"];
const STEPS = ["Identity Info", "Document", "Selfie", "Review & Submit", "Result"];

export default function VerificationPage() {
  const { user } = useAuth();
  const [step, setStep] = useState(0);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [documentType, setDocumentType] = useState("NATIONAL_ID");
  const [document, setDocument] = useState<File | null>(null);
  const [selfie, setSelfie] = useState<File | null>(null);
  const [docPreview, setDocPreview] = useState<string | null>(null);
  const [selfiePreview, setSelfiePreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const canNext = () => {
    if (step === 0) return fullName.trim().length > 0;
    if (step === 1) return !!document;
    if (step === 2) return !!selfie;
    return true;
  };

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.set("full_name", fullName);
      form.set("email", email);
      form.set("phone", phone);
      form.set("document_type", documentType);
      form.set("device_fingerprint", "WEB-DASHBOARD-DEMO");
      form.set("document", document as File);
      form.set("selfie", selfie as File);
      const res = await api.postForm("/identity/verify", form);
      setResult(res);
      setStep(4);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const reset = () => {
    setStep(0); setFullName(""); setEmail(""); setPhone(""); setDocumentType("NATIONAL_ID");
    setDocument(null); setSelfie(null); setDocPreview(null); setSelfiePreview(null);
    setResult(null); setError(null);
  };

  if (user?.role === "VIEWER") {
    return (
      <div className="max-w-3xl mx-auto space-y-4">
        <div>
          <h1 className="text-lg font-semibold">Identity Verification Wizard</h1>
          <p className="text-xs text-slate-500">Run the verification pipeline for an identity.</p>
        </div>
        <div className="card border-amber-800 bg-amber-950/30 text-sm text-amber-200" role="status">
          Viewer accounts are read-only and cannot submit identity verifications. Sign in as an analyst or admin to run this workflow.
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-lg font-semibold">Identity Verification Wizard</h1>
        <p className="text-xs text-slate-500">Runs the full pipeline: OCR &rarr; face match &rarr; liveness &rarr; trust scoring &rarr; fraud intelligence &rarr; decision.</p>
      </div>

      <div className="flex items-center gap-2 text-xs">
        {STEPS.map((s, i) => (
          <React.Fragment key={s}>
            <div className={`px-3 py-1 rounded-full border ${i === step ? "border-sky-500 text-sky-300 bg-sky-950" : i < step ? "border-emerald-700 text-emerald-400" : "border-eefborder text-slate-500"}`}>
              {i + 1}. {s}
            </div>
            {i < STEPS.length - 1 && <div className="w-4 h-px bg-eefborder" />}
          </React.Fragment>
        ))}
      </div>

      {error && <ErrorState message={error} />}

      <div className="card">
        {step === 0 && (
          <div className="space-y-3">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Full Name *</label>
              <input className="w-full bg-slate-900 border border-eefborder rounded px-3 py-2 text-sm" value={fullName} onChange={(e) => setFullName(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Email</label>
              <input className="w-full bg-slate-900 border border-eefborder rounded px-3 py-2 text-sm" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Phone</label>
              <input className="w-full bg-slate-900 border border-eefborder rounded px-3 py-2 text-sm" value={phone} onChange={(e) => setPhone(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Document Type *</label>
              <select className="w-full bg-slate-900 border border-eefborder rounded px-3 py-2 text-sm" value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
                {DOC_TYPES.map((t) => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
              </select>
            </div>
          </div>
        )}

        {step === 1 && (
          <div>
            <label className="block text-xs text-slate-400 mb-2">Upload document image (jpg/png/pdf)</label>
            <input type="file" accept="image/*,.pdf" onChange={(e) => {
              const f = e.target.files?.[0] || null;
              setDocument(f);
              if (f && f.type.startsWith("image/")) setDocPreview(URL.createObjectURL(f));
            }} className="text-sm" />
            {docPreview && <img src={docPreview} alt="document preview" className="mt-3 max-h-64 rounded border border-eefborder" />}
          </div>
        )}

        {step === 2 && (
          <div>
            <label className="block text-xs text-slate-400 mb-2">Upload selfie image</label>
            <input type="file" accept="image/*" onChange={(e) => {
              const f = e.target.files?.[0] || null;
              setSelfie(f);
              if (f) setSelfiePreview(URL.createObjectURL(f));
            }} className="text-sm" />
            {selfiePreview && <img src={selfiePreview} alt="selfie preview" className="mt-3 max-h-64 rounded border border-eefborder" />}
          </div>
        )}

        {step === 3 && (
          <div className="space-y-2 text-sm">
            <div><span className="text-slate-500">Name:</span> {fullName}</div>
            <div><span className="text-slate-500">Email:</span> {email || "-"}</div>
            <div><span className="text-slate-500">Document type:</span> {documentType}</div>
            <div><span className="text-slate-500">Document file:</span> {document?.name}</div>
            <div><span className="text-slate-500">Selfie file:</span> {selfie?.name}</div>
            <p className="text-xs text-slate-500 pt-2">Submitting will run OCR, face matching, liveness, trust scoring, and fraud intelligence against this data, and may raise alerts automatically.</p>
          </div>
        )}

        {step === 4 && result && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <StatusBadge status={result.status} />
              <span className="text-sm text-slate-400">Verification #{result.verification_id}</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div><div className="text-xs text-slate-500">Document Score</div><div className="font-semibold">{result.document_score}</div></div>
              <div><div className="text-xs text-slate-500">Face Match</div><div className="font-semibold">{result.identity_match_score}</div></div>
              <div><div className="text-xs text-slate-500">Liveness</div><div className="font-semibold">{result.liveness_score}</div></div>
              <div><div className="text-xs text-slate-500">Trust Score</div><div className="font-semibold">{result.trust_score}</div></div>
            </div>
            {result.fraud_indicators?.length > 0 && (
              <div>
                <div className="text-xs text-slate-500 mb-1">Fraud Indicators</div>
                <div className="flex flex-wrap gap-1">
                  {result.fraud_indicators.map((f: string) => <span key={f} className="badge badge-high">{f}</span>)}
                </div>
              </div>
            )}
            <div>
              <div className="text-xs text-slate-500 mb-1">Decision Reasoning</div>
              <ul className="text-xs text-slate-400 list-disc list-inside space-y-0.5">
                {(result.explanation?.decision_reasoning || []).map((r: string, i: number) => <li key={i}>{r}</li>)}
              </ul>
            </div>
            <details className="text-xs text-slate-500">
              <summary className="cursor-pointer">Full explanation JSON</summary>
              <pre className="mt-2 bg-slate-900 rounded p-3 overflow-x-auto">{JSON.stringify(result.explanation, null, 2)}</pre>
            </details>
            <button onClick={reset} className="text-xs text-sky-400 hover:underline">Start another verification &rarr;</button>
          </div>
        )}
      </div>

      {step < 4 && (
        <div className="flex justify-between">
          <button
            disabled={step === 0}
            onClick={() => setStep((s) => s - 1)}
            className="text-xs border border-eefborder rounded px-4 py-2 disabled:opacity-30"
          >
            Back
          </button>
          {step < 3 ? (
            <button
              disabled={!canNext()}
              onClick={() => setStep((s) => s + 1)}
              className="text-xs bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white rounded px-4 py-2"
            >
              Next
            </button>
          ) : (
            <button
              disabled={busy}
              onClick={submit}
              className="text-xs bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white rounded px-4 py-2"
            >
              {busy ? "Processing..." : "Run Verification"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
