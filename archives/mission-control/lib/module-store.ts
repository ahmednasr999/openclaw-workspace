// module-store.ts: Legacy compatibility shim
// New code uses lib/sync directly. This file is kept for any remaining imports.

import {
  getTasks,
  getMemory,
  getGoals,
  getAgentActivity,
  getOfficeMetrics,
  getDocsIndex,
} from "@/lib/sync";
import {
  parsedMemoryToMemoryEntries,
  parsedGoalsToProjectEntries,
} from "@/lib/sync/parsers";
import type { ModuleSnapshot } from "@/lib/types";

export async function loadModuleSnapshot(): Promise<ModuleSnapshot> {
  const [tasks, mem, goals, team, office, docs] = await Promise.all([
    getTasks(),
    getMemory(),
    getGoals(),
    getAgentActivity(),
    getOfficeMetrics(),
    getDocsIndex(),
  ]);

  return {
    tasks,
    memory: parsedMemoryToMemoryEntries(mem),
    projects: parsedGoalsToProjectEntries(goals),
    team,
    office,
    docs,
  };
}
