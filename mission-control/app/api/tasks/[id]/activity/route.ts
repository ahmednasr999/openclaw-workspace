import { NextResponse } from "next/server";
import { sqliteDb } from "@/lib/db";

export async function GET(request: Request, { params }: { params: { id: string } }) {
  try {
    const activity = sqliteDb.getActivity(Number(params.id));
    return NextResponse.json(activity);
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch activity" }, { status: 500 });
  }
}

export async function POST(request: Request, { params }: { params: { id: string } }) {
  try {
    const { content, author } = await request.json();
    sqliteDb.addActivity(Number(params.id), "comment", content, author || "Ahmed");
    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to add comment" }, { status: 500 });
  }
}
