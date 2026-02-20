import { NextResponse } from "next/server";
import Database from "better-sqlite3";
import path from "path";

const DB_PATH = path.join(process.cwd(), "mission-control.db");
const db = new Database(DB_PATH);

export const dynamic = "force-dynamic";

// Auto-create task for agent when spawned
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
      description || `[Auto-created for ${agent}]`,
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
      message: `Auto-created task for ${agent}`
    });
  } catch (error) {
    console.error("Auto-create error:", error);
    return NextResponse.json({ error: "Failed to auto-create task" }, { status: 500 });
  }
}

// Get auto-created agent tasks
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const agent = searchParams.get("agent");

    let query = "SELECT * FROM tasks WHERE description LIKE '%Auto-created%'";
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
    return NextResponse.json({ error: "Failed to fetch tasks" }, { status: 500 });
  }
}
