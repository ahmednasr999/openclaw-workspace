import { NextResponse } from "next/server";
import Database from "better-sqlite3";
import path from "path";
import { execSync } from "child_process";

const DB_PATH = path.join(process.cwd(), "mission-control.db");
const db = new Database(DB_PATH);

db.exec(`
  CREATE TABLE IF NOT EXISTS cv_qa_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cvId TEXT UNIQUE,
    jobTitle TEXT,
    company TEXT,
    atsScore INTEGER,
    matchedKeywords TEXT,
    missingKeywords TEXT,
    pdfUrl TEXT,
    status TEXT DEFAULT 'pending',
    qaVerdict TEXT,
    qaScore INTEGER,
    qaNotes TEXT,
    qaIssues TEXT,
    qaRecommendations TEXT,
    createdAt TEXT NOT NULL,
    updatedAt TEXT
  );
`);

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { cvId, jobTitle, company, atsScore, matchedKeywords, missingKeywords, pdfUrl } = body;

    if (!cvId || !jobTitle || !company) {
      return NextResponse.json({ error: "cvId, jobTitle, and company required" }, { status: 400 });
    }

    const now = new Date().toISOString();
    
    db.prepare(`
      INSERT OR REPLACE INTO cv_qa_reviews 
      (cvId, jobTitle, company, atsScore, matchedKeywords, missingKeywords, pdfUrl, status, createdAt, updatedAt)
      VALUES (?, ?, ?, ?, ?, ?, ?, 'spawning', ?, ?)
    `).run(cvId, jobTitle, company, atsScore || 0, JSON.stringify(matchedKeywords || []), JSON.stringify(missingKeywords || []), pdfUrl || "", now, now);

    // Build QA prompt
    const prompt = `You are an expert CV reviewer. Review this tailored CV and return ONLY JSON:

{
  "verdict": "APPROVED|REJECTED|REQUEST_CHANGES",
  "score": 0-100,
  "qaNotes": "Brief summary",
  "issues": ["issue1", "issue2"],
  "recommendations": ["rec1", "rec2"]
}

**Position:** ${jobTitle}
**Company:** ${company}
**ATS Score:** ${atsScore || "N/A"}/100

**Matched:** ${matchedKeywords?.slice(0, 10).join(", ") || "None"}
**Missing:** ${missingKeywords?.slice(0, 10).join(", ") || "None"}

Review criteria:
- ATS compliance (no tables, single column)
- Critical keywords present
- Relevant experience
- Quantified achievements

Return ONLY JSON. No markdown.`;

    // Spawn QA Agent sub-session via OpenClaw sessions_spawn
    try {
      const spawnResult = execSync(
        `curl -s -X POST "http://localhost:3778/api/sessions/spawn" \
          -H "Content-Type: application/json" \
          -d '{"task":"${prompt.replace(/"/g, '\\"')}", "model":"sonnet", "label":"QA: ${jobTitle}", "cleanup":"delete", "timeoutSeconds":120}'`,
        { encoding: "utf-8", timeout: 10000 }
      );
      
      const spawnData = JSON.parse(spawnResult);
      
      if (spawnData.runId) {
        db.prepare(`UPDATE cv_qa_reviews SET qaNotes = ?, updatedAt = ? WHERE cvId = ?`)
          .run(`QA Agent running (${spawnData.runId})`, now, cvId);

        return NextResponse.json({
          success: true,
          qaId: cvId,
          status: "pending",
          runId: spawnData.runId,
          message: "QA Agent spawned"
        });
      }
    } catch (spawnError) {
      console.log("QA Agent spawn failed, using fallback:", spawnError);
    }

    // Fallback: Auto QA based on ATS score
    const verdict = atsScore >= 80 ? "APPROVED" : atsScore >= 60 ? "REQUEST_CHANGES" : "REJECTED";
    const notes = verdict === "APPROVED" ? "Auto-approved: Strong ATS match" 
      : verdict === "REQUEST_CHANGES" ? "Consider keyword improvements" 
      : "Weak match - review recommended";

    db.prepare(`
      UPDATE cv_qa_reviews 
      SET status = ?, qaVerdict = ?, qaScore = ?, qaNotes = ?, updatedAt = ?
      WHERE cvId = ?
    `).run(verdict.toLowerCase() === "approved" ? "approved" : verdict === "REJECTED" ? "rejected" : "changes_requested", verdict, atsScore || 70, notes, now, cvId);

    return NextResponse.json({
      success: true,
      qaId: cvId,
      status: verdict.toLowerCase() === "approved" ? "approved" : verdict === "REJECTED" ? "rejected" : "changes_requested",
      verdict,
      score: atsScore || 70,
      message: "QA completed (fallback)"
    });
  } catch (error) {
    console.error("QA error:", error);
    return NextResponse.json({ error: "QA failed" }, { status: 500 });
  }
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const cvId = searchParams.get("cvId");

    if (cvId) {
      const review: any = db.prepare("SELECT * FROM cv_qa_reviews WHERE cvId = ?").get(cvId);
      if (!review) return NextResponse.json({ error: "Not found" }, { status: 404 });
      
      return NextResponse.json({
        review: {
          ...review,
          matchedKeywords: JSON.parse(review.matchedKeywords || "[]"),
          missingKeywords: JSON.parse(review.missingKeywords || "[]"),
          qaIssues: review.qaIssues ? JSON.parse(review.qaIssues) : [],
          qaRecommendations: review.qaRecommendations ? JSON.parse(review.qaRecommendations) : [],
        }
      });
    }

    const reviews = db.prepare("SELECT * FROM cv_qa_reviews ORDER BY createdAt DESC").all();
    return NextResponse.json({
      reviews: reviews.map((r: any) => ({
        ...r,
        matchedKeywords: JSON.parse(r.matchedKeywords || "[]"),
        missingKeywords: JSON.parse(r.missingKeywords || "[]"),
        qaIssues: r.qaIssues ? JSON.parse(r.qaIssues) : [],
        qaRecommendations: r.qaRecommendations ? JSON.parse(r.qaRecommendations) : [],
      }))
    });
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch" }, { status: 500 });
  }
}

export async function PUT(request: Request) {
  try {
    const body = await request.json();
    const { cvId, verdict, score, qaNotes, issues, recommendations } = body;

    const now = new Date().toISOString();
    db.prepare(`
      UPDATE cv_qa_reviews
      SET status = ?, qaVerdict = ?, qaScore = ?, qaNotes = ?, qaIssues = ?, qaRecommendations = ?, updatedAt = ?
      WHERE cvId = ?
    `).run(
      verdict === "APPROVED" ? "approved" : verdict === "REJECTED" ? "rejected" : "changes_requested",
      verdict,
      score,
      qaNotes,
      JSON.stringify(issues || []),
      JSON.stringify(recommendations || []),
      now,
      cvId
    );

    return NextResponse.json({ success: true, cvId, status: verdict.toLowerCase() });
  } catch (error) {
    return NextResponse.json({ error: "Update failed" }, { status: 500 });
  }
}
