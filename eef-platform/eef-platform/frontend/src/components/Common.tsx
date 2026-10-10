import React from "react";

export function StatCard({ label, value, sub }: { label: string; value: React.ReactNode; sub?: string }) {
  return (
    <div className="card">
      <div className="text-xs text-slate-400">{label}</div>
      <div className="text-2xl font-bold mt-1 text-slate-100">{value}</div>
      {sub && <div className="text-[11px] text-slate-500 mt-1">{sub}</div>}
    </div>
  );
}

export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return <div className="text-sm text-slate-500 py-8 text-center">{label}</div>;
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="text-sm text-red-400 bg-red-950/40 border border-red-800 rounded px-4 py-3">
      {message}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return <div className="text-sm text-slate-500 py-8 text-center border border-dashed border-eefborder rounded">{message}</div>;
}
