import { NextResponse } from "next/server";
import { execSync } from "child_process";

export const dynamic = "force-dynamic";

interface OpenClawJob {
  id: string;
  name?: string;
  enabled?: boolean;
  schedule?: {
    kind: string;
    expr?: string;
    tz?: string;
    everyMs?: number;
    at?: string;
  };
  lastRun?: {
    finishedAt?: string;
    status?: string;
  };
  nextRunAt?: string;
}

function formatSchedule(schedule?: OpenClawJob["schedule"]): string {
  if (!schedule) return "unknown";
  switch (schedule.kind) {
    case "cron":
      return `${schedule.expr}${schedule.tz ? ` (${schedule.tz})` : ""}`;
    case "every": {
      if (!schedule.everyMs) return "interval";
      const mins = Math.round(schedule.everyMs / 60000);
      if (mins < 60) return `Every ${mins} min`;
      const hours = Math.round(mins / 60);
      if (hours < 24) return `Every ${hours}h`;
      return `Every ${Math.round(hours / 24)}d`;
    }
    case "at":
      return `Once at ${schedule.at || "unknown"}`;
    default:
      return schedule.kind;
  }
}

export async function GET() {
  try {
    // Try to read cron jobs from OpenClaw CLI
    let jobs: any[] = [];

    try {
      const output = execSync("openclaw cron list --json 2>/dev/null", {
        timeout: 5000,
        encoding: "utf-8",
      });
      const parsed = JSON.parse(output);
      jobs = Array.isArray(parsed) ? parsed : parsed.jobs || [];
    } catch {
      // Fallback: try the OpenClaw cron API file directly
      try {
        const output = execSync(
          'curl -s http://localhost:3778/api/cron/jobs 2>/dev/null || echo "[]"',
          { timeout: 5000, encoding: "utf-8" }
        );
        const parsed = JSON.parse(output);
        jobs = Array.isArray(parsed) ? parsed : parsed.jobs || [];
      } catch {
        // Return empty if both fail
        return NextResponse.json([]);
      }
    }

    const cronJobs = jobs.map((job: OpenClawJob) => ({
      id: job.id,
      name: job.name || job.id || "Unnamed",
      schedule: formatSchedule(job.schedule),
      nextRun: job.nextRunAt || undefined,
      lastRun: job.lastRun?.finishedAt || undefined,
      lastStatus: job.lastRun?.status || undefined,
      enabled: job.enabled !== false,
    }));

    return NextResponse.json(cronJobs);
  } catch (error) {
    console.error("Failed to fetch cron jobs:", error);
    return NextResponse.json([]);
  }
}
