import React, { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: "\u25A6", viewerHidden: false },
  { to: "/identities", label: "Identities", icon: "\u25CF", viewerHidden: false },
  { to: "/verification", label: "Verification", icon: "\u2713", viewerHidden: false },
  { to: "/documents", label: "Documents", icon: "\u25A4", viewerHidden: true },
  { to: "/deepfake", label: "Deepfake", icon: "\u25C8", viewerHidden: true },
  { to: "/voice", label: "Voice", icon: "\u266A", viewerHidden: true },
  { to: "/fraud", label: "Fraud", icon: "\u26A0", viewerHidden: false },
  { to: "/alerts", label: "Alerts", icon: "\u2691", viewerHidden: false },
  { to: "/graph", label: "Graph", icon: "\u2735", viewerHidden: false },
  { to: "/copilot", label: "Copilot", icon: "\u25C9", viewerHidden: true },
  { to: "/audit", label: "Audit", icon: "\u2637", viewerHidden: false },
  { to: "/settings", label: "Settings", icon: "\u2699", viewerHidden: false },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [theme, setTheme] = useState<"dark" | "light">(() =>
    localStorage.getItem("eef_theme") === "light" ? "light" : "dark"
  );

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("eef_theme", theme);
  }, [theme]);

  return (
    <div className="min-h-screen flex bg-eefbg">
      <aside className="w-56 shrink-0 border-r border-eefborder bg-eefpanel flex flex-col">
        <div className="px-4 py-4 border-b border-eefborder">
          <div className="text-sm font-bold tracking-wide text-sky-400">EEF PLATFORM</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Identity, Trust &amp; Deepfake Detection</div>
        </div>
        <nav className="flex-1 overflow-y-auto py-2">
          {NAV_ITEMS.filter((item) => user?.role !== "VIEWER" || !item.viewerHidden).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2 text-sm ${
                  isActive ? "bg-sky-950 text-sky-300 border-r-2 border-sky-500" : "text-slate-400 hover:bg-slate-800/50"
                }`
              }
            >
              <span className="w-4 text-center">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 py-3 border-t border-eefborder text-xs text-slate-500">
          Prototype / case-study platform.
          <br />
          See README for model limitations.
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-eefborder bg-eefpanel flex items-center justify-between px-6">
          <div className="text-sm text-slate-400">
            Signed in as <span className="text-slate-200 font-medium">{user?.username}</span>{" "}
            <span className="badge badge-neutral ml-1">{user?.role}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setTheme((current) => current === "dark" ? "light" : "dark")}
              aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
              aria-pressed={theme === "dark"}
              title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
              className="inline-flex items-center gap-2 text-xs text-slate-300 border border-eefborder rounded px-3 py-1.5 hover:bg-slate-800"
            >
              <span aria-hidden="true">{theme === "dark" ? "☼" : "☾"}</span>
              <span>{theme === "dark" ? "Dark" : "Light"}</span>
            </button>
            <button
              onClick={() => {
                logout();
                navigate("/login");
              }}
              className="text-xs text-slate-400 hover:text-red-400 border border-eefborder rounded px-3 py-1.5"
            >
              Logout
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
