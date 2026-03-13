"use client";

import { useEffect, useMemo, useState } from "react";

interface PipelineLead {
  id: string;
  role: string;
  company: string;
  location?: string;
  stage: string;
  ageHours: number;
  totalScore: number;
  threshold: number;
  decision: "qualified" | "watch" | "dropped";
  droppedReason?: string;
  appliedDate?: string;
  followUpDate?: string;
  salaryFit?: number;
  strategicFit?: number;
  sourceQuality?: number;
}

function stageBadgeClass(stage: string): string {
  const s = stage.toLowerCase();
  if (s.includes("interview") || s.includes("offer")) {
    return "bg-amber-900/50 text-amber-300 border border-amber-700/60 animate-pulse";
  }
  if (s.includes("applied") || s.includes("awaiting")) {
    return "bg-blue-900/50 text-blue-300 border border-blue-700/60";
  }
  if (s.includes("qualified") || s.includes("cv ready")) {
    return "bg-emerald-900/40 text-emerald-300 border border-emerald-700/60";
  }
  if (s.includes("watch") || s.includes("identified")) {
    return "bg-yellow-900/40 text-yellow-300 border border-yellow-700/60";
  }
  if (s.includes("closed") || s.includes("rejected") || s.includes("dropped")) {
    return "bg-zinc-800/50 text-zinc-500 border border-zinc-700/40";
  }
  return "bg-[#1E2D45] text-[#6B8AAE] border border-[#2D4163]";
}

function AtsScoreBadge({ score, decision }: { score: number; decision: string }) {
  if (!score || score === 0) return <span className="text-[#2D4163]">-</span>;

  const color =
    decision === "qualified"
      ? "text-emerald-400"
      : decision === "watch"
      ? "text-amber-300"
      : "text-[#4B6A9B]";

  return (
    <div className="flex items-center gap-1">
      <span className={`text-xs font-semibold ${color}`}>{score}%</span>
      <div className="relative h-4 w-4">
        <svg className="h-4 w-4 progress-ring" viewBox="0 0 16 16">
          <circle cx="8" cy="8" r="6" fill="none" stroke="#1E2D45" strokeWidth="2" />
          <circle
            cx="8"
            cy="8"
            r="6"
            fill="none"
            stroke={decision === "qualified" ? "#10B981" : decision === "watch" ? "#F59E0B" : "#4B6A9B"}
            strokeWidth="2"
            strokeDasharray={`${(score / 100) * 37.7} 37.7`}
            strokeLinecap="round"
          />
        </svg>
      </div>
    </div>
  );
}

function ageLabel(ageHours: number): { label: string; cls: string } {
  if (ageHours <= 72) return { label: "fresh", cls: "text-emerald-400" };
  if (ageHours <= 168) return { label: "warm", cls: "text-amber-300" };
  return { label: "aging", cls: "text-red-400" };
}

