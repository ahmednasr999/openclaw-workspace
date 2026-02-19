import { NextResponse } from "next/server";
import { sqliteDb } from "@/lib/db";

// GET all tasks
export async function GET() {
  try {
    const tasks = sqliteDb.getAllTasks();
    return NextResponse.json(tasks);
  } catch (error) {
    console.error("Error fetching tasks:", error);
    return NextResponse.json({ error: "Failed to fetch tasks" }, { status: 500 });
  }
}

// POST add a task
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const taskId = sqliteDb.addTask(body);
    
    // Notify all connected clients by triggering an API call
    // The SSE endpoint will broadcast to all subscribers
    
    return NextResponse.json({ id: taskId, success: true });
  } catch (error) {
    console.error("Error adding task:", error);
    return NextResponse.json({ error: "Failed to add task" }, { status: 500 });
  }
}

// PUT update task status
export async function PUT(request: Request) {
  try {
    const body = await request.json();
    const { id, status, completedDate } = body;
    sqliteDb.updateStatus(Number(id), status, completedDate);
    
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error updating task:", error);
    return NextResponse.json({ error: "Failed to update task" }, { status: 500 });
  }
}

// DELETE a task
export async function DELETE(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get("id");
    if (id) {
      sqliteDb.deleteTask(Number(id));
    }
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error deleting task:", error);
    return NextResponse.json({ error: "Failed to delete task" }, { status: 500 });
  }
}
