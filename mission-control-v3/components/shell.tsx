import { ReactNode } from "react";
import { MissionShell } from "@/components/mission-shell";

export function Shell({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return <MissionShell title={title} description={description}>{children}</MissionShell>;
}
