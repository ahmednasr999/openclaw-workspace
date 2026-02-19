import { NextResponse } from "next/server";
import { sqliteDb } from "@/lib/db";

export async function GET(request: Request, { params }: { params: { id: string } }) {
  try {
    const id = parseInt(params.id);
    const activity = sqliteDb.getContactActivity(id);
    return NextResponse.json(activity);
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch activity" }, { status: 500 });
  }
}

export async function POST(request: Request, { params }: { params: { id: string } }) {
  try {
    const id = parseInt(params.id);
    const body = await request.json();
    sqliteDb.addContactActivity(id, body.type || "note", body.content, body.author || "User");
    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to add activity" }, { status: 500 });
  }
}
