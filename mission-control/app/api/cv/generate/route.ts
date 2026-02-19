import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export const dynamic = "force-dynamic";

// Master CV path
const MASTER_CV_PATH = "/root/.openclaw/workspace/memory/master-cv-data.md";

// Extract keywords from text
function extractKeywords(text: string): string[] {
  const keywords = new Set<string>();
  
  // Common skills and keywords to look for
  const skillPatterns = [
    /project management/i, /program management/i, /pmo/i, /agile/i, /scrum/i, /kanban/i,
    /leadership/i, /strategy/i, /strategic/i, /vision/i,
    /digital transformation/i, /digital/i, /automation/i,
    /ai[^\w]/gi, /artificial intelligence/i, /machine learning/i, /ml\b/gi,
    /stakeholder management/i, /stakeholders/i, /executive/i, /senior management/i,
    /budget/i, /financial/i, /revenue/i, /cost/i,
    /team leadership/i, /team management/i, /people management/i,
    /cross-functional/i, /cross functional/i, /matrix/i,
    /cloud/i, /aws/i, /azure/i, /gcp/i,
    /erp/i, /crm/i, /sap/i, /oracle/i,
    /healthcare/i, /hospital/i, /medical/i,
    /saudi/i, /gcc/i, /middle east/i, /mea/i,
    /operations/i, /ops\b/gi, /process improvement/i, /lean/i, /six sigma/i,
    /risk management/i, /compliance/i, /governance/i,
    /data analytics/i, /bi\b/gi, /dashboard/i, /reporting/i,
    /change management/i, /transformation/i, /turnaround/i,
    /vendor management/i, /procurement/i, /outsourcing/i,
    /customer experience/i, /cx\b/gi, /patient experience/i,
    /technology/i, /tech\b/gi, /it\b/gi, /software/i, /hardware/i,
    /engineering/i, /technical/i,
    /mba/i, /bachelor/i, /master/i, /phd/i, /degree/i,
    /pmp/i, /prince2/i, /csm/i, /six sigma black belt/i, /certification/i,
    /15\+ years/i, /10\+ years/i, /8\+ years/i, /5\+ years/i,
    /english/i, /arabic/i, /fluent/i, /native/i,
  ];
  
  for (const pattern of skillPatterns) {
    if (pattern.test(text)) {
      const match = text.match(pattern);
      if (match) {
        keywords.add(match[0].trim().toLowerCase());
      }
    }
  }
  
  // Extract from bullet points
  const lines = text.split("\n");
  for (const line of lines) {
    // Skip headers
    if (line.match(/^#{1,6}\s/)) continue;
    
    // Look for action verbs and responsibilities
    const verbs = ["led", "managed", "directed", "oversaw", "championed", "spearheaded", "delivered", "achieved", "improved", "increased", "reduced", "implemented", "established", "developed", "created", "built", "launched", "transformed", "optimized", "streamlined", "orchestrated", "coordinated"];
    
    const lineLower = line.toLowerCase();
    if (verbs.some(v => lineLower.includes(v + " "))) {
      // Extract key terms from responsibility lines
      const words = line.split(/\s+/);
      for (let i = 0; i < words.length; i++) {
        if (words[i].length > 3 && !["and", "the", "for", "with", "that", "this", "from", "have", "been", "were", "they", "their"].includes(words[i].toLowerCase())) {
          keywords.add(words[i].replace(/[^a-zA-Z]/g, "").toLowerCase());
        }
      }
    }
  }
  
  return Array.from(keywords).filter(k => k.length > 2);
}

// Parse master CV
function parseMasterCV(): { keywords: string[], skills: string[], experience: any[] } {
  try {
    const content = fs.readFileSync(MASTER_CV_PATH, "utf-8");
    const keywords = extractKeywords(content);
    
    // Extract skills section
    const skillsMatch = content.match(/## Skills\s*\n([\s\S]*?)##/);
    const skills = skillsMatch ? extractKeywords(skillsMatch[1]) : [];
    
    // Extract experience
    const expMatch = content.match(/## Experience\s*\n([\s\S]*?)##/);
    const experience: any[] = [];
    
    if (expMatch) {
      const expLines = expMatch[1].split("\n## ");
      for (const exp of expLines) {
        const titleMatch = exp.match(/^(.+?)\s*[-–]\s*(.+?)\s*(\d{4})/);
        if (titleMatch) {
          experience.push({
            title: titleMatch[1].trim(),
            company: titleMatch[2].trim(),
            year: titleMatch[3],
            keywords: extractKeywords(exp)
          });
        }
      }
    }
    
    return { keywords, skills, experience };
  } catch (error) {
    console.error("Error parsing master CV:", error);
    return { keywords: [], skills: [], experience: [] };
  }
}

// Calculate ATS score
function calculateATSScore(jobKeywords: string[], cvKeywords: string[]): { score: number; matched: string[]; missing: string[] } {
  const jobSet = new Set(jobKeywords.map(k => k.toLowerCase()));
  const cvSet = new Set(cvKeywords.map(k => k.toLowerCase()));
  
  const matched: string[] = [];
  const missing: string[] = [];
  
  for (const keyword of jobKeywords) {
    if (cvSet.has(keyword.toLowerCase())) {
      matched.push(keyword);
    } else {
      missing.push(keyword);
    }
  }
  
  // Score calculation
  const relevanceScore = matched.length / Math.max(jobKeywords.length, 1) * 70;
  const coverageBonus = Math.min(
    cvKeywords.filter(k => 
      jobKeywords.some(jk => jk.toLowerCase() === k.toLowerCase())
    ).length / 5 * 30,
    30
  );
  
  const score = Math.min(Math.round(relevanceScore + coverageBonus), 100);
  
  return { score, matched, missing };
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { url, description } = body;
    
    if (!url && !description) {
      return NextResponse.json({ error: "url or description required" }, { status: 400 });
    }
    
    // Fetch job posting
    let jobContent = description || "";
    let jobTitle = "Unknown Position";
    let companyName = "Unknown Company";
    
    if (url) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        const fetchRes = await fetch(url, { signal: controller.signal });
        clearTimeout(timeoutId);
        if (fetchRes.ok) {
          const html = await fetchRes.text();
          
          // Extract title
          const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
          if (titleMatch) {
            jobTitle = titleMatch[1].trim();
            // Clean up common patterns
            jobTitle = jobTitle.replace(/\s*[-|]\s*LinkedIn.*$/i, "");
            jobTitle = jobTitle.replace(/\s*[-|]\s*careers.*$/i, "");
          }
          
          // Extract company from meta tags or og:site_name
          const companyMatch = html.match(/<meta[^>]*property=["']og:site_name["'][^>]*content=["']([^"']+)["']/i) ||
                             html.match(/<meta[^>]*name=["']company["'][^>]*content=["']([^"']+)["']/i);
          if (companyMatch) {
            companyName = companyMatch[1].trim();
          }
          
          // Extract job description from common containers
          const descPatterns = [
            /<div[^>]*class="[^"]*description[^"]*"[^>]*>([\s\S]*?)<\/div>/i,
            /<section[^>]*id="[^"]*job[^"]*description[^"]*"[^>]*>([\s\S]*?)<\/section>/i,
            /<div[^>]*data-test-id="[^"]*job[^"]*description[^"]*"[^>]*>([\s\S]*?)<\/div>/i,
          ];
          
          for (const pattern of descPatterns) {
            const match = html.match(pattern);
            if (match) {
              // Strip HTML tags
              jobContent = match[1]
                .replace(/<[^>]+>/g, " ")
                .replace(/\s+/g, " ")
                .trim();
              break;
            }
          }
          
          // If no description found, use the full body text
          if (!jobContent || jobContent.length < 100) {
            const bodyMatch = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
            if (bodyMatch) {
              jobContent = bodyMatch[1]
                .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, "")
                .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, "")
                .replace(/<[^>]+>/g, " ")
                .replace(/\s+/g, " ")
                .trim();
            }
          }
        }
      } catch (fetchError) {
        console.error("Error fetching job URL:", fetchError);
      }
    }
    
    // Extract keywords from job
    const jobKeywords = extractKeywords(jobContent);
    
    // Parse master CV
    const { keywords: cvKeywords, skills, experience } = parseMasterCV();
    
    // Calculate ATS score
    const { score, matched, missing } = calculateATSScore(jobKeywords, cvKeywords);
    
    // Determine job level from title
    let jobLevel = "Mid";
    const titleLower = jobTitle.toLowerCase();
    if (titleLower.includes("vp") || titleLower.includes("vice president") || titleLower.includes("director") || titleLower.includes("head of")) {
      jobLevel = "Executive";
    } else if (titleLower.includes("senior") || titleLower.includes("sr\\.")) {
      jobLevel = "Senior";
    } else if (titleLower.includes("junior") || titleLower.includes("jr\\.")) {
      jobLevel = "Junior";
    }
    
    return NextResponse.json({
      success: true,
      job: {
        title: jobTitle,
        company: companyName,
        url: url,
        level: jobLevel,
      },
      analysis: {
        atsScore: score,
        matchedKeywords: matched.slice(0, 15),
        missingKeywords: missing.slice(0, 15),
        totalJobKeywords: jobKeywords.length,
        totalCVKeywords: cvKeywords.length,
      },
      suggestions: {
        keyMatches: matched.slice(0, 5),
        criticalMissing: missing.slice(0, 3),
        softSkills: ["leadership", "communication", "stakeholder management"].filter(s => !matched.some(m => m.includes(s))),
      },
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("CV generation error:", error);
    return NextResponse.json({ error: "Failed to analyze job" }, { status: 500 });
  }
}
