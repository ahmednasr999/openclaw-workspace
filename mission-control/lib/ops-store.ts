import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { ContentItem, ContentStage, CronJob, HandoffValidationResult, OpsSnapshot } from "@/lib/types";

const execFileAsync = promisify(execFile);

const dataDir = path.join(process.cwd(), "data");
const filePath = path.join(dataDir, "ops-snapshot.json");

const defaultOps: OpsSnapshot = {
  handoffQueue: [],
  radarLeads: [
    {
      id: "jr-1",
      role: "VP Digital Transformation",
      company: "HealthFirst GCC",
      ageHours: 3,
      salaryFit: 92,
      strategicFit: 90,
      sourceQuality: 88,
      totalScore: 90,
      threshold: 80,
      decision: "qualified",
    },
    {
      id: "jr-2",
      role: "Chief Operating Officer",
      company: "MedChain",
      ageHours: 19,
      salaryFit: 73,
      strategicFit: 82,
      sourceQuality: 80,
      totalScore: 79,
      threshold: 80,
      decision: "watch",
    },
    {
      id: "jr-3",
      role: "Regional PMO Director",
      company: "CareScale",
      ageHours: 51,
      salaryFit: 45,
      strategicFit: 76,
      sourceQuality: 70,
      totalScore: 62,
      threshold: 80,
      decision: "dropped",
      droppedReason: "Salary floor miss and stale posting",
    },
  ],
  contentItems: [
    {
      id: "cf-1",
      title: "AI PMO operating model",
      stage: "draft",
      owner: "Content Creator",
      createdAt: "2026-03-03T08:00:00.000Z",
      stageUpdatedAt: "2026-03-03T08:00:00.000Z",
      slaMinutes: 180,
    },
    {
      id: "cf-2",
      title: "Leadership hiring lesson",
      stage: "review",
      owner: "NASR",
      createdAt: "2026-03-03T06:30:00.000Z",
      stageUpdatedAt: "2026-03-03T07:00:00.000Z",
      slaMinutes: 240,
    },
    {
      id: "cf-3",
      title: "Automation reliability win",
      stage: "approved",
      owner: "NASR",
      createdAt: "2026-03-02T21:30:00.000Z",
      stageUpdatedAt: "2026-03-03T05:00:00.000Z",
      slaMinutes: 360,
    },
    {
      id: "cf-4",
      title: "Quarter roadmap recap",
      stage: "posted",
      owner: "Content Creator",
      createdAt: "2026-03-02T05:00:00.000Z",
      stageUpdatedAt: "2026-03-02T12:00:00.000Z",
      slaMinutes: 180,
    },
  ],
  cronJobs: [
    {
      id: "cj-1",
      name: "Morning Briefing",
      schedule: "0 6 * * *",
      status: "healthy",
      consecutiveFailures: 0,
      lastRunAt: "2026-03-03T06:00:00.000Z",
      lastSuccessAt: "2026-03-03T06:00:01.000Z",
      nextRunAt: "2026-03-04T06:00:00.000Z",
    },
    {
      id: "cj-2",
      name: "Pipeline Sweep",
      schedule: "0 */4 * * *",
      status: "healthy",
      consecutiveFailures: 0,
      lastRunAt: "2026-03-03T16:00:00.000Z",
      lastSuccessAt: "2026-03-03T16:00:01.000Z",
      nextRunAt: "2026-03-03T20:00:00.000Z",
    },
  ],
  heartbeat: {
    status: "healthy",
    updatedAt: new Date().toISOString(),
    tick: 0,
  },
};

async function ensureFile() {
  await mkdir(dataDir, { recursive: true });
  try {
    await readFile(filePath, "utf8");
  } catch {
    await writeFile(filePath, JSON.stringify(defaultOps, null, 2), "utf8");
  }
}

export async function loadOpsSnapshot(): Promise<OpsSnapshot> {
  await ensureFile();
  const raw = await readFile(filePath, "utf8");
  return { ...defaultOps, ...(JSON.parse(raw) as Partial<OpsSnapshot>) };
}

async function saveOpsSnapshot(snapshot: OpsSnapshot) {
  await writeFile(filePath, JSON.stringify(snapshot, null, 2), "utf8");
}

