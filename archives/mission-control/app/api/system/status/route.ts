import { NextResponse } from "next/server";
import { loadModuleSnapshot } from "@/lib/module-store";
import { BackendHealth } from "@/lib/types";

export const runtime = "nodejs";

export async function GET() {
  const startedAt = Date.now();

  try {
    const snapshot = await loadModuleSnapshot();
    const baseLatency = Date.now() - startedAt;
    const moduleCount =
      snapshot.docs.length +
      snapshot.memory.length +
      snapshot.team.length +
      snapshot.office.length +
      snapshot.projects.length;

    const latencyMs = Math.max(25, baseLatency + Math.floor(moduleCount / 2));
    const level = latencyMs >= 450 ? "critical" : latencyMs >= 220 ? "degraded" : "healthy";

    const response: BackendHealth = {
      reachable: true,
      latencyMs,
      level,
      reason: level === "critical" ? "Latency breach detected" : level === "degraded" ? "Latency elevated" : "Backend stable",
      checkedAt: new Date().toISOString(),
    };

    return NextResponse.json(response, { status: 200 });
  } catch {
    const response: BackendHealth = {
      reachable: false,
      latencyMs: 999,
      level: "critical",
      reason: "Backend unreachable",
      checkedAt: new Date().toISOString(),
    };

    return NextResponse.json(response, { status: 503 });
  }
}
