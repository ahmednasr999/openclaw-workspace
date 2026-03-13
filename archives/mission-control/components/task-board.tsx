"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { boardColumns, seedActivity, TaskItem, TaskStatus } from "@/lib/parity";

const defaultForm = {
  title: "",
  assignee: "NASR",
  priority: "medium",
  dueDate: "",
};

type ActivityEvent = {
  id: string;
  text: string;
  meta: string;
  context: string;
  ts: number;
};

function priorityBorderClass(priority: string) {
  if (priority === "high") return "priority-high";
  if (priority === "medium") return "priority-medium";
  return "priority-low";
}

function priorityBadgeClass(priority: string) {
  if (priority === "high") return "text-red-400 bg-red-900/20 border border-red-800/40";
  if (priority === "medium") return "text-amber-300 bg-amber-900/20 border border-amber-800/40";
  return "text-emerald-400 bg-emerald-900/20 border border-emerald-800/40";
}

function columnHeaderClass(key: string) {
  if (key === "backlog") return "text-red-400 border-b-red-700";
  if (key === "in_progress") return "text-blue-400 border-b-blue-700";
  if (key === "review") return "text-amber-400 border-b-amber-700";
  if (key === "done") return "text-emerald-400 border-b-emerald-700";
  if (key === "recurring") return "text-purple-400 border-b-purple-700";
  return "text-[#6B8AAE] border-b-[#1E2D45]";
}

function columnBgClass(key: string) {
  if (key === "backlog") return "bg-red-900/5";
  if (key === "in_progress") return "bg-blue-900/5";
  if (key === "review") return "bg-amber-900/5";
  if (key === "done") return "bg-emerald-900/5";
  if (key === "recurring") return "bg-purple-900/5";
  return "";
}

function columnBadgeClass(key: string) {
  if (key === "backlog") return "bg-red-900/30 text-red-300 border border-red-800/40";
  if (key === "in_progress") return "bg-blue-900/30 text-blue-300 border border-blue-800/40";
  if (key === "review") return "bg-amber-900/30 text-amber-300 border border-amber-800/40";
  if (key === "done") return "bg-emerald-900/30 text-emerald-300 border border-emerald-800/40";
  if (key === "recurring") return "bg-purple-900/30 text-purple-300 border border-purple-800/40";
  return "bg-[#1E2D45] text-[#6B8AAE]";
}

