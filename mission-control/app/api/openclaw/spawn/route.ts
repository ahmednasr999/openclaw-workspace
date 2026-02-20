import { NextResponse } from "next/server";
import Database from "better-sqlite3";
import path from "path";

const DB_PATH = path.join(process.cwd(), "mission-control.db");
const db = new Database(DB_PATH);

export const dynamic = "force-dynamic";

// Create task when OpenClaw spawns an agent
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { runId, label, task, model } = body;

    if (!runId || !label) {
      return NextResponse.json({ error: "runId and label required" }, { status: 400 });
    }

    // Extract agent name from label (e.g., "QA: Senior Manager at GMG" → "QA Agent")
    let agentName = "OpenClaw";
    if (label.includes("QA:")) {
      agentName = "QA Agent";
    } else if (label.includes("NASR")) {
      if (label.includes("Writer")) agentName = "NASR (Writer)";
      else if (label.includes("Research")) agentName = "NASR (Research)";
      else if (label.includes("CV")) agentName = "NASR (CV)";
      else agentName = "NASR (Coder)";
    }

    const now = new Date().toISOString();
    
    // Create task for the spawned agent
    const result = db.prepare(`
      INSERT INTO tasks (title, description, assignee, priority, category, status, createdAt, updatedAt)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      label,
      `Auto-created from OpenClaw spawn (${runId}). Task: ${task || label}`,
      agentName,
      "Medium",
      "Task",
      "Pending",
      now,
      now
    );

    const taskRecord = db.prepare("SELECT * FROM tasks WHERE id = ?").get(result.lastInsertRowid);

    return NextResponse.json({
      success: true,
      taskId: result.lastInsertRowid,
      runId,
      agent: agentName,
      message: `Task created for ${agentName}`
    });
  } catch (error) {
    console.error("Agent spawn hook error:", error);
    return NextResponse.json({ error: "Failed to create task from spawn" }, { status: 500 });
  }
}

// Get tasks created from agent spawns
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const agent = searchParams.get("agent");

    let query = "SELECT * FROM tasks WHERE description LIKE '%Auto-created from OpenClaw%'";
    const params: string[] = [];

    if (agent) {
      query += " AND assignee = ?";
      params.push(agent);
    }

    query += " ORDER BY createdAt DESC";

    const tasks = db.prepare(query).all(...params);

    return NextResponse.json({
      agent: agent || "all",
      taskCount: tasks.length,
      tasks
    });
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch agent tasks" }, { status: 500 });
  }
}
