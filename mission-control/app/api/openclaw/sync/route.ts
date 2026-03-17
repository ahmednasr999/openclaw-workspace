import { NextResponse } from "next/server";
import Database from "better-sqlite3";
import path from "path";

const DB_PATH = path.join(process.cwd(), "mission-control.db");
const db = new Database(DB_PATH);

export const dynamic = "force-dynamic";

// Track synced run IDs to avoid duplicates
db.exec(`
  CREATE TABLE IF NOT EXISTS agent_runs (
    runId TEXT PRIMARY KEY,
    label TEXT,
    task TEXT,
    model TEXT,
    createdAt TEXT
  )
`);

export async function GET(request: Request) {
  try {
    // Get all tracked runs
    const runs = db.prepare("SELECT * FROM agent_runs ORDER BY createdAt DESC LIMIT 20").all();
    
    return NextResponse.json({
      runCount: runs.length,
      runs
    });
  } catch (error) {
    return NextResponse.json({ error: "Failed to get runs" }, { status: 500 });
  }
}

// Sync new runs from OpenClaw and create tasks
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { runs } = body;

    if (!runs || !Array.isArray(runs)) {
      return NextResponse.json({ error: "runs array required" }, { status: 400 });
    }

    let created = 0;
    const now = new Date().toISOString();

    for (const run of runs) {
      const { runId, label, task, model } = run;
      
      // Check if already synced
      const existing = db.prepare("SELECT runId FROM agent_runs WHERE runId = ?").get(runId);
      if (existing) continue;

      // Extract agent name from label
      let agentName = "OpenClaw";
      if (label.includes("QA:")) {
        agentName = "QA Agent";
      } else if (label.includes("NASR")) {
        if (label.includes("Writer")) agentName = "NASR (Writer)";
        else if (label.includes("Research")) agentName = "NASR (Research)";
        else if (label.includes("CV")) agentName = "NASR (CV)";
        else agentName = "NASR (Coder)";
      }

      // Create task
      db.prepare(`
        INSERT INTO tasks (title, description, assignee, priority, category, status, createdAt, updatedAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `).run(
        label,
        `Auto-created from OpenClaw run (${runId}). Task: ${task || label}`,
        agentName,
        "Medium",
        "Task",
        "Pending",
        now,
        now
      );

      // Track the run
      db.prepare("INSERT OR IGNORE INTO agent_runs (runId, label, task, model, createdAt) VALUES (?, ?, ?, ?, ?)").run(
        runId, label, task || "", model || "", now
      );

      created++;
    }

    return NextResponse.json({
      success: true,
      synced: created,
      message: `Synced ${created} new runs`
    });
  } catch (error) {
    console.error("Sync error:", error);
    return NextResponse.json({ error: "Sync failed" }, { status: 500 });
  }
}
