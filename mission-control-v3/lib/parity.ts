export type TaskStatus = "recurring" | "backlog" | "in_progress" | "review" | "done";

export interface TaskItem {
  id: string;
  title: string;
  assignee: string;
  priority: "low" | "medium" | "high";
  dueDate: string;
  status: TaskStatus;
  description?: string;
}

export interface ActivityEvent {
  id: string;
  text: string;
  meta: string;
  context: string;
  ts: number;
}

export const boardColumns: { key: TaskStatus; label: string; wipLimit?: number }[] = [
  { key: "recurring", label: "Recurring" },
  { key: "backlog", label: "Backlog", wipLimit: 6 },
  { key: "in_progress", label: "In Progress", wipLimit: 4 },
  { key: "review", label: "Review", wipLimit: 3 },
  { key: "done", label: "Done" },
];

export const seedTasks: TaskItem[] = [
  { id: "t1", title: "Finalize Delphi prep pack", assignee: "NASR", priority: "high", dueDate: "2026-03-05", status: "in_progress" },
  { id: "t2", title: "Audit stale applications", assignee: "Job Hunter", priority: "medium", dueDate: "2026-03-08", status: "backlog" },
  { id: "t3", title: "Draft AI PMO post", assignee: "Content Creator", priority: "medium", dueDate: "2026-03-06", status: "review" },
  { id: "t4", title: "Calendar cron QA", assignee: "CV Optimizer", priority: "low", dueDate: "2026-03-04", status: "done" },
  { id: "t5", title: "Partner follow-up batch", assignee: "NASR", priority: "high", dueDate: "2026-03-04", status: "in_progress" },
  { id: "t6", title: "Pipeline reconciliation", assignee: "Job Hunter", priority: "high", dueDate: "2026-03-07", status: "review" },
  { id: "t7", title: "Daily heartbeat check", assignee: "NASR", priority: "medium", dueDate: "2026-03-03", status: "recurring" },
  { id: "t8", title: "Role market scan", assignee: "Job Hunter", priority: "medium", dueDate: "2026-03-09", status: "backlog" },
  { id: "t9", title: "Ops playbook cleanup", assignee: "NASR", priority: "medium", dueDate: "2026-03-10", status: "review" },
  { id: "t10", title: "Automation drift fix", assignee: "NASR", priority: "high", dueDate: "2026-03-06", status: "review" },
];

export const seedActivity: ActivityEvent[] = [
  { id: "a1", text: "task_moved: Pipeline reconciliation -> review", meta: "task-board · NASR", context: "task_moved", ts: Date.now() - 60000 },
  { id: "a2", text: "cron_triggered: morning briefing", meta: "calendar-cron · system", context: "cron_triggered", ts: Date.now() - 180000 },
  { id: "a3", text: "url_validated: LinkedIn direct URL accepted", meta: "handoff-gate · NASR", context: "url_validated", ts: Date.now() - 420000 },
];

export const handoffTrend = [71, 74, 76, 78, 80, 82, 83];

export const radarRows = [
  { role: "VP Digital Transformation", company: "HealthFirst GCC", ageHours: 3, droppedReason: "", queueSnapshot: "handoff-ready" },
  { role: "Chief Operating Officer", company: "MedChain", ageHours: 19, droppedReason: "", queueSnapshot: "scored" },
  { role: "Regional PMO Director", company: "CareScale", ageHours: 51, droppedReason: "salary below floor", queueSnapshot: "dropped" },
  { role: "Head of AI PMO", company: "Delta Health", ageHours: 6, droppedReason: "", queueSnapshot: "preflight" },
];
