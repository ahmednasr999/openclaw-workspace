import { NextRequest, NextResponse } from "next/server";
import { createTask, loadTasks, updateTaskStatus } from "@/lib/task-store";
import { TaskStatus } from "@/lib/parity";

export const runtime = "nodejs";

const allowedPriorities = ["low", "medium", "high"] as const;
const allowedStatuses: TaskStatus[] = ["recurring", "backlog", "in_progress", "review", "done"];

function isTaskStatus(value: string): value is TaskStatus {
  return allowedStatuses.includes(value as TaskStatus);
}

export async function GET() {
  const tasks = await loadTasks();
  return NextResponse.json({ tasks, fetchedAt: new Date().toISOString() });
}

export async function POST(request: NextRequest) {
  const payload = await request.json().catch(() => null) as Record<string, string> | null;

  const title = String(payload?.title || "").trim();
  const assignee = String(payload?.assignee || "").trim();
  const priority = String(payload?.priority || "").trim();
  const dueDate = String(payload?.dueDate || "").trim();
  const status = String(payload?.status || "backlog").trim();

  if (!title || !assignee || !dueDate || !allowedPriorities.includes(priority as (typeof allowedPriorities)[number]) || !isTaskStatus(status)) {
    return NextResponse.json({ error: "Invalid task payload" }, { status: 400 });
  }

  const task = await createTask({
    title,
    assignee,
    priority: priority as (typeof allowedPriorities)[number],
    dueDate,
    status,
  });

  return NextResponse.json({ task }, { status: 201 });
}

export async function PATCH(request: NextRequest) {
  const payload = await request.json().catch(() => null) as Record<string, string> | null;
  const taskId = String(payload?.taskId || "").trim();
  const status = String(payload?.status || "").trim();

  if (!taskId || !isTaskStatus(status)) {
    return NextResponse.json({ error: "Invalid update payload" }, { status: 400 });
  }

  const task = await updateTaskStatus(taskId, status);

  if (!task) {
    return NextResponse.json({ error: "Task not found" }, { status: 404 });
  }

  return NextResponse.json({ task });
}
