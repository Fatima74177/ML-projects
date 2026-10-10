import React, { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line,
} from "recharts";
import { api } from "../services/api";
import { StatCard, LoadingState, ErrorState } from "../components/Common";

const RISK_COLORS: Record<string, string> = {
  LOW: "#10b981", MEDIUM: "#f59e0b", HIGH: "#f97316", CRITICAL: "#ef4444", UNKNOWN: "#64748b",
};

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [riskDist, setRiskDist] = useState<any[]>([]);
  const [trustDist, setTrustDist] = useState<any[]>([]);
  const [alertSeverity, setAlertSeverity] = useState<any[]>([]);
  const [trend, setTrend] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [s, r, t, a, v] = await Promise.all([
          api.get("/dashboard/stats"),
          api.get("/dashboard/charts/risk-distribution"),
          api.get("/dashboard/charts/trust-score-distribution"),
          api.get("/dashboard/charts/alert-severity"),
          api.get("/dashboard/charts/verification-trend"),
        ]);
        setStats(s);
        setRiskDist(r);
        setTrustDist(t);
        setAlertSeverity(a);
        setTrend(v);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <LoadingState label="Loading dashboard..." />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">Executive Dashboard</h1>
        <p className="text-xs text-slate-500">
          All figures are computed live from the platform database -- nothing here is hardcoded.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Identities" value={stats.total_users} />
        <StatCard label="Total Verifications" value={stats.total_verifications} />
        <StatCard label="Success Rate" value={`${stats.success_rate_pct}%`} />
        <StatCard label="High-Risk Identities" value={stats.high_risk_identities} />
        <StatCard label="Verified" value={stats.successful_verifications} />
        <StatCard label="Review Required" value={stats.review_required_verifications} />
        <StatCard label="Rejected" value={stats.failed_verifications} />
        <StatCard label="Open Fraud Cases" value={stats.open_fraud_cases} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <div className="text-sm font-medium mb-3">Risk Level Distribution</div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={riskDist} dataKey="count" nameKey="risk_level" outerRadius={80} label>
                {riskDist.map((entry, i) => (
                  <Cell key={i} fill={RISK_COLORS[entry.risk_level] || "#64748b"} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "#111a2e", border: "1px solid #1f2b45" }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="text-sm font-medium mb-3">Trust Score Distribution</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={trustDist}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2b45" />
              <XAxis dataKey="bucket" tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} allowDecimals={false} />
              <Tooltip contentStyle={{ background: "#111a2e", border: "1px solid #1f2b45" }} />
              <Bar dataKey="count" fill="#38bdf8" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="text-sm font-medium mb-3">Alert Severity Distribution</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={alertSeverity} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2b45" />
              <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 10 }} allowDecimals={false} />
              <YAxis dataKey="severity" type="category" tick={{ fill: "#94a3b8", fontSize: 10 }} width={70} />
              <Tooltip contentStyle={{ background: "#111a2e", border: "1px solid #1f2b45" }} />
              <Bar dataKey="count" fill="#f97316" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="text-sm font-medium mb-3">Verification Volume Trend</div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2b45" />
              <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 9 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} allowDecimals={false} />
              <Tooltip contentStyle={{ background: "#111a2e", border: "1px solid #1f2b45" }} />
              <Line type="monotone" dataKey="count" stroke="#a78bfa" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
