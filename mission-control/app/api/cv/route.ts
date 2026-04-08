import { NextResponse } from "next/server";
import { sqliteDb } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get("id");
    const limit = parseInt(searchParams.get("limit") || "50", 10);

    if (id) {
      const entry = sqliteDb.getCVHistoryById(parseInt(id)) as {
        id: number;
        jobTitle: string;
        company: string;
        jobUrl?: string;
        atsScore?: number;
        matchedKeywords?: string;
        missingKeywords?: string;
        pdfPath?: string;
        status: string;
        notes?: string;
        createdAt: string;
      } | undefined;
      if (!entry) {
        return NextResponse.json({ error: "Not found" }, { status: 404 });
      }
      // Parse JSON strings back to arrays
      const parsed = {
        ...entry,
        matchedKeywords: entry.matchedKeywords ? JSON.parse(entry.matchedKeywords) : [],
        missingKeywords: entry.missingKeywords ? JSON.parse(entry.missingKeywords) : [],
      };
      return NextResponse.json(parsed);
    }

    const entries = sqliteDb.getAllCVHistory(limit) as Array<{
      id: number;
      jobTitle: string;
      company: string;
      jobUrl?: string;
      atsScore?: number;
      matchedKeywords?: string;
      missingKeywords?: string;
      pdfPath?: string;
      status: string;
      notes?: string;
      createdAt: string;
    }>;
    const parsed = entries.map((e) => ({
      ...e,
      matchedKeywords: e.matchedKeywords ? JSON.parse(e.matchedKeywords) : [],
      missingKeywords: e.missingKeywords ? JSON.parse(e.missingKeywords) : [],
    }));

    return NextResponse.json(parsed);
  } catch (error) {
    console.error("CV history GET error:", error);
    return NextResponse.json({ error: "Failed to fetch CV history" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { jobTitle, company, jobUrl, atsScore, matchedKeywords, missingKeywords, pdfPath, status, notes } = body;

    if (!jobTitle || !company) {
      return NextResponse.json({ error: "jobTitle and company are required" }, { status: 400 });
    }

    const id = sqliteDb.addCVHistory({
      jobTitle,
      company,
      jobUrl,
      atsScore,
      matchedKeywords,
      missingKeywords,
      pdfPath,
      status: status || "Generated",
      notes,
    });

    return NextResponse.json({ id, success: true });
  } catch (error) {
    console.error("CV history POST error:", error);
    return NextResponse.json({ error: "Failed to create CV history" }, { status: 500 });
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

    sqliteDb.updateCVHistory(id, body);
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("CV history PATCH error:", error);
    return NextResponse.json({ error: "Failed to update CV history" }, { status: 500 });
  }
}

export async function DELETE(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = parseInt(searchParams.get("id") || "");

    if (!id) {
      return NextResponse.json({ error: "id is required" }, { status: 400 });
    }

    sqliteDb.deleteCVHistory(id);
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("CV history DELETE error:", error);
    return NextResponse.json({ error: "Failed to delete CV history" }, { status: 500 });
  }
}
