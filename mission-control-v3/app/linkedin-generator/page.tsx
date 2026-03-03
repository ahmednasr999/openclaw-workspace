import { Shell } from "@/components/shell";
import { LinkedInGeneratorPanel } from "@/components/linkedin-factory";

export default function LinkedinGeneratorPage() {
  return (
    <Shell title="LinkedIn Generator" description="Safe generate mode and operator feedback.">
      <LinkedInGeneratorPanel />
    </Shell>
  );
}
