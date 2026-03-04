import { Shell } from "@/components/shell";
import { DocsPanel } from "@/components/module-panels";

export default function DocsPage() {
  return (
    <Shell title="Docs" description="Repository browsing with active capability retention.">
      <DocsPanel />
    </Shell>
  );
}
