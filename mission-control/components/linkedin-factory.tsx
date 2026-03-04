"use client";

import { useEffect, useMemo, useState } from "react";
import { ContentItem, ContentStage } from "@/lib/types";

export function LinkedInGeneratorPanel() {
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("Safe mode enabled, no posting will occur.");
  return (
    <div className="glass rounded-[10px] p-4 card-glow">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">LinkedIn Generator</h3>
      <div className="space-y-3 text-sm">
        <p className="text-[#6B8AAE] text-xs">Safe generate: draft content without publishing.</p>
        <button
          onClick={async () => {
            setLoading(true);
            setMsg("Generating draft safely...");
            await new Promise((r) => setTimeout(r, 900));
            setLoading(false);
            setMsg("Draft generated in safe mode.");
          }}
          className="rounded-[6px] border border-cyan-700/60 bg-cyan-900/20 px-3 py-2 text-xs text-cyan-300 hover:bg-cyan-900/30 disabled:opacity-50 transition-smooth"
          disabled={loading}
        >
          {loading ? "Generating..." : "Safe generate"}
        </button>
        <p className={loading ? "text-[#4B6A9B]" : "text-emerald-400"} style={{ fontSize: "0.75rem" }}>{msg}</p>
      </div>
    </div>
  );
}

const stages: ContentStage[] = ["draft", "review", "approved", "posted"];

const stageConfig: Record<ContentStage, { bg: string; text: string; border: string; dot: string }> = {
  draft: { bg: "bg-[#1E2D45]/50", text: "text-[#6B8AAE]", border: "border-[#2D4163]", dot: "bg-[#4B6A9B]" },
  review: { bg: "bg-amber-900/30", text: "text-amber-300", border: "border-amber-800/50", dot: "bg-amber-400" },
  approved: { bg: "bg-blue-900/30", text: "text-blue-300", border: "border-blue-800/50", dot: "bg-blue-400" },
  posted: { bg: "bg-emerald-900/30", text: "text-emerald-300", border: "border-emerald-800/50", dot: "bg-emerald-400" },
};

function getSlaStatus(item: ContentItem) {
  const elapsedMinutes = Math.round((Date.now() - new Date(item.stageUpdatedAt).getTime()) / 60000);
  const nearSla = elapsedMinutes > Math.round(item.slaMinutes * 0.8);
  const breached = elapsedMinutes > item.slaMinutes;
  if (breached) return { label: "breached", cls: "text-red-400", near: true };
  if (nearSla) return { label: "near breach", cls: "text-amber-300", near: true };
  return { label: "on track", cls: "text-emerald-400", near: false };
}

export function ContentFactoryPanel() {
  const [items, setItems] = useState<ContentItem[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState("");
  const [activeStage, setActiveStage] = useState<ContentStage | "all">("all");

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const response = await fetch("/api/content-factory", { cache: "no-store" });
        if (!response.ok) throw new Error("Failed to load content state");
        const payload = await response.json() as { items: ContentItem[]; source?: string };
        setItems(payload.items || []);
        setSource(payload.source || "");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
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

  const filtered = useMemo(() => {
    if (activeStage === "all") return items;
    return items.filter((item) => item.stage === activeStage);
  }, [items, activeStage]);

  async function advance(itemId: string) {
    const response = await fetch("/api/content-factory", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ itemId }),
    });
    if (!response.ok) return;
    const payload = await response.json() as { item: ContentItem };
    setItems((prev) => prev.map((row) => row.id === payload.item.id ? payload.item : row));
  }

  return (
    <div className="space-y-4">
      {/* Pipeline funnel */}
      <div className="glass rounded-[10px] p-4">
        <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">Content pipeline</h3>
        <div className="flex items-center gap-0">
          {stages.map((stage, idx) => {
            const cfg = stageConfig[stage];
            const isActive = activeStage === stage;
            return (
              <button
                key={stage}
                onClick={() => setActiveStage(activeStage === stage ? "all" : stage)}
                className={`flex-1 relative text-center py-3 px-2 transition-smooth ${cfg.bg} border ${cfg.border} ${isActive ? "ring-1 ring-[#4F8EF7] z-10" : "opacity-70 hover:opacity-100"} ${idx === 0 ? "rounded-l-[8px]" : ""} ${idx === stages.length - 1 ? "rounded-r-[8px]" : ""}`}
              >
                <div className="flex items-center justify-center gap-1.5 mb-1">
                  <span className={`h-1.5 w-1.5 rounded-full ${cfg.dot}`} />
                  <span className={`text-[10px] uppercase tracking-widest font-semibold ${cfg.text}`}>{stage}</span>
                </div>
                <span className={`text-2xl font-bold ${cfg.text}`}>{counts[stage]}</span>
                {idx < stages.length - 1 && (
                  <span className="absolute -right-px top-1/2 -translate-y-1/2 z-20 text-[#2D4163] text-xs">
                    {">"}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content items */}
      <div className="glass rounded-[10px] p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">Content Factory</h3>
          {source && !loading && <p className="text-[10px] text-[#2D4163]">{source}</p>}
        </div>

        {loading && <p className="text-sm text-[#4B6A9B]">Loading content from linkedin_content_calendar.md...</p>}
        {error && <p className="text-red-400 text-sm">{error}</p>}

        <ul className="space-y-2">
          {filtered.slice(0, 20).map((item) => {
            const sla = getSlaStatus(item);
            const cfg = stageConfig[item.stage];
            return (
              <li
                key={item.id}
                className={`glass-light rounded-[8px] p-3 transition-smooth border ${cfg.border} ${sla.near ? "animate-glow-amber-border" : ""}`}
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <p className="text-xs text-[#e2e8f0] font-medium flex-1">{item.title}</p>
                  <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] border ${cfg.bg} ${cfg.text} ${cfg.border}`}>
                    {item.stage}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className={`text-[10px] ${sla.cls}`}>SLA: {sla.label}</span>
                  <button
                    onClick={() => advance(item.id)}
                    disabled={item.stage === "posted"}
                    className="rounded border border-[#1E2D45] px-2 py-0.5 text-[10px] text-[#6B8AAE] hover:border-[#2D4163] hover:text-[#a8c4e8] disabled:opacity-30 transition-smooth"
                  >
                    Advance
                  </button>
                </div>
              </li>
            );
          })}
          {filtered.length === 0 && !loading && (
            <li className="text-sm text-[#2D4163]">No content items in this stage.</li>
          )}
          {filtered.length > 20 && (
            <li className="text-[10px] text-[#2D4163]">Showing 20 of {filtered.length} items</li>
          )}
        </ul>
      </div>
    </div>
  );
}
