import React, { useState } from "react";
import { api } from "../services/api";
import { ModelTypeTag } from "../components/Badges";

const SUGGESTIONS = [
  "Why is user 3 high risk?",
  "Why did verification fail for user 9?",
  "Show connected devices for user 1?",
  "Summarize user 5.",
  "Explain the deepfake result for user 3.",
  "Explain the fraud indicators for user 1.",
];

interface Msg {
  role: "user" | "assistant";
  text: string;
  citations?: any[];
  modelType?: string;
}

export default function CopilotPage() {
  const [messages, setMessages] = useState<Msg[]>([
    { role: "assistant", text: "Ask me about any identity's verification history, fraud signals, trust score, deepfake results, or connected devices. I only answer from real platform records -- if there's no evidence, I'll say so." },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  const send = async (q?: string) => {
    const question = q ?? input;
    if (!question.trim()) return;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setBusy(true);
    try {
      const res = await api.post("/copilot/ask", { question });
      setMessages((m) => [...m, { role: "assistant", text: res.answer, citations: res.citations, modelType: res.model_type }]);
    } catch (e: any) {
      setMessages((m) => [...m, { role: "assistant", text: `Error: ${e.message}` }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-4 flex flex-col h-full">
      <div>
        <h1 className="text-lg font-semibold">AI Identity Copilot</h1>
        <p className="text-xs text-slate-500">Tool-grounded assistant -- every answer is backed by a real database/graph query, cited below the response.</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button key={s} onClick={() => send(s)} className="text-[11px] border border-eefborder rounded-full px-3 py-1 text-slate-400 hover:border-sky-500 hover:text-sky-300">
            {s}
          </button>
        ))}
      </div>

      <div className="card flex-1 space-y-3 min-h-[400px] max-h-[500px] overflow-y-auto">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${m.role === "user" ? "bg-sky-900 text-sky-100" : "bg-slate-800 text-slate-200"}`}>
              <div>{m.text}</div>
              {m.modelType && (
                <div className="mt-2 flex items-center gap-2">
                  <ModelTypeTag type={m.modelType} />
                  {m.citations && m.citations.length > 0 && (
                    <span className="text-[10px] text-slate-500">{m.citations.length} tool call(s) cited</span>
                  )}
                </div>
              )}
              {m.citations && m.citations.length > 0 && (
                <details className="mt-1">
                  <summary className="text-[10px] text-slate-500 cursor-pointer">View citations</summary>
                  <pre className="text-[10px] text-slate-500 mt-1 overflow-x-auto max-w-full">{JSON.stringify(m.citations, null, 2)}</pre>
                </details>
              )}
            </div>
          </div>
        ))}
        {busy && <div className="text-xs text-slate-500">Querying platform data...</div>}
      </div>

      <div className="flex gap-2">
        <input value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Ask about an identity, e.g. 'Why is user 3 high risk?'"
          className="flex-1 bg-slate-900 border border-eefborder rounded px-3 py-2 text-sm" />
        <button onClick={() => send()} disabled={busy} className="text-xs bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white rounded px-4 py-2">
          Send
        </button>
      </div>
    </div>
  );
}
