import { Shell } from "@/components/shell";
import { CalendarBoard } from "@/components/calendar-board";

export default function CalendarPage() {
  return (
    <Shell
      title="Calendar"
      description="Unified calendar for tasks, content, meetings, and automations with interactive scheduling."
    >
      <CalendarBoard />
    </Shell>
  );
}
