import { NextResponse } from "next/server";
import { sqliteDb } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const q = searchParams.get("q") || "";
    const category = searchParams.get("category") || undefined;
    const limit = parseInt(searchParams.get("limit") || "5", 10);

    if (!q || q.length < 2) {
      return NextResponse.json([]);
    }

    let results: any[] = [];

    if (category) {
      // Get latest from specific category
      results = sqliteDb.getAllKnowledge({ category, limit });
    } else {
      // Search across all
      results = sqliteDb.searchKnowledge(q, limit);
    }

    const parsed = results.map((r: any) => ({
      ...r,
      tags: r.tags ? JSON.parse(r.tags) : [],
    }));

    return NextResponse.json(parsed);
  } catch (error) {
    console.error("Agent knowledge search error:", error);
    return NextResponse.json([]);
  }
}
