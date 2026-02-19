import { NextResponse } from "next/server";
import { sqliteDb } from "@/lib/db";

export const dynamic = "force-dynamic";

const CATEGORIES = ["company", "content", "interview", "market", "outreach"];

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const category = searchParams.get("category") || undefined;
    const q = searchParams.get("q") || undefined;
    const limit = parseInt(searchParams.get("limit") || "50", 10);

    const items = sqliteDb.getAllKnowledge({ category, q, limit });

    // Parse tags JSON string back to array
    const parsed = items.map((i: any) => ({
      ...i,
      tags: i.tags ? JSON.parse(i.tags) : [],
    }));

    return NextResponse.json(parsed);
  } catch (error) {
    console.error("Knowledge GET error:", error);
    return NextResponse.json({ error: "Failed to fetch knowledge" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const {
      category,
      title,
      content,
      tags,
      agentId,
      taskId,
      sourceType = "agent",
      author = "System",
    } = body;

    if (!category || !title || !content) {
      return NextResponse.json({ error: "category, title, and content are required" }, { status: 400 });
    }

    if (!CATEGORIES.includes(category)) {
      return NextResponse.json({ error: `Invalid category. Must be: ${CATEGORIES.join(", ")}` }, { status: 400 });
    }

    const id = sqliteDb.addKnowledge({
      category,
      title,
      content,
      tags: tags ? JSON.stringify(tags) : undefined,
      agentId,
      taskId: taskId ? parseInt(String(taskId), 10) : undefined,
      sourceType,
      author,
    });

    return NextResponse.json({ id, success: true });
  } catch (error) {
    console.error("Knowledge POST error:", error);
    return NextResponse.json({ error: "Failed to create knowledge entry" }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = parseInt(searchParams.get("id") || "");
    const body = await request.json();

    if (!id) {
      return NextResponse.json({ error: "id is required" }, { status: 400 });
    }

    sqliteDb.updateKnowledge(id, body);
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Knowledge PATCH error:", error);
    return NextResponse.json({ error: "Failed to update knowledge" }, { status: 500 });
  }
}

export async function DELETE(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = parseInt(searchParams.get("id") || "");

    if (!id) {
      return NextResponse.json({ error: "id is required" }, { status: 400 });
    }

    sqliteDb.deleteKnowledge(id);
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Knowledge DELETE error:", error);
    return NextResponse.json({ error: "Failed to delete knowledge" }, { status: 500 });
  }
}
