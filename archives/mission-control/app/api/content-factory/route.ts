import { NextRequest, NextResponse } from "next/server";
import { getContentItems } from "@/lib/sync";
import { advanceContentStage } from "@/lib/ops-store";

export const runtime = "nodejs";

export async function GET() {
  // Prefer live data from content calendar
  const items = await getContentItems();

  // Fall back to ops-store if calendar is empty
  if (items.length === 0) {
    const { loadContentItems } = await import("@/lib/ops-store");
    const fallback = await loadContentItems();
    return NextResponse.json({ items: fallback, source: "ops-store", fetchedAt: new Date().toISOString() });
  }

  return NextResponse.json({ items, source: "calendar", fetchedAt: new Date().toISOString() });
}

export async function PATCH(request: NextRequest) {
  const payload = await request.json().catch(() => null) as Record<string, string> | null;
  const itemId = String(payload?.itemId || "").trim();
  if (!itemId) {
    return NextResponse.json({ error: "Invalid item id" }, { status: 400 });
  }

  // advanceContentStage still writes to ops-store (for manual stage advancement)
  const item = await advanceContentStage(itemId);
  if (!item) {
    return NextResponse.json({ error: "Content item not found" }, { status: 404 });
  }

  return NextResponse.json({ item });
}
