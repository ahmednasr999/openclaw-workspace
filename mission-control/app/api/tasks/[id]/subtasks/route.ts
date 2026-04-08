import { NextResponse } from "next/server";
import { sqliteDb } from "@/lib/db";

export async function GET(request: Request, { params }: { params: { id: string } }) {
  try {
    const subtasks = sqliteDb.getSubtasks(Number(params.id));
    return NextResponse.json(subtasks);
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch subtasks" }, { status: 500 });
  }
}

export async function POST(request: Request, { params }: { params: { id: string } }) {
  try {
    const { title } = await request.json();
    const id = sqliteDb.addSubtask(Number(params.id), title);
    return NextResponse.json({ id, success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to add subtask" }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  try {
    const { subtaskId } = await request.json();
    const newVal = sqliteDb.toggleSubtask(Number(subtaskId));
    return NextResponse.json({ completed: newVal, success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to toggle subtask" }, { status: 500 });
  }
}

export async function DELETE(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const subtaskId = searchParams.get("subtaskId");
    if (subtaskId) sqliteDb.deleteSubtask(Number(subtaskId));
    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to delete subtask" }, { status: 500 });
  }
}
