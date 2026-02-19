import { NextResponse } from "next/server";
import { sqliteDb } from "@/lib/db";

export const dynamic = "force-dynamic";

const CATEGORIES = ["company", "content", "interview", "market", "outreach"];

// Quick knowledge capture for agents
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { category, title, content, tags, agentId, taskId } = body;

    if (!category || !title || !content) {
      return NextResponse.json({ error: "category, title, and content required" }, { status: 400 });
    }

    if (!CATEGORIES.includes(category)) {
      return NextResponse.json({ error: `Invalid category. Use: ${CATEGORIES.join(", ")}` }, { status: 400 });
    }

    const id = sqliteDb.addKnowledge({
      category,
      title,
      content,
      tags: tags ? JSON.stringify(tags) : undefined,
      agentId,
      taskId: taskId ? parseInt(String(taskId), 10) : undefined,
      sourceType: "agent",
      author: agentId || "Agent",
    });

    return NextResponse.json({ id, success: true });
  } catch (error) {
    console.error("Agent knowledge capture error:", error);
    return NextResponse.json({ error: "Failed to capture knowledge" }, { status: 500 });
  }
}
