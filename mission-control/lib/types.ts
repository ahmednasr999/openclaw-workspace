export type ScreenKey =
  | "dashboard"
  | "tasks"
  | "content"
  | "calendar"
  | "memory"
  | "ai-team"
  | "contacts"
  | "settings";

export type CalendarCategory = "task" | "content" | "meeting" | "automation";

export interface CalendarEvent {
  id: string;
  title: string;
  date: string;
  time: string;
  category: CalendarCategory;
  source: "Tasks" | "Content" | "Meetings" | "Automations";
  details: string;
}

export interface Contact {
  id: string;
  name: string;
  role: string;
  company: string;
  email: string;
  category: "Executive" | "Hiring" | "Partner" | "Team";
  notes: string;
}

export interface DocsEntry {
  id: string;
  title: string;
  category: string;
  updatedAt: string;
}

export interface MemoryEntry {
  id: string;
  type: "decision" | "thread";
  text: string;
  updatedAt: string;
}

export interface TeamEntry {
  id: string;
  name: string;
  focus: string;
  status: "active" | "busy" | "idle";
}

export interface OfficeMetric {
  id: string;
  label: string;
  value: string;
  trend: "up" | "flat" | "down";
}

export interface ProjectEntry {
  id: string;
  name: string;
  progress: number;
  linkedTasks: string[];
}

export interface SnapshotTask {
  id: string;
  title: string;
  assignee: string;
  priority: "low" | "medium" | "high";
  dueDate: string;
  status: "recurring" | "backlog" | "in_progress" | "review" | "done";
}

export interface ModuleSnapshot {
  docs: DocsEntry[];
  memory: MemoryEntry[];
  team: TeamEntry[];
  office: OfficeMetric[];
  projects: ProjectEntry[];
  tasks: SnapshotTask[];
}

export type BackendHealthLevel = "healthy" | "degraded" | "critical";

export interface BackendHealth {
  reachable: boolean;
  latencyMs: number;
  level: BackendHealthLevel;
  reason: string;
  checkedAt: string;
}

export interface HandoffValidationResult {
  valid: boolean;
  reason: string;
  confidence: number;
  matchedRule: string;
}

export interface HandoffItem {
  id: string;
  url: string;
  roleHint: string;
  companyHint: string;
  score: number;
  validation: HandoffValidationResult;
  createdAt: string;
}

export interface JobRadarLead {
  id: string;
  role: string;
  company: string;
  ageHours: number;
  salaryFit: number;
  strategicFit: number;
  sourceQuality: number;
  totalScore: number;
  threshold: number;
  decision: "qualified" | "watch" | "dropped";
  droppedReason?: string;
}

export type ContentStage = "draft" | "review" | "approved" | "posted";

export interface ContentItem {
  id: string;
  title: string;
  stage: ContentStage;
  owner: string;
  createdAt: string;
  stageUpdatedAt: string;
  slaMinutes: number;
}

export interface CronJob {
  id: string;
  name: string;
  schedule: string;
  status: "healthy" | "failing" | "paused";
  consecutiveFailures: number;
  lastRunAt: string;
  lastSuccessAt: string;
  nextRunAt: string;
}

export interface OpsSnapshot {
  handoffQueue: HandoffItem[];
  radarLeads: JobRadarLead[];
  contentItems: ContentItem[];
  cronJobs: CronJob[];
  heartbeat: {
    status: "healthy" | "degraded";
    updatedAt: string;
    tick: number;
  };
}
