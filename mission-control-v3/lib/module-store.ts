import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { seedTasks } from "@/lib/parity";
import { loadTasks } from "@/lib/task-store";
import { ModuleSnapshot } from "@/lib/types";

const dataDir = path.join(process.cwd(), "data");
const filePath = path.join(dataDir, "module-snapshot.json");

const fallbackSnapshot: ModuleSnapshot = {
  docs: [
    { id: "d1", title: "Executive strategy playbook", category: "Strategy", updatedAt: "2026-03-02T09:00:00.000Z" },
    { id: "d2", title: "Automation incident runbook", category: "Operations", updatedAt: "2026-03-02T08:30:00.000Z" },
    { id: "d3", title: "Interview prep matrix", category: "Career", updatedAt: "2026-03-01T18:00:00.000Z" },
  ],
  memory: [
    { id: "m1", type: "decision", text: "Adopted Mission Control v3 dark baseline and route structure.", updatedAt: "2026-03-02T12:00:00.000Z" },
    { id: "m2", type: "decision", text: "Pinned single-token auth for single user access.", updatedAt: "2026-03-02T12:10:00.000Z" },
    { id: "m3", type: "thread", text: "Complete API integration status checks.", updatedAt: "2026-03-03T08:00:00.000Z" },
  ],
  team: [
    { id: "t1", name: "NASR", focus: "Strategic orchestration", status: "active" },
    { id: "t2", name: "Job Hunter", focus: "Role scan and scoring", status: "busy" },
    { id: "t3", name: "Content Creator", focus: "LinkedIn drafts", status: "active" },
  ],
  office: [
    { id: "o1", label: "Agent presence", value: "Stable", trend: "flat" },
    { id: "o2", label: "Blocker escalations", value: "0", trend: "down" },
    { id: "o3", label: "Queue velocity", value: "Normal", trend: "up" },
  ],
  projects: [
    { id: "p1", name: "Digital Transformation Program", progress: 68, linkedTasks: ["Finalize operating model v3"] },
    { id: "p2", name: "AI Automation Ecosystem", progress: 54, linkedTasks: ["Cross-link radar to pipeline"] },
  ],
  tasks: seedTasks,
};

async function ensureSnapshotFile() {
  await mkdir(dataDir, { recursive: true });

  try {
    await readFile(filePath, "utf8");
  } catch {
    await writeFile(filePath, JSON.stringify(fallbackSnapshot, null, 2), "utf8");
  }
}

export async function loadModuleSnapshot(): Promise<ModuleSnapshot> {
  await ensureSnapshotFile();
  const raw = await readFile(filePath, "utf8");
  const snapshot = JSON.parse(raw) as Partial<ModuleSnapshot>;
  const tasks = await loadTasks();

  return {
    ...fallbackSnapshot,
    ...snapshot,
    tasks,
  } as ModuleSnapshot;
}