export function JobRadar() {
  const [rows, setRows] = useState<PipelineLead[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "qualified" | "watch" | "dropped">("all");

  useEffect(() => {
    async function load() {
      try {
        const response = await fetch("/api/job-radar", { cache: "no-store" });
        if (!response.ok) throw new Error("Failed to load job radar");
        const payload = await response.json() as { leads: PipelineLead[]; total: number };
        setRows(payload.leads || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  // Sort: Interview first, then watch, then applied, then dropped
  const sortedRows = useMemo(() => {
    return [...rows].sort((a, b) => {
      const stageScore = (s: string) => {
        const sl = s.toLowerCase();
        if (sl.includes("interview") || sl.includes("offer")) return 0;
        if (sl.includes("awaiting")) return 1;
        if (sl.includes("applied")) return 2;
        if (sl.includes("cv ready") || sl.includes("qualified")) return 3;
        if (sl.includes("watch") || sl.includes("identified")) return 4;
        return 5;
      };
      return stageScore(a.stage) - stageScore(b.stage);
    });
  }, [rows]);

  const filtered = useMemo(() => {
    if (filter !== "all") return sortedRows.filter((r) => r.decision === filter);
    return sortedRows;
  }, [sortedRows, filter]);

  const counts = useMemo(() => ({
    total: rows.length,
    qualified: rows.filter((r) => r.decision === "qualified").length,
    watch: rows.filter((r) => r.decision === "watch").length,
    dropped: rows.filter((r) => r.decision === "dropped").length,
  }), [rows]);

  const filterItems: Array<{ key: "all" | "qualified" | "watch" | "dropped"; label: string; count: number; cls: string }> = [
    { key: "all", label: "All", count: counts.total, cls: "text-[#e2e8f0]" },
    { key: "qualified", label: "Interview / Offer", count: counts.qualified, cls: "text-emerald-400" },
    { key: "watch", label: "Applied / Watch", count: counts.watch, cls: "text-amber-300" },
    { key: "dropped", label: "Closed", count: counts.dropped, cls: "text-[#4B6A9B]" },
  ];

  return (
    <div className="space-y-4">
      {/* Summary stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {filterItems.map(({ key, label, count, cls }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`glass rounded-[10px] p-4 card-glow text-left transition-smooth ${filter === key ? "border border-[rgba(79,142,247,0.3)] bg-[rgba(79,142,247,0.08)]" : ""}`}
          >
            <p className="text-[10px] uppercase tracking-widest text-[#4B6A9B]">{label}</p>
            <p className={`text-3xl font-bold mt-1 ${cls}`}>{count}</p>
          </button>
        ))}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 text-sm flex-wrap">
        {(["all", "qualified", "watch", "dropped"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full border px-3 py-1 text-xs capitalize transition-smooth ${
              filter === f
                ? "border-[#4F8EF7] bg-[rgba(79,142,247,0.12)] text-[#a8c4e8]"
                : "border-[#1E2D45] text-[#4B6A9B] hover:text-[#6B8AAE] hover:border-[#2D4163]"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Pipeline card view */}
      <div className="glass rounded-[10px] p-4">
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">
          Pipeline ({filtered.length} entries)
        </h3>
        {loading && <p className="text-sm text-[#4B6A9B]">Loading pipeline from jobs-bank/pipeline.md...</p>}
        {error && <p className="mb-2 text-sm text-red-400">{error}</p>}
        {!loading && filtered.length === 0 && <p className="text-sm text-[#2D4163]">No entries in this filter.</p>}

        {/* Mobile card view */}
        <div className="space-y-2 md:hidden">
          {filtered.map((row) => {
            const age = ageLabel(row.ageHours);
            return (
              <div
                key={row.id}
                className={`glass-light rounded-[8px] p-3 transition-smooth card-glow ${row.decision === "dropped" ? "opacity-50" : ""}`}
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <p className="font-semibold text-[#e2e8f0] text-sm">{row.company}</p>
                  <span className={`shrink-0 rounded px-2 py-0.5 text-[10px] ${stageBadgeClass(row.stage)}`}>{row.stage}</span>
                </div>
                <p className="text-xs text-[#6B8AAE] mb-2">{row.role}</p>
                <div className="flex items-center gap-3 text-xs">
                  <AtsScoreBadge score={row.totalScore} decision={row.decision} />
                  <span className={`${age.cls}`}>{age.label}</span>
                  {row.appliedDate && <span className="text-[#2D4163]">{row.appliedDate}</span>}
                </div>
              </div>
            );
          })}
        </div>

        {/* Desktop table view */}
        <div className="overflow-auto hidden md:block">
          <table className="w-full text-left text-sm">
            <thead className="text-[10px] uppercase tracking-widest text-[#2D4163]">
              <tr>
                <th className="pb-3 pr-4">Company</th>
                <th className="pb-3 pr-4">Role</th>
                <th className="pb-3 pr-4">Stage</th>
                <th className="pb-3 pr-4">ATS</th>
                <th className="pb-3 pr-4">Applied</th>
                <th className="pb-3 pr-4">Follow-up</th>
                <th className="pb-3">Age</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => {
                const age = ageLabel(row.ageHours);
                return (
                  <tr
                    key={row.id}
                    className={`border-t border-[#1E2D45] transition-smooth hover:bg-[rgba(79,142,247,0.04)] ${row.decision === "dropped" ? "opacity-40" : ""}`}
                  >
                    <td className="py-2.5 pr-4 font-semibold text-[#e2e8f0]">{row.company}</td>
                    <td className="py-2.5 pr-4 text-xs text-[#6B8AAE] max-w-36 truncate">{row.role}</td>
                    <td className="py-2.5 pr-4">
                      <span className={`rounded px-2 py-0.5 text-[10px] ${stageBadgeClass(row.stage)}`}>{row.stage}</span>
                    </td>
                    <td className="py-2.5 pr-4">
                      <AtsScoreBadge score={row.totalScore} decision={row.decision} />
                    </td>
                    <td className="py-2.5 pr-4 text-xs text-[#4B6A9B]">{row.appliedDate || "-"}</td>
                    <td className="py-2.5 pr-4 text-xs text-[#4B6A9B]">{row.followUpDate || "-"}</td>
                    <td className={`py-2.5 text-xs ${age.cls}`}>{age.label}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
