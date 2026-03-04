import { NextResponse } from "next/server";
import { getPipeline } from "@/lib/sync";
import type { PipelineEntry } from "@/lib/sync/parsers";

export const runtime = "nodejs";

function stageToDecision(stage: string): "qualified" | "watch" | "dropped" {
  const s = stage.toLowerCase();
  if (s.includes("interview") || s.includes("offer")) return "qualified";
  if (s.includes("applied") || s.includes("awaiting") || s.includes("cv ready")) return "watch";
  if (s.includes("closed") || s.includes("rejected")) return "dropped";
  return "watch";
}

function pipelineEntryToLead(entry: PipelineEntry, idx: number) {
  // Derive a score from ATS if available
  const atsRaw = entry.atsScore.replace(/[%\s]/g, "").split("-")[0];
  const ats = parseInt(atsRaw, 10) || 80;

  // Age: use applied date
  let ageHours = 72;
  if (entry.appliedDate) {
    const applied = new Date(entry.appliedDate);
    if (!isNaN(applied.getTime())) {
      ageHours = Math.round((Date.now() - applied.getTime()) / 3600000);
    }
  }

  const decision = stageToDecision(entry.stage);

  return {
    id: entry.id || `jrl-${idx}`,
    role: entry.role,
    company: entry.company,
    location: entry.location,
    stage: entry.stage,
    ageHours,
    salaryFit: ats,
    strategicFit: ats,
    sourceQuality: 80,
    totalScore: ats,
    threshold: 80,
    decision,
    droppedReason: decision === "dropped" ? "No response or closed" : undefined,
    appliedDate: entry.appliedDate,
    followUpDate: entry.followUpDate,
  };
}

export async function GET() {
  const pipeline = await getPipeline();

  const leads = pipeline
    .filter((e) => e.company && e.role)
    .map((entry, idx) => pipelineEntryToLead(entry, idx))
    .sort((a, b) => {
      // Sort: Interview first, then by ageHours ascending
      const stageOrder: Record<string, number> = { "Interview": 0, "Offer": 0, "Awaiting Feedback": 1, "Applied": 2, "CV Ready": 3, "Identified": 4, "Closed": 5 };
      const ao = stageOrder[a.stage] ?? 3;
      const bo = stageOrder[b.stage] ?? 3;
      if (ao !== bo) return ao - bo;
      return a.ageHours - b.ageHours;
    });

  return NextResponse.json({
    leads,
    total: leads.length,
    thresholdPolicy: "qualified >= 80",
    fetchedAt: new Date().toISOString(),
  });
}
