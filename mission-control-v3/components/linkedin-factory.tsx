"use client";

import { useEffect, useMemo, useState } from "react";
import { Panel } from "@/components/ui";
import { ContentItem, ContentStage } from "@/lib/types";

export function LinkedInGeneratorPanel() {
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("Safe mode enabled, no posting will occur.");
  return (
    <Panel title="LinkedIn Generator">
      <div className="space-y-3 text-sm">
        <p className="text-zinc-400">safe-generate UX parity with explicit loading feedback.</p>
        <button
          onClick={async () => {
            setLoading(true);
            setMsg("Generating draft safely...");
            await new Promise((r) => setTimeout(r, 900));
            setLoading(false);
            setMsg("Draft generated in safe mode.");
          }}
          className="rounded border border-cyan-700 px-3 py-2 text-cyan-300 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Generating..." : "Safe generate"}
        </button>
        <p className="text-emerald-400">{msg}</p>
      </div>
    </Panel>
  );
}

const stages: ContentStage[] = ["draft", "review", "approved", "posted"];

function getSlaStatus(item: ContentItem) {
  const elapsedMinutes = Math.round((Date.now() - new Date(item.stageUpdatedAt).getTime()) / 60000);
  if (elapsedMinutes > item.slaMinutes) {
    return { label: "breached", cls: "text-red-400" };
  }
  if (elapsedMinutes > Math.round(item.slaMinutes * 0.8)) {
    return { label: "near breach", cls: "text-amber-300" };
  }
  return { label: "on track", cls: "text-emerald-400" };
}

export function ContentFactoryPanel() {
  const [items, setItems] = useState<ContentItem[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const response = await fetch("/api/content-factory", { cache: "no-store" });
        if (!response.ok) {
          throw new Error("Failed to load content state");
        }
        const payload = await response.json() as { items: ContentItem[] };
        setItems(payload.items || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      }
    }

    load();
  }, []);

  const counts = useMemo(() => {
    return stages.reduce<Record<ContentStage, number>>((acc, stage) => {
      acc[stage] = items.filter((item) => item.stage === stage).length;
      return acc;
    }, { draft: 0, review: 0, approved: 0, posted: 0 });
  }, [items]);

  async function advance(itemId: string) {
    const response = await fetch("/api/content-factory", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ itemId }),
    });

    if (!response.ok) {
      return;
    }

    const payload = await response.json() as { item: ContentItem };
    setItems((prev) => prev.map((row) => row.id === payload.item.id ? payload.item : row));
  }

  return (
    <Panel title="Content Factory">
      <div className="space-y-2 text-sm text-zinc-300">
        {error && <p className="text-red-400">{error}</p>}
        <div className="grid grid-cols-4 gap-2 text-center text-xs">
          {[
            ["Draft", counts.draft],
            ["Review", counts.review],
            ["Approved", counts.approved],
            ["Posted", counts.posted],
          ].map(([k, v]) => <div key={String(k)} className="rounded border border-zinc-700 p-2"><div>{k}</div><div className="text-lg font-semibold">{v}</div></div>)}
        </div>

        <ul className="space-y-2 pt-2">
          {items.map((item) => {
            const sla = getSlaStatus(item);
            return (
              <li key={item.id} className="rounded border border-zinc-800 p-2">
                <div className="flex items-center justify-between">
                  <p>{item.title}</p>
                  <p className="text-xs text-zinc-500">{item.stage}</p>
                </div>
                <div className="mt-1 flex items-center justify-between text-xs">
                  <p className={sla.cls}>SLA: {sla.label}</p>
                  <button onClick={() => advance(item.id)} disabled={item.stage === "posted"} className="rounded border border-zinc-700 px-2 py-0.5 disabled:opacity-40">Advance</button>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </Panel>
  );
}
