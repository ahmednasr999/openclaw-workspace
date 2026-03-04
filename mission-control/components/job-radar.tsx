"use client";

import { useEffect, useMemo, useState } from "react";
import { Panel } from "@/components/ui";
import { JobRadarLead } from "@/lib/types";

function urgency(ageHours: number) {
  if (ageHours <= 8) return { label: "fresh", cls: "text-emerald-400" };
  if (ageHours <= 24) return { label: "warm", cls: "text-amber-300" };
  return { label: "aging", cls: "text-red-400" };
}

export function JobRadar() {
  const [rows, setRows] = useState<JobRadarLead[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const response = await fetch("/api/job-radar", { cache: "no-store" });
        if (!response.ok) {
          throw new Error("Failed to load job radar");
        }
        const payload = await response.json() as { leads: JobRadarLead[] };
        setRows(payload.leads || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      }
    }

    load();
  }, []);

  const sorted = useMemo(() => [...rows].sort((a, b) => a.ageHours - b.ageHours), [rows]);

  return (
    <Panel title="Urgency-first job radar">
      {error && <p className="mb-2 text-sm text-red-400">{error}</p>}
      <div className="overflow-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-zinc-500"><tr><th>Role</th><th>Company</th><th>Urgency</th><th>Decision</th><th>Score trace</th><th>Dropped reason</th></tr></thead>
          <tbody>
            {sorted.map((row) => {
              const u = urgency(row.ageHours);
              return (
                <tr key={row.id} className="border-t border-zinc-800">
                  <td className="py-2">{row.role}</td><td>{row.company}</td>
                  <td className={`font-medium ${u.cls}`}>{u.label} ({row.ageHours}h)</td>
                  <td className={row.decision === "qualified" ? "text-emerald-400" : row.decision === "watch" ? "text-amber-300" : "text-red-400"}>{row.decision}</td>
                  <td>{row.totalScore}/{row.threshold} (S {row.salaryFit}, F {row.strategicFit}, Q {row.sourceQuality})</td>
                  <td>{row.droppedReason || "-"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
