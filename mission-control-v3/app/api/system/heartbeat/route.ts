import { NextResponse } from "next/server";
import { monitorCronHealth } from "@/lib/ops-store";

export const runtime = "nodejs";

export async function GET() {
  const snapshot = await monitorCronHealth();
  return NextResponse.json(snapshot.heartbeat);
}
