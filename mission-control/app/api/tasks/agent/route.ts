import { NextResponse } from "next/server";
import { sqliteDb } from "@/lib/db";

/**
 * Agent Task API - used by NASR to create/update tasks when spawning sub-agents
 * 
 * POST: Create a task for an agent assignment
 * PATCH: Update task status (agent reports completion)
 */

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const {
      title,
      description,
      agent,        // e.g. "NASR (Coder)", "NASR (Writer)", "QA Agent"
      priority = "Medium",
      category = "Task",
      status = "In Progress",
      dueDate,
    } = body;

    if (!title) {
      return NextResponse.json({ error: "Title is required" }, { status: 400 });
    }

    const id = sqliteDb.addTask({
      title,
      description: description || undefined,
      assignee: agent || "OpenClaw",
      status,
      priority,
      category,
      dueDate: dueDate || undefined,
      createdAt: new Date().toISOString(),
    });

    // Log the agent assignment
    sqliteDb.addActivity(id as number, "agent_assigned", `Assigned to ${agent || "OpenClaw"}`, "NASR");

    return NextResponse.json({ id, success: true });
  } catch (error) {
    console.error("Agent task creation error:", error);
    return NextResponse.json({ error: "Failed to create agent task" }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  try {
    const body = await request.json();
    const { taskId, status, result, agent, knowledge } = body;

    if (!taskId || !status) {
      return NextResponse.json({ error: "taskId and status required" }, { status: 400 });
    }

    const completedDate = status === "Completed" ? new Date().toISOString() : undefined;
    sqliteDb.updateStatus(taskId, status, completedDate);

    if (result) {
      sqliteDb.addActivity(taskId, "agent_result", `${agent || "Agent"}: ${result}`, agent || "System");
    }

    // Auto-capture knowledge if provided
    if (knowledge && knowledge.category && knowledge.title && knowledge.content) {
      sqliteDb.addKnowledge({
        category: knowledge.category,
        title: knowledge.title,
        content: knowledge.content,
        tags: knowledge.tags ? JSON.stringify(knowledge.tags) : undefined,
        agentId: agent || undefined,
        taskId: parseInt(String(taskId), 10),
        sourceType: "agent",
        author: agent || "System",
      });
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Agent task update error:", error);
    return NextResponse.json({ error: "Failed to update task" }, { status: 500 });
  }
}
