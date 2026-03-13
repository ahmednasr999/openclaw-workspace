import { Shell } from "@/components/shell";
import { ContentFactoryPanel } from "@/components/linkedin-factory";

export default function ContentFactoryPage() {
  return (
    <Shell title="Content Factory" description="Funnel visibility and SLA cues.">
      <ContentFactoryPanel />
    </Shell>
  );
}
