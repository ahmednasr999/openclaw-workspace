import { Shell } from "@/components/shell";
import { Panel } from "@/components/ui";

export default function DashboardPage() {
  return (
    <Shell title="Dashboard" description="Snapshot of priorities, execution rhythm, and system health.">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[ ["Open tasks", "14"], ["Radar handoff-ready", "6"], ["SLA risk", "1"], ["Automation health", "97%"] ].map(([label, value]) => (
          <Panel key={label} title={label}><p className="text-3xl font-semibold text-zinc-100">{value}</p></Panel>
        ))}
      </div>
    </Shell>
  );
}
