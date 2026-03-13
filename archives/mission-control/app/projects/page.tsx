import { Shell } from "@/components/shell";
import { ProjectsPanels } from "@/components/module-panels";

export default function ProjectsPage() {
  return (
    <Shell title="Projects" description="Portfolio progress and linked execution items.">
      <ProjectsPanels />
    </Shell>
  );
}
