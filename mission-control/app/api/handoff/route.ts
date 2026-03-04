import { NextRequest, NextResponse } from "next/server";
import { enqueueHandoff, loadOpsSnapshot, validateHandoffUrl } from "@/lib/ops-store";

export const runtime = "nodejs";

export async function GET() {
  const snapshot = await loadOpsSnapshot();
  return NextResponse.json({ queue: snapshot.handoffQueue, fetchedAt: new Date().toISOString() });
}

export async function POST(request: NextRequest) {
  const payload = await request.json().catch(() => null) as Record<string, string> | null;
  const url = String(payload?.url || "").trim();
  const roleHint = String(payload?.roleHint || "").trim();
  const companyHint = String(payload?.companyHint || "").trim();

  const validation = validateHandoffUrl(url);
  if (!validation.valid) {
    return NextResponse.json({ validation }, { status: 400 });
  }

  const item = await enqueueHandoff(url, roleHint, companyHint);
  return NextResponse.json({ item, validation }, { status: 201 });
}
