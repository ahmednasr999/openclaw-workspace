import { Shell } from "@/components/shell";
import { MemoryPanels } from "@/components/module-panels";

export default function MemoryPage() {
  return (
    <Shell title="Memory" description="Recent decisions, context links, and open follow-ups.">
      <MemoryPanels />
    </Shell>
  );
}
