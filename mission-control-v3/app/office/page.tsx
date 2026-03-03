import { Shell } from "@/components/shell";
import { OfficePanel } from "@/components/module-panels";

export default function OfficePage() {
  return (
    <Shell title="Office" description="Presence and operations room activity.">
      <OfficePanel />
    </Shell>
  );
}
