import { Shell } from "@/components/shell";
import { HandoffGate } from "@/components/handoff-gate";

export default function HandoffGatePage() {
  return (
    <Shell title="Handoff Gate" description="Preflight URL checks and promotion guardrails.">
      <HandoffGate />
    </Shell>
  );
}
