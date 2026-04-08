import { NextResponse } from "next/server";
import { sqliteDb } from "@/lib/db";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const startDate = searchParams.get("startDate") || undefined;
    const endDate = searchParams.get("endDate") || undefined;
    const tasks = sqliteDb.getScheduledTasks(startDate, endDate);
    return NextResponse.json(tasks);
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch scheduled tasks" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const id = sqliteDb.addScheduledTask({
      taskId: body.taskId,
      title: body.title,
      scheduledDate: body.scheduledDate,
      scheduledTime: body.scheduledTime,
      type: body.type || "task",
      status: body.status || "scheduled",
      notes: body.notes,
      createdAt: new Date().toISOString(),
    });
    return NextResponse.json({ id, success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to create scheduled task" }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = parseInt(searchParams.get("id") || "");
    const body = await request.json();
    sqliteDb.updateScheduledTask(id, body);
    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to update scheduled task" }, { status: 500 });
  }
}

export async function DELETE(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = parseInt(searchParams.get("id") || "");
    if (id) sqliteDb.deleteScheduledTask(id);
    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to delete scheduled task" }, { status: 500 });
  }
}