export function validateHandoffUrl(input: string): HandoffValidationResult {
  const value = input.trim();
  if (!value) {
    return { valid: false, reason: "Enter a URL to validate.", confidence: 0, matchedRule: "empty" };
  }

  let url: URL;
  try {
    url = new URL(value);
  } catch {
    return { valid: false, reason: "Invalid URL format.", confidence: 0, matchedRule: "format" };
  }

  if (!["http:", "https:"].includes(url.protocol)) {
    return { valid: false, reason: "Only http and https URLs are allowed.", confidence: 10, matchedRule: "protocol" };
  }

  const host = url.hostname.toLowerCase();
  const pathName = url.pathname.toLowerCase();
  const blockedHosts = ["linkedin.com/feed", "linkedin.com/in/"];
  if (blockedHosts.some((pattern) => `${host}${pathName}`.includes(pattern))) {
    return { valid: false, reason: "Profile and feed links are blocked.", confidence: 15, matchedRule: "blocked_path" };
  }

  const linkedInDirect = host.includes("linkedin.com") && (pathName.startsWith("/jobs/view/") || pathName === "/jobs/view" || url.searchParams.has("currentjobid"));
  if (linkedInDirect) {
    return { valid: true, reason: "Valid LinkedIn direct job URL.", confidence: 92, matchedRule: "linkedin_direct" };
  }

  const employerPath = /(career|careers|job|jobs|vacanc|position|opportunit)/.test(pathName);
  if (!host.includes("linkedin.com") && employerPath) {
    return { valid: true, reason: "Valid direct employer job posting URL.", confidence: 84, matchedRule: "employer_posting" };
  }

  return { valid: false, reason: "URL must be a LinkedIn /jobs/view link or direct employer posting.", confidence: 25, matchedRule: "rule_miss" };
}

export async function enqueueHandoff(url: string, roleHint = "", companyHint = "") {
  const snapshot = await loadOpsSnapshot();
  const validation = validateHandoffUrl(url);
  if (!validation.valid) {
    return null;
  }

  const score = Math.min(100, Math.max(0, Math.round((validation.confidence * 0.6) + 40)));
  const item = {
    id: `hq-${Date.now()}`,
    url,
    roleHint,
    companyHint,
    score,
    validation,
    createdAt: new Date().toISOString(),
  };

  snapshot.handoffQueue = [item, ...snapshot.handoffQueue].slice(0, 50);
  await saveOpsSnapshot(snapshot);
  return item;
}

export async function loadRadarLeads() {
  const snapshot = await loadOpsSnapshot();
  return [...snapshot.radarLeads].sort((a, b) => a.ageHours - b.ageHours);
}

const nextStages: Record<ContentStage, ContentStage | null> = {
  draft: "review",
  review: "approved",
  approved: "posted",
  posted: null,
};

export async function advanceContentStage(itemId: string): Promise<ContentItem | null> {
  const snapshot = await loadOpsSnapshot();
  const idx = snapshot.contentItems.findIndex((item) => item.id === itemId);
  if (idx < 0) {
    return null;
  }

  const item = snapshot.contentItems[idx];
  const target = nextStages[item.stage];
  if (!target) {
    return item;
  }

  const updated: ContentItem = {
    ...item,
    stage: target,
    stageUpdatedAt: new Date().toISOString(),
  };

  snapshot.contentItems[idx] = updated;
  await saveOpsSnapshot(snapshot);
  return updated;
}

export async function loadContentItems() {
  const snapshot = await loadOpsSnapshot();
  return snapshot.contentItems;
}

type OpenClawCronJob = {
  id?: string;
  name?: string;
  enabled?: boolean;
  schedule?: { expr?: string };
  state?: {
    nextRunAtMs?: number;
    lastRunAtMs?: number;
    lastStatus?: string;
    lastRunStatus?: string;
    consecutiveErrors?: number;
  };
};

