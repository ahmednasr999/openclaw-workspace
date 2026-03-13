import { NextRequest, NextResponse } from "next/server";
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

export const runtime = "nodejs";

const allowed = ["docs", "memory", "team", "office", "projects", "tasks"] as const;
type AllowedKey = (typeof allowed)[number];

function isAllowedKey(value: string): value is AllowedKey {
  return allowed.includes(value as AllowedKey);
}

async function fetchModule(moduleName: AllowedKey) {
  switch (moduleName) {
    case "tasks": {
      const tasks = await getTasks();
      return tasks;
    }

    case "memory": {
      const mem = await getMemory();
      return parsedMemoryToMemoryEntries(mem);
    }

    case "projects": {
      const goals = await getGoals();
      return parsedGoalsToProjectEntries(goals);
    }

    case "team": {
      return await getAgentActivity();
    }

    case "office": {
      return await getOfficeMetrics();
    }

    case "docs": {
      return await getDocsIndex();
    }

    default:
      return [];
  }
}

export async function GET(request: NextRequest) {
  const moduleName = request.nextUrl.searchParams.get("module");

  if (!moduleName) {
    // Return all modules snapshot
    const [tasks, mem, goals, team, office, docs] = await Promise.all([
      getTasks(),
      getMemory(),
      getGoals(),
      getAgentActivity(),
      getOfficeMetrics(),
      getDocsIndex(),
    ]);

    const snapshot = {
      tasks,
      memory: parsedMemoryToMemoryEntries(mem),
      projects: parsedGoalsToProjectEntries(goals),
      team,
      office,
      docs,
    };

    return NextResponse.json({ snapshot, fetchedAt: new Date().toISOString() });
  }

  if (!isAllowedKey(moduleName)) {
    return NextResponse.json({ error: "Invalid module query" }, { status: 400 });
  }

  const data = await fetchModule(moduleName);
  return NextResponse.json({ data, fetchedAt: new Date().toISOString() });
}
