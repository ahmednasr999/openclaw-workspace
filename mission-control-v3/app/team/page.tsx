import { Shell } from "@/components/shell";
import { TeamPanel } from "@/components/module-panels";

export default function TeamPage() {
  return (
    <Shell title="Team" description="Agent workload, role coverage, and handoffs.">
      <TeamPanel />
    </Shell>
  );
}
