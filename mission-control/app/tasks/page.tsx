import { Shell } from "@/components/shell";
import { TaskBoard } from "@/components/task-board";

export default function TasksPage() {
  return (
    <Shell title="Board" description="WIP limits, drag transitions, telemetry, and live activity parity.">
      <TaskBoard />
    </Shell>
  );
}
