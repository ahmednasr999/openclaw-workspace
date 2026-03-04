import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { readdir, stat } from "node:fs/promises";

import { getOrParse, getCacheStats } from "./cache";
import {
  parseActiveTasks,
  parseMemory,
  parseGoals,
  parsePipeline,
  parseContentCalendar,
  parseCvHistory,
  ParsedTask,
  ParsedMemory,
  ParsedGoals,
  PipelineEntry,
  CvHistoryEntry,
  getDefaultTeamEntries,
  systemMetricsToOfficeEntries,
  docsIndexToDocsEntries,
} from "./parsers";
import type { ContentItem, DocsEntry, OfficeMetric, TeamEntry } from "@/lib/types";

const execFileAsync = promisify(execFile);

// Workspace root
const WS = "/root/.openclaw/workspace";

// ---------------------------------------------------------------------------
// getTasks
// ---------------------------------------------------------------------------
export async function getTasks(): Promise<ParsedTask[]> {
  const fp = path.join(WS, "memory/active-tasks.md");
  const result = await getOrParse(fp, parseActiveTasks);
  return result || [];
}

// ---------------------------------------------------------------------------
// getMemory
// ---------------------------------------------------------------------------
export async function getMemory(): Promise<ParsedMemory> {
  const fp = path.join(WS, "MEMORY.md");
  const result = await getOrParse(fp, parseMemory);
  return result || { priorities: [], lessons: [], milestones: [], decisions: [] };
}

// ---------------------------------------------------------------------------
// getGoals
// ---------------------------------------------------------------------------
export async function getGoals(): Promise<ParsedGoals> {
  const fp = path.join(WS, "GOALS.md");
  const result = await getOrParse(fp, parseGoals);
  return result || { objectives: [], primaryMission: "", activeApplications: 0 };
}

// ---------------------------------------------------------------------------
// getPipeline
// ---------------------------------------------------------------------------
export async function getPipeline(): Promise<PipelineEntry[]> {
  const fp = path.join(WS, "jobs-bank/pipeline.md");
  const result = await getOrParse(fp, parsePipeline);
  return result || [];
}

// ---------------------------------------------------------------------------
// getContentItems
// ---------------------------------------------------------------------------
export async function getContentItems(): Promise<ContentItem[]> {
  const fp = path.join(WS, "memory/linkedin_content_calendar.md");
  const result = await getOrParse(fp, parseContentCalendar);
  return result || [];
}

// ---------------------------------------------------------------------------
// getCvHistory
// ---------------------------------------------------------------------------
export async function getCvHistory(): Promise<CvHistoryEntry[]> {
  const fp = path.join(WS, "memory/cv-history.md");
  const result = await getOrParse(fp, parseCvHistory);
  return result || [];
}

// ---------------------------------------------------------------------------
// getSystemHealth
// ---------------------------------------------------------------------------
export interface SystemHealth {
  ram: { used: number; total: number };
  disk: { used: number; total: number };
  gateway: { status: string; uptime: string };
  ollama: { status: string };
  score: number;
}

export async function getSystemHealth(): Promise<SystemHealth> {
  const health: SystemHealth = {
    ram: { used: 0, total: 0 },
    disk: { used: 0, total: 0 },
    gateway: { status: "unknown", uptime: "" },
    ollama: { status: "unknown" },
    score: 0,
  };

  // RAM via /proc/meminfo
  try {
    const { readFile } = await import("node:fs/promises");
    const memInfo = await readFile("/proc/meminfo", "utf8");
    const totalMatch = memInfo.match(/MemTotal:\s+(\d+)/);
    const availMatch = memInfo.match(/MemAvailable:\s+(\d+)/);
    if (totalMatch && availMatch) {
      const totalKb = parseInt(totalMatch[1], 10);
      const availKb = parseInt(availMatch[1], 10);
      health.ram.total = Math.round(totalKb / 1024);
      health.ram.used = Math.round((totalKb - availKb) / 1024);
    }
  } catch {
    // ignore
  }

  // Disk via df
  try {
    const { stdout } = await execFileAsync("df", ["-BM", "--output=used,size", "/"], { timeout: 5000 });
    const lines = stdout.trim().split("\n");
    if (lines.length >= 2) {
      const parts = lines[1].trim().split(/\s+/);
      health.disk.used = parseInt(parts[0], 10);
      health.disk.total = parseInt(parts[1], 10);
    }
  } catch {
    // ignore
  }

  // Gateway health
  try {
    const { stdout } = await execFileAsync(
      "curl",
      ["-sf", "--max-time", "3", "http://localhost:18789/health"],
      { timeout: 5000 }
    );
    const parsed = JSON.parse(stdout) as { status?: string; uptime?: string };
    health.gateway.status = parsed.status || "healthy";
    health.gateway.uptime = parsed.uptime || "";
  } catch {
    health.gateway.status = "unreachable";
  }

  // Ollama
  try {
    await execFileAsync("curl", ["-sf", "--max-time", "3", "http://localhost:11434/api/tags"], { timeout: 5000 });
    health.ollama.status = "running";
  } catch {
    health.ollama.status = "offline";
  }

  // Compute score: 0-100
  let score = 100;
  if (health.ram.total > 0) {
    const ramPct = (health.ram.used / health.ram.total) * 100;
    if (ramPct > 90) score -= 20;
    else if (ramPct > 80) score -= 10;
  }
  if (health.disk.total > 0) {
    const diskPct = (health.disk.used / health.disk.total) * 100;
    if (diskPct > 90) score -= 20;
    else if (diskPct > 80) score -= 10;
  }
  if (health.gateway.status !== "healthy" && health.gateway.status !== "ok") score -= 15;
  if (health.ollama.status === "offline") score -= 5;

  health.score = Math.max(0, score);

  return health;
}

