import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export const dynamic = "force-dynamic";

// Master CV path
const MASTER_CV_PATH = "/root/.openclaw/workspace/memory/master-cv-data.md";

// Generate ATS-friendly HTML
function generateCVHTML(job: { title: string; company: string }, cvContent: string): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ahmed Nasr - CV for ${job.company}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.4; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
    h1 { font-size: 18pt; color: #1a1a1a; margin-bottom: 4px; }
    h2 { font-size: 12pt; color: #1a1a1a; border-bottom: 1px solid #ddd; padding-bottom: 4px; margin-top: 16px; }
    h3 { font-size: 11pt; color: #333; margin-top: 12px; }
    p, li { margin-bottom: 6px; }
    ul { margin-left: 20px; }
    .header { text-align: center; margin-bottom: 20px; }
    .contact { font-size: 10pt; color: #666; margin-bottom: 16px; }
    .section { margin-bottom: 16px; }
    .job-title { font-weight: bold; }
    .company { color: #666; }
    .date { float: right; color: #666; font-size: 10pt; }
    .skills { display: flex; flex-wrap: wrap; gap: 8px; }
    .skill { background: #f0f0f0; padding: 2px 8px; border-radius: 4px; font-size: 9pt; }
  </style>
</head>
<body>
  <div class="header">
    <h1>Ahmed Nasr</h1>
    <p class="contact">Senior Technology Executive | PMO & AI Automation | Saudi Arabia</p>
  </div>

  <div class="section">
    <h2>Professional Summary</h2>
    <p>Results-driven senior technology executive with 20+ years of experience in operational leadership, digital transformation, and program management. Proven track record of leading cross-functional teams, implementing enterprise solutions, and driving AI automation initiatives across healthcare and technology sectors. Expertise in PMO establishment, stakeholder management, and strategic planning.</p>
  </div>

  <div class="section">
    <h2>Core Competencies</h2>
    <div class="skills">
      <span class="skill">Program & Project Management</span>
      <span class="skill">Digital Transformation</span>
      <span class="skill">AI/ML Automation</span>
      <span class="skill">PMO Establishment</span>
      <span class="skill">Stakeholder Management</span>
      <span class="skill">Strategic Planning</span>
      <span class="skill">Cross-functional Leadership</span>
      <span class="skill">Budget Management ($50M+)</span>
    </div>
  </div>

  ${cvContent}

  <div class="section">
    <h2>Education</h2>
    <h3>Master of Business Administration (MBA)</h3>
    <p class="company">University, Year</p>
    <h3>Bachelor of Engineering</h3>
    <p class="company">University, Year</p>
  </div>

  <div class="section">
    <h2>Certifications</h2>
    <ul>
      <li>Project Management Professional (PMP)</li>
      <li>Certified Scrum Master (CSM)</li>
      <li>AI/ML Certifications</li>
    </ul>
  </div>

  <div style="text-align: center; margin-top: 24px; padding-top: 16px; border-top: 1px solid #ddd; font-size: 9pt; color: #999;">
    <p>This CV was tailored for ${job.title} at ${job.company}</p>
  </div>
</body>
</html>`;
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { job, content } = body;
    
    if (!job || !job.title || !job.company) {
      return NextResponse.json({ error: "job with title and company required" }, { status: 400 });
    }
    
    // Read master CV
    let cvContent = "";
    try {
      cvContent = fs.readFileSync(MASTER_CV_PATH, "utf-8");
      // Remove markdown formatting for cleaner output
      cvContent = cvContent
        .replace(/^##+\s/gm, "### ")
        .replace(/\*\*/g, "")
        .replace(/`([^`]+)`/g, "$1")
        .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
    } catch {
      cvContent = "<p>Master CV content not found</p>";
    }
    
    // Generate HTML
    const html = generateCVHTML(job, cvContent);
    
    // Save HTML file
    const filename = `Ahmed Nasr - ${job.title} - ${job.company}.html`.replace(/[^a-zA-Z0-9\s\-]/g, "");
    const outputDir = path.join(process.cwd(), "public/cv");
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    const filePath = path.join(outputDir, filename);
    fs.writeFileSync(filePath, html);
    
    return NextResponse.json({
      success: true,
      downloadUrl: `/cv/${filename}`,
      filename,
      html // Return HTML for browser PDF export
    });
  } catch (error) {
    console.error("PDF generation error:", error);
    return NextResponse.json({ error: "Failed to generate CV" }, { status: 500 });
  }
}
