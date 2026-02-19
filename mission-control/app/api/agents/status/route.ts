import { NextResponse } from "next/server";
import { execSync } from "child_process";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    let runs: any[] = [];

    // Try to get active sessions/sub-agents from OpenClaw
    try {
      const output = execSync(
        'curl -s http://localhost:3778/api/sessions?activeMinutes=60 2>/dev/null || echo "[]"',
        { timeout: 5000, encoding: "utf-8" }
      );
      const parsed = JSON.parse(output);
      runs = Array.isArray(parsed) ? parsed : parsed.sessions || [];
    } catch {
      // Fallback: empty
    }

    return NextResponse.json({
      runs: runs.map((r: any) => ({
        sessionKey: r.sessionKey || r.key || "",
        label: r.label || "",
        status: r.status || "unknown",
        updatedAt: r.updatedAt || new Date().toISOString(),
        task: r.task || r.label || "",
      })),
    });
  } catch (error) {
    return NextResponse.json({ runs: [] });
  }
}
