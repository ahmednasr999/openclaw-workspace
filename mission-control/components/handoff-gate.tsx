"use client";

import { useEffect, useMemo, useState } from "react";
import { Panel } from "@/components/ui";
import { handoffTrend } from "@/lib/parity";
import { HandoffItem, HandoffValidationResult } from "@/lib/types";

function validateUrl(input: string): HandoffValidationResult {
  const value = input.trim();
  if (!value) return { valid: false, reason: "Enter a URL to validate.", confidence: 0, matchedRule: "empty" };
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    return { valid: false, reason: "Invalid URL format.", confidence: 0, matchedRule: "format" };
  }
  if (!["http:", "https:"].includes(url.protocol)) return { valid: false, reason: "Only http and https URLs are allowed.", confidence: 10, matchedRule: "protocol" };
  const host = url.hostname.toLowerCase();
  const pathName = url.pathname.toLowerCase();
  const linkedInDirect = host.includes("linkedin.com") && (pathName.startsWith("/jobs/view/") || pathName === "/jobs/view" || url.searchParams.has("currentjobid"));
  if (linkedInDirect) return { valid: true, reason: "Valid LinkedIn direct job URL.", confidence: 92, matchedRule: "linkedin_direct" };
  const employerPath = /(career|careers|job|jobs|vacanc|position|opportunit)/.test(pathName);
  if (!host.includes("linkedin.com") && employerPath) return { valid: true, reason: "Valid direct employer job posting URL.", confidence: 84, matchedRule: "employer_posting" };
  return { valid: false, reason: "URL must be a LinkedIn /jobs/view link or direct employer posting.", confidence: 25, matchedRule: "rule_miss" };
}

export function HandoffGate() {
  const [url, setUrl] = useState("");
  const [checked, setChecked] = useState(false);
  const [queue, setQueue] = useState<HandoffItem[]>([]);
  const [promoteMsg, setPromoteMsg] = useState("");

  const result = useMemo(() => validateUrl(url), [url]);
  const heatTone = handoffTrend.at(-1)! >= 80 ? "text-emerald-400" : "text-amber-300";

  useEffect(() => {
    async function loadQueue() {
      const response = await fetch("/api/handoff", { cache: "no-store" });
      if (!response.ok) {
        return;
      }
      const payload = await response.json() as { queue: HandoffItem[] };
      setQueue(payload.queue || []);
    }

    loadQueue();
  }, []);

  async function promote() {
    setPromoteMsg("Promoting...");
    const response = await fetch("/api/handoff", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const payload = await response.json() as { item?: HandoffItem; validation?: HandoffValidationResult };
    if (!response.ok || !payload.item) {
      setPromoteMsg(payload.validation?.reason || "Promotion failed.");
      return;
    }

    setQueue((prev) => [payload.item!, ...prev].slice(0, 20));
    setPromoteMsg(`Queued with score ${payload.item.score}.`);
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Panel title="URL preflight validator">
        <div className="space-y-3 text-sm">
          <input value={url} onChange={(e) => { setUrl(e.target.value); setChecked(false); }} placeholder="Paste role URL" className="w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-2" />
          <button onClick={() => setChecked(true)} className="rounded border border-zinc-600 px-3 py-2 hover:bg-zinc-900">Validate URL</button>
          {checked && <p className={result.valid ? "text-emerald-400" : "text-red-400"}>{result.reason} ({result.confidence}%)</p>}
          <button onClick={promote} disabled={!result.valid} className="rounded border px-3 py-2 disabled:cursor-not-allowed disabled:border-zinc-800 disabled:text-zinc-600 border-emerald-700 text-emerald-300">Promote to handoff queue</button>
          {promoteMsg && <p className="text-xs text-zinc-400">{promoteMsg}</p>}
        </div>
      </Panel>
      <Panel title="Trend and heat indicators">
        <div className="space-y-3 text-sm">
          <p className={heatTone}>Quality trend: {handoffTrend.at(-1)}%</p>
          <div className="flex items-end gap-1 h-24">
            {handoffTrend.map((v, i) => (
              <div key={i} className="w-6 rounded-t bg-cyan-700/70" style={{ height: `${v}%` }} title={`Day ${i + 1}: ${v}%`} />
            ))}
          </div>
          <p className="text-zinc-400">Heatmap parity: bars represent 7-day validation confidence.</p>
          <p className="text-zinc-300">Queue: {queue.length} validated links.</p>
        </div>
      </Panel>
    </div>
  );
}