// ---------------------------------------------------------------------------
// getOfficeMetrics (wraps system health into OfficeMetric[])
// ---------------------------------------------------------------------------
export async function getOfficeMetrics(): Promise<OfficeMetric[]> {
  const h = await getSystemHealth();
  return systemMetricsToOfficeEntries({
    ram: h.ram,
    disk: h.disk,
    gateway: h.gateway,
    ollama: h.ollama,
  });
}

// ---------------------------------------------------------------------------
// getAgentActivity
// ---------------------------------------------------------------------------
export async function getAgentActivity(): Promise<TeamEntry[]> {
  // Primary source: list agent folders in workspace agents directory
  const agentDirs = [
    "/root/.openclaw/agents",
    "/root/.openclaw/workspace/agents",
  ];

  const found: TeamEntry[] = [];

  for (const dir of agentDirs) {
    try {
      const entries = await readdir(dir);
      for (const name of entries) {
        const s = await stat(path.join(dir, name)).catch(() => null);
        if (s?.isDirectory()) {
          found.push({
            id: `agent-${name}`,
            name,
            focus: "Agent",
            status: "active",
          });
        }
      }
    } catch {
      // directory doesn't exist
    }
  }

  return found.length > 0 ? found : getDefaultTeamEntries();
}

// ---------------------------------------------------------------------------
// getDocsIndex
// ---------------------------------------------------------------------------
export async function getDocsIndex(): Promise<DocsEntry[]> {
  const dirs = [
    { dir: WS, category: "Workspace", depth: 0 },
    { dir: path.join(WS, "memory"), category: "Memory", depth: 0 },
    { dir: path.join(WS, "skills"), category: "Skills", depth: 1 },
  ];

  const raw: Array<{ path: string; title: string; category: string; updatedAt: string; sizeBytes: number }> = [];

  for (const { dir, category, depth } of dirs) {
    try {
      const entries = await readdir(dir);
      for (const name of entries) {
        if (!name.endsWith(".md")) continue;
        const fullPath = path.join(dir, name);
        try {
          const s = await stat(fullPath);
          raw.push({
            path: fullPath,
            title: name.replace(".md", "").replace(/-/g, " "),
            category,
            updatedAt: s.mtime.toISOString(),
            sizeBytes: s.size,
          });
        } catch {
          // skip
        }
      }

      // One level deep for skills
      if (depth > 0) {
        const subdirs = await readdir(dir).catch(() => [] as string[]);
        for (const sub of subdirs) {
          const subPath = path.join(dir, sub);
          const ss = await stat(subPath).catch(() => null);
          if (ss?.isDirectory()) {
            const subEntries = await readdir(subPath).catch(() => [] as string[]);
            for (const name of subEntries) {
              if (!name.endsWith(".md")) continue;
              const fullPath = path.join(subPath, name);
              try {
                const s = await stat(fullPath);
                raw.push({
                  path: fullPath,
                  title: `${sub}/${name.replace(".md", "")}`,
                  category: "Skills",
                  updatedAt: s.mtime.toISOString(),
                  sizeBytes: s.size,
                });
              } catch {
                // skip
              }
            }
          }
        }
      }
    } catch {
      // directory doesn't exist
    }
  }

  // Sort by updatedAt desc
  raw.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));

  return docsIndexToDocsEntries(raw.slice(0, 50));
}

// ---------------------------------------------------------------------------
// getSyncStatus
// ---------------------------------------------------------------------------
export interface SyncStatus {
  lastSync: string;
  fileCount: number;
  cacheEntries: number;
  cacheKeys: string[];
}

export function getSyncStatus(): SyncStatus {
  const stats = getCacheStats();
  return {
    lastSync: new Date().toISOString(),
    fileCount: stats.entries,
    cacheEntries: stats.entries,
    cacheKeys: stats.keys,
  };
}