export function TaskBoard() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [activity, setActivity] = useState(seedActivity);
  const [dragTaskId, setDragTaskId] = useState<string>("");
  const [form, setForm] = useState(defaultForm);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function hydrateTasks() {
      setLoading(true);
      setError("");
      try {
        const response = await fetch("/api/tasks", { cache: "no-store" });
        if (!response.ok) throw new Error("Failed to load tasks");
        const payload = await response.json() as { tasks: TaskItem[] };
        if (active && Array.isArray(payload.tasks)) {
          setTasks(payload.tasks);
        }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        if (active) setLoading(false);
      }
    }

    hydrateTasks();
    return () => { active = false; };
  }, []);

  const telemetry = useMemo(() => {
    const done = tasks.filter((t) => t.status === "done").length;
    const progressPercent = Math.round((done / Math.max(tasks.length, 1)) * 100);
    const highCount = tasks.filter((t) => t.priority === "high" && t.status !== "done").length;
    const latencyMs = 240 + highCount * 15;
    const critical = latencyMs > 300;
    return { progressPercent, latencyMs, heartbeat: "Pulse active", critical };
  }, [tasks]);

  async function moveTask(taskId: string, status: TaskStatus) {
    setTasks((prev) => prev.map((task) => (task.id === taskId ? { ...task, status } : task)));

    await fetch("/api/tasks", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ taskId, status }),
    });

    const newEvent: ActivityEvent = {
      id: `a-${Date.now()}`,
      text: `task_moved: ${taskId} -> ${status}`,
      meta: "task-board - user",
      context: "task_moved",
      ts: Date.now(),
    };
    setActivity((prev) => [newEvent, ...prev].slice(0, 20));
  }

  async function onCreateTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.title.trim() || !form.assignee.trim() || !form.dueDate) return;

    setIsSubmitting(true);
    const response = await fetch("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, status: "backlog" }),
    });
    setIsSubmitting(false);
    if (!response.ok) return;

    const payload = await response.json() as { task: TaskItem };
    setTasks((prev) => [payload.task, ...prev]);
    const newEvent: ActivityEvent = {
      id: `a-${Date.now()}`,
      text: `task_created: ${payload.task.title}`,
      meta: `task-board - ${payload.task.assignee}`,
      context: "task_created",
      ts: Date.now(),
    };
    setActivity((prev) => [newEvent, ...prev].slice(0, 20));
    setForm(defaultForm);
  }

  return (
    <div className="space-y-4">
      {loading && <p className="text-sm text-[#4B6A9B]">Loading tasks from active-tasks.md...</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}

      {/* Mini stat row */}
      <div className="grid gap-3 md:grid-cols-4">
        {[
          { label: "Health", value: telemetry.critical ? "Critical" : "Stable", cls: telemetry.critical ? "text-red-400" : "text-emerald-400" },
          { label: "Progress", value: `${telemetry.progressPercent}%`, cls: "gradient-text" },
          { label: "Open", value: String(tasks.filter((t) => t.status !== "done").length), cls: "text-[#e2e8f0]" },
          { label: "Total", value: String(tasks.length), cls: "text-[#e2e8f0]" },
        ].map(({ label, value, cls }) => (
          <div key={label} className="glass rounded-[10px] p-3 card-glow">
            <p className="text-[10px] uppercase tracking-widest text-[#4B6A9B]">{label}</p>
            <p className={`text-2xl font-bold mt-1 ${cls}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Create task */}
      <div className="glass rounded-[10px] p-4">
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">Create task</h3>
        <form className="grid gap-2 md:grid-cols-5" onSubmit={onCreateTask}>
          <input
            value={form.title}
            onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
            className="rounded-[6px] border border-[#1E2D45] bg-[#080C16] px-2 py-1.5 text-sm text-[#e2e8f0] placeholder-[#4B6A9B] outline-none focus:border-[#4F8EF7] transition-colors"
            placeholder="Task title"
          />
          <input
            value={form.assignee}
            onChange={(e) => setForm((prev) => ({ ...prev, assignee: e.target.value }))}
            className="rounded-[6px] border border-[#1E2D45] bg-[#080C16] px-2 py-1.5 text-sm text-[#e2e8f0] placeholder-[#4B6A9B] outline-none focus:border-[#4F8EF7] transition-colors"
            placeholder="Assignee"
          />
          <select
            value={form.priority}
            onChange={(e) => setForm((prev) => ({ ...prev, priority: e.target.value }))}
            className="rounded-[6px] border border-[#1E2D45] bg-[#080C16] px-2 py-1.5 text-sm text-[#e2e8f0] outline-none focus:border-[#4F8EF7] transition-colors"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
          <input
            type="date"
            value={form.dueDate}
            onChange={(e) => setForm((prev) => ({ ...prev, dueDate: e.target.value }))}
            className="rounded-[6px] border border-[#1E2D45] bg-[#080C16] px-2 py-1.5 text-sm text-[#e2e8f0] outline-none focus:border-[#4F8EF7] transition-colors"
          />
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-[6px] border border-emerald-700 bg-emerald-900/30 px-2 py-1.5 text-sm text-emerald-300 hover:bg-emerald-900/50 disabled:opacity-50 transition-colors"
          >
            {isSubmitting ? "Creating..." : "Create"}
          </button>
        </form>
      </div>

      {/* Kanban board */}
      <div className="grid gap-3 xl:grid-cols-5">
        {boardColumns.map((col) => {
          const items = tasks.filter((t) => t.status === col.key);
          const over = typeof col.wipLimit === "number" && items.length > col.wipLimit;
          return (
            <section
              key={col.key}
              className={`rounded-[10px] border border-[#1E2D45] p-3 ${columnBgClass(col.key)} ${over ? "border-red-700/50" : ""} transition-smooth`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => dragTaskId && moveTask(dragTaskId, col.key)}
            >
              <header className={`mb-3 flex items-center justify-between pb-2 border-b ${columnHeaderClass(col.key)}`}>
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-semibold ${columnHeaderClass(col.key).split(" ")[0]}`}>{col.label}</span>
                  <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${columnBadgeClass(col.key)}`}>{items.length}</span>
                </div>
                {typeof col.wipLimit === "number" && (
                  <span className={`rounded px-1.5 py-0.5 text-[10px] ${over ? "bg-red-900/40 text-red-300 border border-red-800/40" : "bg-[#1E2D45] text-[#4B6A9B]"}`}>
                    {items.length}/{col.wipLimit}
                  </span>
                )}
              </header>
              <div className="space-y-2 min-h-24">
                {items.map((task) => (
                  <article
                    key={task.id}
                    draggable
                    onDragStart={() => setDragTaskId(task.id)}
                    className={`glass-light rounded-[8px] p-2.5 text-xs cursor-grab active:cursor-grabbing transition-smooth hover:bg-[rgba(79,142,247,0.06)] ${priorityBorderClass(task.priority)}`}
                  >
                    <h4 className="font-medium leading-snug text-[#e2e8f0] mb-1.5">{task.title}</h4>
                    <div className="flex flex-wrap items-center gap-1">
                      <span className="text-[#4B6A9B]">{task.assignee}</span>
                      <span className={`rounded px-1.5 py-0.5 ${priorityBadgeClass(task.priority)}`}>{task.priority}</span>
                      {task.dueDate && (
                        <span className="ts text-[#2D4163]">due {task.dueDate}</span>
                      )}
                    </div>
                    {"section" in task && (task as TaskItem & { section?: string }).section && (
                      <p className="mt-1 text-[10px] text-[#4B6A9B] truncate">
                        {((task as TaskItem & { section?: string }).section || "").replace(/[🔴🟡🟢✅]\s*/g, "")}
                      </p>
                    )}
                  </article>
                ))}
                {items.length === 0 && (
                  <p className="text-[10px] text-[#2D4163] text-center pt-4">Drop here</p>
                )}
              </div>
            </section>
          );
        })}
      </div>

      {/* Activity stream */}
      <div className="glass rounded-[10px] p-4">
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">Activity and telemetry stream</h3>
        <ul className="space-y-1.5 text-sm text-[#6B8AAE]">
          {activity.map((row) => (
            <li key={row.id} className="glass-light rounded-[6px] p-2">
              <div className="text-[#a8c4e8] text-xs">{row.text}</div>
              <div className="ts mt-0.5">{row.meta}</div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
