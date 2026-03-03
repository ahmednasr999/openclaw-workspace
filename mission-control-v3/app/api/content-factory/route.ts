import { NextRequest, NextResponse } from "next/server";
import { advanceContentStage, loadContentItems } from "@/lib/ops-store";

export const runtime = "nodejs";

export async function GET() {
  const items = await loadContentItems();
  return NextResponse.json({ items, fetchedAt: new Date().toISOString() });
}

export async function PATCH(request: NextRequest) {
  const payload = await request.json().catch(() => null) as Record<string, string> | null;
  const itemId = String(payload?.itemId || "").trim();
  if (!itemId) {
    return NextResponse.json({ error: "Invalid item id" }, { status: 400 });
  }

  const item = await advanceContentStage(itemId);
  if (!item) {
    return NextResponse.json({ error: "Content item not found" }, { status: 404 });
  }

  return NextResponse.json({ item });
}
