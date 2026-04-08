import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const MASTER_CV_PATH = "/root/.openclaw/workspace/memory/master-cv-data.md";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { jobDescription, jobUrl } = body;

    if (!jobDescription) {
      return NextResponse.json({ error: "jobDescription required" }, { status: 400 });
    }

    // Read master CV
    let masterCV = "";
    try {
      masterCV = fs.readFileSync(MASTER_CV_PATH, "utf-8");
    } catch {
      return NextResponse.json({ error: "Master CV not found" }, { status: 500 });
    }

    // Build prompt for CV generation
    const prompt = `You are Ahmed Nasr's CV agent. Create a tailored CV HTML for this job.

## MASTER CV DATA:
${masterCV}

## JOB DESCRIPTION:
${jobDescription}

## YOUR TASK:
1. Analyze job requirements against master CV
2. Create ATS-friendly HTML CV tailored to this role
3. Output ONLY JSON with this structure:
{
  "jobTitle": "exact title from JD",
  "company": "company name from JD or Unknown",
  "atsScore": 0-100,
  "matchedKeywords": ["keyword1", "keyword2", ...],
  "missingKeywords": ["keyword1", "keyword2", ...],
  "html": "full ATS-compliant HTML CV"
}

## ATS REQUIREMENTS:
- Single column, no tables, no grids
- Standard headers: Professional Summary, Skills, Experience, Education, Certifications
- Simple bullets with AVR pattern
- Arial 11pt, black text on white
- No floating elements, no CSS grid
- Hyphens for dates (2020-2024), not em-dashes

## OUTPUT:
Return ONLY valid JSON (no markdown, no explanation).`;

    // Spawn sub-agent to generate CV
    try {
      const spawnRes = await fetch("http://localhost:3778/api/sessions/spawn", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task: prompt,
          model: "sonnet",
          label: `CV: ${jobDescription.substring(0, 50)}...`,
          cleanup: "delete",
          timeoutSeconds: 180,
        }),
      });

      if (spawnRes.ok) {
        const spawnData = await spawnRes.json();
        return NextResponse.json({
          success: true,
          status: "generating",
          runId: spawnData.runId,
          message: "CV generation started"
        });
      }
    } catch (e) {
      console.log("Sub-agent spawn failed, using fallback");
    }

    // Fallback: simple analysis without full CV generation
    const keywords = extractKeywords(jobDescription);
    const score = Math.min(60 + keywords.length * 2, 95);

    return NextResponse.json({
      success: true,
      status: "fallback",
      jobTitle: "Unknown Position",
      company: "Unknown Company",
      atsScore: score,
      matchedKeywords: keywords.slice(0, 10),
      missingKeywords: [],
      html: generateSimpleHTML(jobDescription, score),
      message: "Generated with basic template (sub-agent unavailable)"
    });
  } catch (error) {
    console.error("CV generation error:", error);
    return NextResponse.json({ error: "Failed to generate CV" }, { status: 500 });
  }
}

function extractKeywords(text: string): string[] {
  const keywords = new Set<string>();
  const patterns = [
    /project management/i, /program management/i, /pmo/i, /agile/i, /scrum/i,
    /digital transformation/i, /change management/i, /retail/i, /operations/i,
    /stakeholder/i, /leadership/i, /strategy/i, /kpi/i, /performance/i,
    /cross-functional/i, /process optimization/i, /data analytics/i,
    /stakeholder management/i, /budget/i, /revenue/i,
  ];

  for (const pattern of patterns) {
    if (pattern.test(text)) {
      const match = text.match(pattern);
      if (match) keywords.add(match[0]);
    }
  }

  return Array.from(keywords);
}

function generateSimpleHTML(jobDescription: string, score: number): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CV - Generated</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.5; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
    h1 { font-size: 18pt; color: #1a1a1a; }
    h2 { font-size: 12pt; color: #1a1a1a; border-bottom: 1px solid #ddd; padding-bottom: 4px; margin-top: 18px; }
    ul { margin-left: 18px; }
    li { margin-bottom: 6px; }
    .header { text-align: center; margin-bottom: 20px; }
    .contact { font-size: 10pt; color: #666; margin-bottom: 16px; }
  </style>
</head>
<body>
  <div class="header">
    <h1>Ahmed Nasr</h1>
    <p class="contact">Dubai, UAE | Contact info on file</p>
    <p><strong>ATS Score: ${score}/100</strong></p>
    <p>See full CV at Mission Control for complete profile</p>
  </div>
  <h2>Job Match</h2>
  <p>${jobDescription.substring(0, 500)}...</p>
</body>
</html>`;
}
