import { NextResponse } from "next/server";
import Database from "better-sqlite3";
import path from "path";

const DB_PATH = path.join(process.cwd(), "mission-control.db");
const db = new Database(DB_PATH);

export const dynamic = "force-dynamic";

// Map agent IDs to task assignee names
const AGENT_LABEL_MAP: Record<string, string[]> = {
  "nasr": ["NASR (Coder)", "NASR"],
  "qa": ["QA Agent", "QA"],
  "scheduler": ["Scheduler", "scheduler"],
  "researcher": ["Research Agent", "researcher"],
  "writer": ["Writer Agent", "writer"],
  "cv": ["CV Agent", "cv"],
  "openclaw": ["OpenClaw", "OpenClaw Tasks"],
  "ahmed": ["Ahmed", "My Tasks"],
};

export async function GET() {
  try {
    // Read tasks directly from SQLite
    const tasks = db.prepare("SELECT * FROM tasks ORDER BY createdAt DESC").all();

    // Group tasks by assignee
    const agentRuns: any[] = [];

    for (const task of tasks as any[]) {
      const assignee = task.assignee || "Unassigned";
      
      // Map task status to run status
      let runStatus = "unknown";
      if (task.status === "In Progress") {
        runStatus = "running";
      } else if (task.status === "Completed") {
        runStatus = "completed";
      } else {
        runStatus = "pending";
      }

      // Add to runs list
      agentRuns.push({
        sessionKey: `task-${task.id}`,
        label: assignee,
        status: runStatus,
        updatedAt: task.createdAt,
        task: task.title,
        // Include agent ID for matching
        agentId: Object.entries(AGENT_LABEL_MAP)
          .find(([_, labels]) => labels.includes(assignee))?.[0] || null,
      });
    }

    return NextResponse.json({
      runs: agentRuns,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Error fetching agent status:", error);
    return NextResponse.json({ runs: [], error: "Failed to fetch agent status" });
  }
}
