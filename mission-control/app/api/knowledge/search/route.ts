import { NextResponse } from "next/server";
import { sqliteDb } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const q = searchParams.get("q") || "";
    const limit = parseInt(searchParams.get("limit") || "10", 10);

    if (!q || q.length < 2) {
      return NextResponse.json([]);
    }

    const results = sqliteDb.searchKnowledge(q, limit);

    // Parse tags JSON string back to array
    const parsed = results.map((r: any) => ({
      ...r,
      tags: r.tags ? JSON.parse(r.tags) : [],
    }));

    return NextResponse.json(parsed);
  } catch (error) {
    console.error("Knowledge search error:", error);
    return NextResponse.json([]);
  }
}
