import { Shell } from "@/components/shell";
import { JobRadar } from "@/components/job-radar";

export default function JobRadarPage() {
  return (
    <Shell title="Job Radar" description="Urgency-first queue with dropped reasons and snapshots.">
      <JobRadar />
    </Shell>
  );
}