async function readGatewayToken() {
  if (process.env.OPENCLAW_GATEWAY_TOKEN) {
    return process.env.OPENCLAW_GATEWAY_TOKEN;
  }

  try {
    const configPath = process.env.OPENCLAW_CONFIG_PATH || "/root/.openclaw/openclaw.json";
    const raw = await readFile(configPath, "utf8");
    const parsed = JSON.parse(raw) as { gateway?: { auth?: { token?: string } } };
    return parsed?.gateway?.auth?.token || "";
  } catch {
    return "";
  }
}

async function isDeliveryOnlyFailure(jobId: string, token: string) {
  try {
    const { stdout } = await execFileAsync(
      "openclaw",
      ["cron", "runs", "--id", jobId, "--limit", "1", "--token", token],
      { timeout: 15000, maxBuffer: 512 * 1024 }
    );

    const parsed = JSON.parse(stdout) as { entries?: Array<{ status?: string; error?: string; summary?: string }> };
    const latest = parsed.entries?.[0];
    if (!latest) {
      return false;
    }

    return latest.status === "error" && (latest.error || "").toLowerCase().includes("cron announce delivery failed");
  } catch {
    return false;
  }
}

async function fetchOpenClawCronJobs(): Promise<CronJob[] | null> {
  try {
    const token = await readGatewayToken();
    if (!token) {
      return null;
    }

    const { stdout } = await execFileAsync(
      "openclaw",
      ["cron", "list", "--all", "--json", "--token", token],
      { timeout: 8000, maxBuffer: 1024 * 1024 }
    );

    const parsed = JSON.parse(stdout) as { jobs?: OpenClawCronJob[] };
    const jobs = parsed.jobs || [];

    const mapped: CronJob[] = [];
    for (const job of jobs) {
      const state = job.state || {};
      const id = job.id || `cron-${Math.random().toString(36).slice(2, 8)}`;
      const consecutiveFailures = Number(state.consecutiveErrors || 0);
      const paused = job.enabled === false;
      let failing = !paused && (consecutiveFailures > 0 || (state.lastStatus && state.lastStatus !== "ok"));

      if (failing && consecutiveFailures > 0 && job.id) {
        const deliveryOnly = await isDeliveryOnlyFailure(job.id, token);
        if (deliveryOnly) {
          failing = false;
        }
      }

      const lastRunAt = state.lastRunAtMs ? new Date(state.lastRunAtMs).toISOString() : "";
      const lastSuccessAt = (state.lastRunStatus === "ok" && state.lastRunAtMs)
        ? new Date(state.lastRunAtMs).toISOString()
        : "";
      const nextRunAt = state.nextRunAtMs ? new Date(state.nextRunAtMs).toISOString() : "";

      mapped.push({
        id,
        name: job.name || "Unnamed cron",
        schedule: job.schedule?.expr || "unknown",
        status: paused ? "paused" : failing ? "failing" : "healthy",
        consecutiveFailures,
        lastRunAt,
        lastSuccessAt,
        nextRunAt,
      });
    }

    return mapped;
  } catch {
    return null;
  }
}

export async function monitorCronHealth() {
  const snapshot = await loadOpsSnapshot();
  const now = new Date();

  const liveJobs = await fetchOpenClawCronJobs();
  if (liveJobs && liveJobs.length > 0) {
    snapshot.cronJobs = liveJobs;
    snapshot.heartbeat = {
      status: liveJobs.some((job) => job.status === "failing") ? "degraded" : "healthy",
      updatedAt: now.toISOString(),
      tick: snapshot.heartbeat.tick + 1,
    };

    await saveOpsSnapshot(snapshot);
    return snapshot;
  }

  const jobs = snapshot.cronJobs.map((job): CronJob => {
    if (job.consecutiveFailures >= 2) {
      return {
        ...job,
        status: "failing",
        nextRunAt: new Date(now.getTime() + 15 * 60 * 1000).toISOString(),
      };
    }

    return { ...job, status: "healthy" };
  });

  snapshot.cronJobs = jobs;
  snapshot.heartbeat = {
    status: jobs.some((job) => job.status === "failing") ? "degraded" : "healthy",
    updatedAt: now.toISOString(),
    tick: snapshot.heartbeat.tick + 1,
  };

  await saveOpsSnapshot(snapshot);
  return snapshot;
}
