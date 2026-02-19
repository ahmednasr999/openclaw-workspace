import { NextResponse } from "next/server";
import Database from "better-sqlite3";
import path from "path";

const DB_PATH = path.join(process.cwd(), "mission-control.db");
const db = new Database(DB_PATH);

export const dynamic = "force-dynamic";

// Create QA review table
db.exec(`
  CREATE TABLE IF NOT EXISTS cv_qa_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cvId TEXT UNIQUE,
    jobTitle TEXT,
    company TEXT,
    atsScore INTEGER,
    matchedKeywords TEXT,
    missingKeywords TEXT,
    status TEXT DEFAULT 'pending',
    qaNotes TEXT,
    createdAt TEXT NOT NULL,
    updatedAt TEXT
  );
`);

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { cvId, jobTitle, company, atsScore, matchedKeywords, missingKeywords, html } = body;

    if (!cvId || !jobTitle || !company) {
      return NextResponse.json({ error: "cvId, jobTitle, and company required" }, { status: 400 });
    }

    // Save QA review request
    const now = new Date().toISOString();
    db.prepare(`
      INSERT OR REPLACE INTO cv_qa_reviews (cvId, jobTitle, company, atsScore, matchedKeywords, missingKeywords, status, createdAt, updatedAt)
      VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
    `).run(
      cvId,
      jobTitle,
      company,
      atsScore || 0,
      JSON.stringify(matchedKeywords || []),
      JSON.stringify(missingKeywords || []),
      now,
      now
    );

    return NextResponse.json({
      success: true,
      qaId: cvId,
      status: "pending",
      message: "CV submitted for QA review"
    });
  } catch (error) {
    console.error("QA submission error:", error);
    return NextResponse.json({ error: "Failed to submit for QA" }, { status: 500 });
  }
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const status = searchParams.get("status");
    const cvId = searchParams.get("cvId");

    let query = "SELECT * FROM cv_qa_reviews";
    const params: string[] = [];

    if (cvId) {
      query += " WHERE cvId = ?";
      params.push(cvId);
    } else if (status) {
      query += " WHERE status = ?";
      params.push(status);
    }

    query += " ORDER BY createdAt DESC";

    const reviews = db.prepare(query).all(...params);

    return NextResponse.json({
      reviews: reviews.map((r: any) => ({
        ...r,
        matchedKeywords: JSON.parse(r.matchedKeywords || "[]"),
        missingKeywords: JSON.parse(r.missingKeywords || "[]"),
      }))
    });
  } catch (error) {
    console.error("QA fetch error:", error);
    return NextResponse.json({ error: "Failed to fetch QA reviews" }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  try {
    const body = await request.json();
    const { cvId, status, qaNotes } = body;

    if (!cvId || !status) {
      return NextResponse.json({ error: "cvId and status required" }, { status: 400 });
    }

    const now = new Date().toISOString();
    db.prepare(`
      UPDATE cv_qa_reviews
      SET status = ?, qaNotes = ?, updatedAt = ?
      WHERE cvId = ?
    `).run(status, qaNotes || null, now, cvId);

    return NextResponse.json({
      success: true,
      cvId,
      status,
      updatedAt: now
    });
  } catch (error) {
    console.error("QA update error:", error);
    return NextResponse.json({ error: "Failed to update QA review" }, { status: 500 });
  }
}
