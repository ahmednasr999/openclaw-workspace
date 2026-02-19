import { NextResponse } from "next/server";
import { sqliteDb } from "@/lib/db";

export async function GET(_req: Request, { params }: { params: { id: string } }) {
  try {
    const activity = sqliteDb.getContentActivity(Number(params.id));
    return NextResponse.json(activity);
  } catch (error) {
    return NextResponse.json({ error: "Failed" }, { status: 500 });
  }
}

export async function POST(request: Request, { params }: { params: { id: string } }) {
  try {
    const { content, author } = await request.json();
    sqliteDb.addContentActivity(Number(params.id), "comment", content, author || "Ahmed");
    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed" }, { status: 500 });
  }
}
