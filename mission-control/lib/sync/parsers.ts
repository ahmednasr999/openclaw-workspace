import { ContentItem, ContentStage, DocsEntry, MemoryEntry, OfficeMetric, ProjectEntry, TeamEntry } from "@/lib/types";
import { TaskItem, TaskStatus } from "@/lib/parity";

// ---------------------------------------------------------------------------
// 1. active-tasks.md parser
// ---------------------------------------------------------------------------

export interface ParsedTask extends TaskItem {
  section: string;
  nextAction?: string;
}

function sectionToStatus(section: string): TaskStatus {
  if (section.includes("URGENT")) return "in_progress";
  if (section.includes("In Progress")) return "in_progress";
  if (section.includes("Recurring")) return "recurring";
  if (section.includes("Recently Completed")) return "done";
  return "backlog";
}

function sectionToPriority(section: string): "low" | "medium" | "high" {
  if (section.includes("URGENT")) return "high";
  if (section.includes("In Progress")) return "medium";
  return "low";
}

export function parseActiveTasks(content: string): ParsedTask[] {
  const tasks: ParsedTask[] = [];
  let currentSection = "";
  let counter = 0;

  const lines = content.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Detect section headers
    if (line.startsWith("## ")) {
      currentSection = line.replace(/^## /, "").trim();
      continue;
    }

    // Detect subsection (task block): ### Task Title
    if (line.startsWith("### ")) {
      const title = line.replace(/^### /, "").trim();
      if (!title || !currentSection) continue;

      // Find next action
      let nextAction = "";
      for (let j = i + 1; j < Math.min(i + 8, lines.length); j++) {
        const sub = lines[j].trim();
        if (sub.startsWith("- **Next:**")) {
          nextAction = sub.replace(/^- \*\*Next:\*\*\s*/, "").trim();
        }
        if (lines[j].startsWith("### ") || lines[j].startsWith("## ")) break;
      }

      counter++;
      tasks.push({
        id: `task-md-${counter}`,
        title,
        section: currentSection,
        status: sectionToStatus(currentSection),
        priority: sectionToPriority(currentSection),
        assignee: "NASR",
        dueDate: "",
        nextAction: nextAction || undefined,
      });
      continue;
    }

    // Detect bullet tasks: - **Title:** description  (only in URGENT / top-level sections)
    if (line.startsWith("- **") && currentSection && !line.startsWith("- **Status:**") && !line.startsWith("- **Next:**") && !line.startsWith("- **Progress:**") && !line.startsWith("- **Location:**")) {
      const match = line.match(/^- \*\*([^*]+)\*\*[:\s]*(.*)/);
      if (match) {
        const rawTitle = match[1].trim();
        const details = match[2].trim();

        // Skip meta keys that are sub-properties
        const metaKeys = ["Status", "Next", "Progress", "Location", "Completed", "Week", "Match Notes", "Matched Keywords", "Missing Keywords"];
        if (metaKeys.some((k) => rawTitle === k)) continue;

        // Extract due date from details if present
        const dateMatch = details.match(/\*\*(\d{4}-\d{2}-\d{2})\*\*/);
        const dueDate = dateMatch ? dateMatch[1] : "";

        counter++;
        tasks.push({
          id: `task-md-${counter}`,
          title: `${rawTitle}: ${details}`.replace(/\*\*/g, "").slice(0, 120),
          section: currentSection,
          status: sectionToStatus(currentSection),
          priority: sectionToPriority(currentSection),
          assignee: "NASR",
          dueDate,
        });
      }
    }
  }

  return tasks;
}

// ---------------------------------------------------------------------------
// 2. MEMORY.md parser
// ---------------------------------------------------------------------------

export interface ParsedMemory {
  priorities: string[];
  lessons: MemoryEntry[];
  milestones: MemoryEntry[];
  decisions: MemoryEntry[];
}

export function parseMemory(content: string): ParsedMemory {
  const priorities: string[] = [];
  const lessons: MemoryEntry[] = [];
  const milestones: MemoryEntry[] = [];
  const decisions: MemoryEntry[] = [];

  const lines = content.split("\n");
  let section = "";
  let counter = 0;

  for (const line of lines) {
    if (line.startsWith("## ")) {
      section = line.replace(/^## /, "").trim();
      continue;
    }

    if (section.includes("Current Strategic Priorities")) {
      const match = line.match(/^\d+\.\s+(.+)/);
      if (match) priorities.push(match[1].trim());
    }

    if (section.includes("Lessons Learned")) {
      if (line.startsWith("- ") || line.startsWith("* ")) {
        const text = line.slice(2).trim();
        if (text) {
          counter++;
          lessons.push({ id: `lesson-${counter}`, type: "thread", text, updatedAt: new Date().toISOString() });
        }
      }
    }

    if (section.includes("Completed Milestones")) {
      if (line.startsWith("- [x]") || line.startsWith("- ✅") || (line.startsWith("- ") && line.includes("✅"))) {
        const text = line.replace(/^- \[x\]\s*/, "").replace(/^- ✅\s*/, "").replace("✅", "").trim();
        if (text) {
          counter++;
          milestones.push({ id: `ms-${counter}`, type: "decision", text, updatedAt: new Date().toISOString() });
        }
      }
    }

    if (section.includes("Work") || section.includes("Communication")) {
      if (line.startsWith("- **") && line.includes(":**")) {
        const match = line.match(/^- \*\*([^*]+)\*\*[:\s]*(.*)/);
        if (match) {
          const key = match[1].trim();
          const val = match[2].trim();
          if (val) {
            counter++;
            decisions.push({
              id: `dec-${counter}`,
              type: "decision",
              text: `${key}: ${val}`,
              updatedAt: new Date().toISOString(),
            });
          }
        }
      }
    }
  }

  return { priorities, lessons, milestones, decisions };
}

// ---------------------------------------------------------------------------
// 3. GOALS.md parser
// ---------------------------------------------------------------------------

export interface ParsedObjective {
  id: string;
  title: string;
  progress: number;
  status: "active" | "completed" | "pending";
  keyResults: string[];
}

export interface ParsedGoals {
  objectives: ParsedObjective[];
  primaryMission: string;
  activeApplications: number;
}

export function parseGoals(content: string): ParsedGoals {
  const objectives: ParsedObjective[] = [];
  let primaryMission = "";
  let activeApplications = 0;
  let section = "";
  let counter = 0;
  let currentObj: ParsedObjective | null = null;

  const lines = content.split("\n");
  for (const line of lines) {
    if (line.startsWith("## ")) {
      if (currentObj) {
        objectives.push(currentObj);
        currentObj = null;
      }
      section = line.replace(/^## /, "").trim();
      continue;
    }

    if (section.includes("Primary Mission") && !primaryMission && line.trim() && !line.startsWith("#")) {
      primaryMission = line.trim();
      continue;
    }

    if (section.includes("Strategic Objectives") || section.includes("Active Job Pipeline")) {
      if (line.startsWith("### ")) {
        if (currentObj) objectives.push(currentObj);
        counter++;
        currentObj = {
          id: `obj-${counter}`,
          title: line.replace(/^### /, "").trim(),
          progress: 0,
          status: "active",
          keyResults: [],
        };
        continue;
      }

      if (currentObj && (line.startsWith("- [ ]") || line.startsWith("- [x]"))) {
        const kr = line.replace(/^- \[[x ]\]\s*/, "").replace(/✅$/, "").trim();
        if (kr) {
          currentObj.keyResults.push(kr);
        }
      }
    }

    // Count active applications from the table
    if (section.includes("Active Applications") || section.includes("Active Job Pipeline")) {
      if (line.startsWith("| ") && !line.startsWith("| Company") && !line.startsWith("| ---") && !line.startsWith("| #") && line.includes("|")) {
        activeApplications++;
      }
    }
  }

  if (currentObj) objectives.push(currentObj);

  // Recalculate progress for each objective based on key results
  for (const obj of objectives) {
    if (obj.keyResults.length === 0) {
      obj.progress = 0;
    } else {
      // We need to re-parse to count done vs total
      // For now, estimate from the raw content
      obj.progress = 0;
    }
  }

  // Second pass for accurate progress calculation
  const objMap = new Map<string, { done: number; total: number }>();
  let objTitle = "";
  let inObj = false;
  for (const line of lines) {
    if (line.startsWith("### ")) {
      objTitle = line.replace(/^### /, "").trim();
      inObj = true;
      objMap.set(objTitle, { done: 0, total: 0 });
      continue;
    }
    if (line.startsWith("## ")) {
      inObj = false;
      continue;
    }
    if (inObj && objTitle) {
      if (line.startsWith("- [x]")) {
        const e = objMap.get(objTitle) || { done: 0, total: 0 };
        e.done++;
        e.total++;
        objMap.set(objTitle, e);
      } else if (line.startsWith("- [ ]")) {
        const e = objMap.get(objTitle) || { done: 0, total: 0 };
        e.total++;
        objMap.set(objTitle, e);
      }
    }
  }

  for (const obj of objectives) {
    const counts = objMap.get(obj.title);
    if (counts && counts.total > 0) {
      obj.progress = Math.round((counts.done / counts.total) * 100);
    }
  }

  return { objectives, primaryMission, activeApplications };
}

// ---------------------------------------------------------------------------
// 4. pipeline.md parser
// ---------------------------------------------------------------------------

export interface PipelineEntry {
  id: string;
  company: string;
  role: string;
  location: string;
  stage: string;
  atsScore: string;
  appliedDate: string;
  followUpDate: string;
  notes: string;
  salary: string;
  applied: boolean;
}

function stageFromText(raw: string): string {
  const s = raw.toLowerCase();
  if (s.includes("interview")) return "Interview";
  if (s.includes("offer")) return "Offer";
  if (s.includes("closed") || s.includes("rejected")) return "Closed";
  if (s.includes("applied")) return "Applied";
  if (s.includes("awaiting feedback")) return "Awaiting Feedback";
  if (s.includes("cv ready")) return "CV Ready";
  return raw.replace(/[✅📞]/g, "").trim() || "Identified";
}

export function parsePipeline(content: string): PipelineEntry[] {
  const entries: PipelineEntry[] = [];
  let inTable = false;
  let headerParsed = false;
  let colMap: Record<string, number> = {};
  let rowCount = 0;

  const lines = content.split("\n");
  for (const line of lines) {
    const trimmed = line.trim();

    // Detect header row: starts with | # | or | Company |
    if (trimmed.startsWith("|") && (trimmed.includes("Company") || trimmed.includes("# |")) && !headerParsed) {
      inTable = true;
      const cols = trimmed.split("|").map((c) => c.trim().toLowerCase());
      cols.forEach((c, i) => {
        if (c.includes("#") || c === "") return;
        if (c.includes("company")) colMap["company"] = i;
        if (c.includes("role")) colMap["role"] = i;
        if (c.includes("location") || c.includes("loc")) colMap["location"] = i;
        if (c.includes("ats")) colMap["ats"] = i;
        if (c.includes("stage")) colMap["stage"] = i;
        if (c.includes("applied") && !c.includes("follow") && !c.includes("?")) colMap["applied_date"] = i;
        if (c.includes("follow")) colMap["followup"] = i;
        if (c.includes("applied?") || c === "applied?") colMap["applied_check"] = i;
        if (c === "applied" && !colMap["applied_date"]) colMap["applied_date"] = i;
      });
      headerParsed = true;
      continue;
    }

    // Skip separator row
    if (inTable && trimmed.startsWith("|") && trimmed.includes("---")) {
      continue;
    }

    // Parse data rows
    if (inTable && trimmed.startsWith("|")) {
      const cols = trimmed.split("|").map((c) => c.trim());

      const get = (key: string) => {
        const idx = colMap[key];
        return idx !== undefined ? (cols[idx] || "").replace(/\*\*/g, "").trim() : "";
      };

      const company = get("company");
      const role = get("role");

      if (!company || company === "" || company.toLowerCase() === "company") continue;

      // Check if this row is a separator or header re-occurrence
      if (company.startsWith("-") || company.toLowerCase() === "company") continue;

      rowCount++;
      const stageRaw = get("stage");
      const appliedCheck = get("applied_check");
      const appliedDate = get("applied_date");

      entries.push({
        id: `pl-${rowCount}`,
        company,
        role,
        location: get("location"),
        stage: stageFromText(stageRaw || ""),
        atsScore: get("ats"),
        appliedDate: appliedDate.replace(/\[\d+\]/, "").trim(),
        followUpDate: get("followup"),
        notes: "",
        salary: "",
        applied: appliedCheck.includes("☑") || appliedCheck.includes("[x]") || appliedCheck.includes("yes"),
      });
    }

    // Stop at end of table (blank line after table content)
    if (inTable && headerParsed && trimmed === "" && rowCount > 0) {
      // Don't break yet -- there might be more sections
    }

    // Reset for next table if we hit a new header
    if (trimmed.startsWith("## ") && inTable && rowCount > 0) {
      inTable = false;
      headerParsed = false;
      colMap = {};
    }
  }

  return entries;
}

// ---------------------------------------------------------------------------
// 5. LinkedIn content calendar parser
// ---------------------------------------------------------------------------

function stageFromCalendarStatus(raw: string): ContentStage {
  const s = raw.toLowerCase();
  if (s.includes("posted") || s.includes("live") || s.includes("published")) return "posted";
  if (s.includes("approved") || s.includes("ready")) return "approved";
  if (s.includes("review") || s.includes("reviewing")) return "review";
  return "draft";
}

export function parseContentCalendar(content: string): ContentItem[] {
  const items: ContentItem[] = [];
  let counter = 0;
  const now = new Date().toISOString();

  const lines = content.split("\n");
  for (const line of lines) {
    if (line.startsWith("## ") || line.startsWith("### ")) {
      continue;
    }

    // Look for week/post entries: "**Week N, Post X:**" or "- **Title:**"
    const weekPostMatch = line.match(/^\*\*Week \d+[^*]*\*\*[:\s]*(.*)/);
    if (weekPostMatch) {
      const title = weekPostMatch[1].replace(/\*\*/g, "").trim();
      if (title) {
        counter++;
        items.push({
          id: `cal-${counter}`,
          title: title.slice(0, 100),
          stage: "draft",
          owner: "Content Creator",
          createdAt: now,
          stageUpdatedAt: now,
          slaMinutes: 180,
        });
      }
      continue;
    }

    // Table rows for content calendar
    if (line.startsWith("|") && !line.includes("---") && !line.toLowerCase().includes("week") && !line.toLowerCase().includes("pillar") && !line.toLowerCase().includes("topic") && !line.toLowerCase().includes("hook") && !line.toLowerCase().includes("framework")) {
      const cols = line.split("|").map((c) => c.trim()).filter(Boolean);
      if (cols.length >= 3 && cols[0] && !cols[0].startsWith("-")) {
        const weekOrDate = cols[0];
        const topic = cols[1] || "";
        const status = cols.length > 3 ? cols[3] : "";

        if (weekOrDate && topic && !weekOrDate.toLowerCase().includes("date") && !weekOrDate.toLowerCase().includes("week")) {
          counter++;
          items.push({
            id: `cal-${counter}`,
            title: `${topic}`.slice(0, 100),
            stage: stageFromCalendarStatus(status),
            owner: "Content Creator",
            createdAt: now,
            stageUpdatedAt: now,
            slaMinutes: 180,
          });
        }
      }
    }
  }

  return items;
}

// ---------------------------------------------------------------------------
// 6. cv-history.md parser
// ---------------------------------------------------------------------------

export interface CvHistoryEntry {
  id: string;
  jobTitle: string;
  company: string;
  atsScore: string;
  status: string;
  date: string;
  notes: string;
}

export function parseCvHistory(content: string): CvHistoryEntry[] {
  const entries: CvHistoryEntry[] = [];
  let counter = 0;
  let current: Partial<CvHistoryEntry> | null = null;

  const lines = content.split("\n");
  for (const line of lines) {
    // New entry starts with "## Company - Role"
    if (line.startsWith("## ") && !line.startsWith("### ")) {
      if (current?.company) {
        entries.push({
          id: `cv-${++counter}`,
          jobTitle: current.jobTitle || "",
          company: current.company || "",
          atsScore: current.atsScore || "",
          status: current.status || "",
          date: current.date || "",
          notes: current.notes || "",
        });
      }
      const title = line.replace(/^## /, "").trim();
      const parts = title.split(" - ");
      current = {
        company: parts[0]?.trim() || title,
        jobTitle: parts.slice(1).join(" - ").trim(),
      };
      continue;
    }

    if (!current) continue;

    const match = line.match(/^- \*\*([^*]+)\*\*[:\s]*(.*)/);
    if (match) {
      const key = match[1].trim().toLowerCase();
      const val = match[2].trim();
      if (key.includes("ats") || key.includes("score")) current.atsScore = val;
      else if (key.includes("status")) current.status = val;
      else if (key.includes("date")) current.date = val;
      else if (key.includes("job title")) current.jobTitle = val;
      else if (key.includes("notes") || key.includes("match notes")) current.notes = val;
    }
  }

  if (current?.company) {
    entries.push({
      id: `cv-${++counter}`,
      jobTitle: current.jobTitle || "",
      company: current.company || "",
      atsScore: current.atsScore || "",
      status: current.status || "",
      date: current.date || "",
      notes: current.notes || "",
    });
  }

  return entries;
}

// ---------------------------------------------------------------------------
// Re-export shape adapters for module-store compatibility
// ---------------------------------------------------------------------------

export function parsedTasksToSnapshotTasks(tasks: ParsedTask[]): TaskItem[] {
  return tasks;
}

export function parsedMemoryToMemoryEntries(mem: ParsedMemory): MemoryEntry[] {
  const entries: MemoryEntry[] = [];
  let idx = 0;

  for (const p of mem.priorities) {
    entries.push({ id: `prio-${idx++}`, type: "decision", text: p, updatedAt: new Date().toISOString() });
  }

  for (const d of mem.decisions.slice(0, 5)) {
    entries.push(d);
  }

  for (const t of mem.lessons.slice(0, 5)) {
    entries.push(t);
  }

  return entries;
}

export function parsedGoalsToProjectEntries(goals: ParsedGoals): ProjectEntry[] {
  return goals.objectives.map((obj) => ({
    id: obj.id,
    name: obj.title,
    progress: obj.progress,
    linkedTasks: obj.keyResults.slice(0, 2),
  }));
}

export function getDefaultTeamEntries(): TeamEntry[] {
  return [
    { id: "agent-nasr", name: "NASR", focus: "Strategic orchestration", status: "active" },
    { id: "agent-cv", name: "CV Optimizer", focus: "ATS-optimized CVs", status: "active" },
    { id: "agent-job", name: "Job Hunter", focus: "Role scan and scoring", status: "busy" },
    { id: "agent-research", name: "Researcher", focus: "Intelligence and research", status: "active" },
    { id: "agent-content", name: "Content Creator", focus: "LinkedIn drafts", status: "active" },
  ];
}

export function systemMetricsToOfficeEntries(metrics: {
  ram?: { used: number; total: number };
  disk?: { used: number; total: number };
  gateway?: { status: string; uptime?: string };
  ollama?: { status: string };
}): OfficeMetric[] {
  const entries: OfficeMetric[] = [];

  if (metrics.ram) {
    const pct = Math.round((metrics.ram.used / metrics.ram.total) * 100);
    entries.push({ id: "ram", label: "RAM usage", value: `${pct}% (${metrics.ram.used}/${metrics.ram.total} MB)`, trend: pct > 80 ? "up" : "flat" });
  }

  if (metrics.disk) {
    const pct = Math.round((metrics.disk.used / metrics.disk.total) * 100);
    entries.push({ id: "disk", label: "Disk usage", value: `${pct}%`, trend: pct > 85 ? "up" : "flat" });
  }

  if (metrics.gateway) {
    entries.push({ id: "gateway", label: "Gateway", value: metrics.gateway.status, trend: metrics.gateway.status === "healthy" ? "flat" : "down" });
  }

  if (metrics.ollama) {
    entries.push({ id: "ollama", label: "Ollama", value: metrics.ollama.status, trend: "flat" });
  }

  return entries;
}

export function docsIndexToDocsEntries(
  docs: Array<{ path: string; title: string; category: string; updatedAt: string; sizeBytes: number }>
): DocsEntry[] {
  return docs.map((d, i) => ({
    id: `doc-${i}`,
    title: d.title,
    category: d.category,
    updatedAt: d.updatedAt,
  }));
}
