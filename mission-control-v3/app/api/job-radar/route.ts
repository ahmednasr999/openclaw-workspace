import { NextResponse } from "next/server";
import { loadRadarLeads } from "@/lib/ops-store";

export const runtime = "nodejs";

export async function GET() {
  const leads = await loadRadarLeads();
  return NextResponse.json({ leads, thresholdPolicy: "qualified >= 80", fetchedAt: new Date().toISOString() });
}
