import { NextResponse } from "next/server";
import Database from "better-sqlite3";
import path from "path";

const DB_PATH = path.join(process.cwd(), "mission-control.db");
const db = new Database(DB_PATH);

export const dynamic = "force-dynamic";

// Auto-create task for agent
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { title, description, agent, priority, category } = body;

    if (!title || !agent) {
      return NextResponse.json({ error: "title and agent required" }, { status: 400 });
    }

    const now = new Date().toISOString();
    const result = db.prepare(`
      INSERT INTO tasks (title, description, assignee, priority, category, status, createdAt, updatedAt)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      title,
      description || "",
      agent,
      priority || "Medium",
      category || "Task",
      "Pending",
      now,
      now
    );

    const task = db.prepare("SELECT * FROM tasks WHERE id = ?").get(result.lastInsertRowid);

    return NextResponse.json({
      success: true,
      task,
      message: `Task created for ${agent}`
    });
  } catch (error) {
    console.error("Create task error:", error);
    return NextResponse.json({ error: "Failed to create task" }, { status: 500 });
  }
}

// Get tasks for specific agent
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const agent = searchParams.get("agent");

    if (!agent) {
      return NextResponse.json({ error: "agent required" }, { status: 400 });
    }

    const tasks = db.prepare("SELECT * FROM tasks WHERE assignee = ? ORDER BY createdAt DESC").all(agent);

    return NextResponse.json({
      agent,
      taskCount: tasks.length,
      tasks
    });
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch tasks" }, { status: 500 });
  }
}
