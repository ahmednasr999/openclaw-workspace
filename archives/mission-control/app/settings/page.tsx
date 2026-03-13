"use client";

import { useEffect, useState } from "react";
import { Shell } from "@/components/shell";
import { CronJob } from "@/lib/types";

const integrations = [
  { name: "Gmail", status: "Connected", healthy: true },
  { name: "Calendar", status: "Connected", healthy: true },
  { name: "LinkedIn", status: "Needs relay", healthy: false },
  { name: "OpenClaw Gateway", status: "Healthy", healthy: true },
];

function CronStatusDot({ status }: { status: string }) {
  if (status === "healthy") {
    return <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse inline-block animate-glow-green" />;
  }
  if (status === "failing") {
    return <span className="h-2.5 w-2.5 rounded-full bg-red-500 animate-glow-red inline-block" />;
  }
  return <span className="h-2.5 w-2.5 rounded-full bg-[#2D4163] inline-block" />;
}

function CronStatusLabel({ status }: { status: string }) {
  if (status === "healthy") return <span className="text-emerald-400 text-xs font-medium">healthy</span>;
  if (status === "failing") return <span className="text-red-400 text-xs font-semibold">FAILING</span>;
  return <span className="text-[#4B6A9B] text-xs">paused</span>;
}

function formatCountdown(nextRun: string | undefined): string {
  if (!nextRun) return "-";
  const diff = new Date(nextRun).getTime() - Date.now();
  if (diff <= 0) return "now";
  const mins = Math.floor(diff / 60000);
  const secs = Math.floor((diff % 60000) / 1000);
  if (mins > 60) return `${Math.floor(mins / 60)}h ${mins % 60}m`;
  return `${mins}m ${secs}s`;
}

function NextRunCountdown({ nextRun }: { nextRun?: string }) {
  const [countdown, setCountdown] = useState<string>(formatCountdown(nextRun));

  useEffect(() => {
    function update() {
      setCountdown(formatCountdown(nextRun));
    }

    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [nextRun]);

  return <span className="ts text-[#4B6A9B]">{countdown}</span>;
}

export default function SettingsPage() {
  const [cronRows, setCronRows] = useState<CronJob[]>([]);
  const [heartbeat, setHeartbeat] = useState("-");

  useEffect(() => {
    async function loadCron() {
      const response = await fetch("/api/cron-jobs", { cache: "no-store" });
      if (!response.ok) return;
      const payload = await response.json() as { cronJobs: CronJob[]; heartbeat: { status: string } };
      setCronRows(payload.cronJobs || []);
      setHeartbeat(payload.heartbeat?.status || "-");
    }

    loadCron();
    const interval = setInterval(loadCron, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Shell title="Settings" description="Integration health and cron monitor for failure transitions.">
      <div className="grid gap-4 xl:grid-cols-2">
        {/* Integration status */}
        <div className="glass rounded-[10px] p-4 card-glow">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">Integration status</h3>
          <ul className="space-y-2">
            {integrations.map(({ name, status, healthy }) => (
              <li key={name} className="glass-light rounded-[8px] p-2.5 flex items-center justify-between transition-smooth">
                <div className="flex items-center gap-2.5">
                  <span className={`h-2 w-2 rounded-full ${healthy ? "bg-emerald-400" : "bg-amber-400"}`} />
                  <span className="text-xs text-[#e2e8f0]">{name}</span>
                </div>
                <span className={`text-xs ${healthy ? "text-emerald-400" : "text-amber-300"}`}>{status}</span>
              </li>
            ))}
          </ul>
          <div className="mt-3 pt-3 border-t border-[#1E2D45] flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${heartbeat === "healthy" ? "bg-emerald-400 animate-pulse" : "bg-red-500 animate-glow-red"}`} />
            <span className="text-[10px] text-[#4B6A9B]">Gateway heartbeat: {heartbeat}</span>
          </div>
        </div>

        {/* Cron monitor */}
        <div className="glass rounded-[10px] p-4 card-glow">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">Cron manager monitor</h3>
          {cronRows.length === 0 ? (
            <p className="text-sm text-[#2D4163]">No cron jobs found.</p>
          ) : (
            <div className="space-y-2">
              {cronRows.map((row) => (
                <div key={row.id} className={`glass-light rounded-[8px] p-3 transition-smooth ${row.status === "failing" ? "border border-red-800/40" : "border border-transparent"}`}>
                  <div className="flex items-center justify-between gap-3 mb-1">
                    <div className="flex items-center gap-2">
                      <CronStatusDot status={row.status} />
                      <span className="text-xs font-medium text-[#e2e8f0]">{row.name}</span>
                    </div>
                    <CronStatusLabel status={row.status} />
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <span className="ts text-[#2D4163]">{row.schedule}</span>
                    <div className="flex items-center gap-3">
                      {row.consecutiveFailures > 0 && (
                        <span className="text-[10px] text-red-400">{row.consecutiveFailures} fails</span>
                      )}
                      <div className="flex items-center gap-1">
                        <span className="text-[10px] text-[#2D4163]">next:</span>
                        <NextRunCountdown nextRun={row.nextRunAt} />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Shell>
  );
}
