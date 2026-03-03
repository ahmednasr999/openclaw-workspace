"use client";

import { useEffect, useState } from "react";
import { Shell } from "@/components/shell";
import { Panel } from "@/components/ui";
import { CronJob } from "@/lib/types";

const integrations = [
  ["Gmail", "Connected"],
  ["Calendar", "Connected"],
  ["LinkedIn", "Needs relay"],
  ["OpenClaw Gateway", "Healthy"],
];

export default function SettingsPage() {
  const [cronRows, setCronRows] = useState<CronJob[]>([]);
  const [heartbeat, setHeartbeat] = useState("-");

  useEffect(() => {
    async function loadCron() {
      const response = await fetch("/api/cron-jobs", { cache: "no-store" });
      if (!response.ok) {
        return;
      }
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
        <Panel title="Integration status">
          <ul className="space-y-2 text-sm text-zinc-300">
            {integrations.map(([name, status]) => (
              <li key={name} className="flex items-center justify-between rounded border border-zinc-800 p-2">
                <span>{name}</span>
                <span className="text-zinc-400">{status}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-zinc-500">Heartbeat: {heartbeat}</p>
        </Panel>
        <Panel title="Cron manager monitor">
          <div className="overflow-auto">
            <table className="w-full text-left text-sm text-zinc-300">
              <thead className="text-zinc-500">
                <tr>
                  <th className="pb-2">Job</th>
                  <th className="pb-2">Schedule</th>
                  <th className="pb-2">Status</th>
                  <th className="pb-2">Failures</th>
                </tr>
              </thead>
              <tbody>
                {cronRows.map((row) => (
                  <tr key={row.id} className="border-t border-zinc-800">
                    <td className="py-2">{row.name}</td>
                    <td className="py-2">{row.schedule}</td>
                    <td className={row.status === "healthy" ? "text-emerald-400" : row.status === "failing" ? "text-red-400" : "text-zinc-400"}>{row.status}</td>
                    <td className="py-2">{row.consecutiveFailures}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </Shell>
  );
}
