import React from "react";

export function RiskBadge({ level }: { level?: string }) {
  const l = (level || "").toUpperCase();
  const cls =
    l === "LOW" ? "badge-low" : l === "MEDIUM" ? "badge-medium" : l === "HIGH" ? "badge-high" :
    l === "CRITICAL" ? "badge-critical" : "badge-neutral";
  return <span className={`badge ${cls}`}>{l || "UNKNOWN"}</span>;
}

export function StatusBadge({ status }: { status?: string }) {
  const s = (status || "").toUpperCase();
  const cls =
    s === "VERIFIED" || s === "RESOLVED" || s === "ACCEPTED" ? "badge-low" :
    s === "REVIEW_REQUIRED" || s === "INVESTIGATING" ? "badge-medium" :
    s === "REJECTED" || s === "OPEN" ? "badge-high" :
    "badge-neutral";
  return <span className={`badge ${cls}`}>{s.replace(/_/g, " ")}</span>;
}

export function ModelTypeTag({ type }: { type?: string }) {
  const t = (type || "").toUpperCase();
  const color =
    t === "REAL_MODEL" ? "text-emerald-400 border-emerald-700" :
    t === "HEURISTIC" ? "text-amber-400 border-amber-700" :
    "text-sky-400 border-sky-700";
  return (
    <span className={`text-[10px] uppercase tracking-wide border rounded px-1.5 py-0.5 ${color}`}>
      {t.replace(/_/g, " ")}
    </span>
  );
}
