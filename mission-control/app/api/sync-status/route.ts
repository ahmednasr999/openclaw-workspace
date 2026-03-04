import { NextResponse } from "next/server";
import { getSyncStatus } from "@/lib/sync";

export const runtime = "nodejs";

export async function GET() {
  const status = getSyncStatus();
  return NextResponse.json({ ...status, fetchedAt: new Date().toISOString() });
}
