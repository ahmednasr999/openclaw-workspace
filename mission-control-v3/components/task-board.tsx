"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { boardColumns, seedActivity, seedTasks, TaskItem, TaskStatus } from "@/lib/parity";
import { Panel } from "@/components/ui";

const defaultForm = {
  title: "",
  assignee: "NASR",
  priority: "medium",
  dueDate: "",
};

export function TaskBoard() {
  const [tasks, setTasks] = useState<TaskItem[]>(seedTasks);
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
        if (!response.ok) {
          throw new Error("Failed to load tasks");
        }

        const payload = await response.json() as { tasks: TaskItem[] };
        if (active && Array.isArray(payload.tasks) && payload.tasks.length > 0) {
          setTasks(payload.tasks);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Unknown error");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    hydrateTasks();

    return () => {
      active = false;
    };
  }, []);

  const telemetry = useMemo(() => {
    const done = tasks.filter((t) => t.status === "done").length;
    const progressPercent = Math.round((done / Math.max(tasks.length, 1)) * 100);
    const latencyMs = 240 + tasks.filter((t) => t.priority === "high").length * 15;
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

    setActivity((prev) => [
      { id: `a-${Date.now()}`, text: `task_moved: ${taskId} -> ${status}`, meta: "task-board · user", context: "task_moved", ts: Date.now() },
      ...prev,
    ].slice(0, 20));
  }

  async function onCreateTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.title.trim() || !form.assignee.trim() || !form.dueDate) {
      return;
    }

    setIsSubmitting(true);

    const response = await fetch("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, status: "backlog" }),
    });

    setIsSubmitting(false);

    if (!response.ok) {
      return;
    }

    const payload = await response.json() as { task: TaskItem };
    setTasks((prev) => [payload.task, ...prev]);
    setActivity((prev) => [
      { id: `a-${Date.now()}`, text: `task_created: ${payload.task.title}`, meta: `task-board · ${payload.task.assignee}`, context: "task_created", ts: Date.now() },
      ...prev,
    ].slice(0, 20));
    setForm(defaultForm);
  }

  return (
    <div className="space-y-4">
      {loading && <p className="text-sm text-zinc-400">Loading board data...</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}
      <div className="grid gap-3 md:grid-cols-4">
        <Panel title="Health"><p className={telemetry.critical ? "text-red-400" : "text-emerald-400"}>{telemetry.critical ? "Critical" : "Stable"}</p></Panel>
        <Panel title="Progress"><p className="text-2xl font-semibold">{telemetry.progressPercent}%</p></Panel>
        <Panel title="Latency"><p className="text-2xl font-semibold">{telemetry.latencyMs} ms</p></Panel>
        <Panel title="Heartbeat"><p className="text-emerald-400">{telemetry.heartbeat}</p></Panel>
      </div>

      <Panel title="Create task">
        <form className="grid gap-2 md:grid-cols-5" onSubmit={onCreateTask}>
          <input
            value={form.title}
            onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
            className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1"
            placeholder="Task title"
          />
          <input
            value={form.assignee}
            onChange={(event) => setForm((prev) => ({ ...prev, assignee: event.target.value }))}
            className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1"
            placeholder="Assignee"
          />
          <select
            value={form.priority}
            onChange={(event) => setForm((prev) => ({ ...prev, priority: event.target.value }))}
            className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
          <input
            type="date"
            value={form.dueDate}
            onChange={(event) => setForm((prev) => ({ ...prev, dueDate: event.target.value }))}
            className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1"
          />
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded border border-emerald-700 bg-emerald-900/40 px-2 py-1 text-emerald-200 disabled:opacity-50"
          >
            {isSubmitting ? "Creating..." : "Create"}
          </button>
        </form>
      </Panel>

      <div className="grid gap-3 xl:grid-cols-5">
        {boardColumns.map((col) => {
          const items = tasks.filter((t) => t.status === col.key);
          const over = typeof col.wipLimit === "number" && items.length > col.wipLimit;
          return (
            <section
              key={col.key}
              className={`rounded-lg border bg-[#111111] p-3 ${over ? "border-red-700" : "border-zinc-800"}`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => dragTaskId && moveTask(dragTaskId, col.key)}
            >
              <header className="mb-2 flex items-center justify-between text-sm">
                <span>{col.label} ({items.length})</span>
                {typeof col.wipLimit === "number" && (
                  <span className={`rounded px-2 py-0.5 text-xs ${over ? "bg-red-900 text-red-200" : "bg-emerald-900/40 text-emerald-300"}`}>
                    {items.length}/{col.wipLimit} WIP
                  </span>
                )}
              </header>
              <div className="space-y-2 min-h-24">
                {items.map((task) => (
                  <article
                    key={task.id}
                    draggable
                    onDragStart={() => setDragTaskId(task.id)}
                    className={`rounded border p-2 text-sm ${over ? "border-red-700" : "border-zinc-700"}`}
                  >
                    <h4 className="font-medium">{task.title}</h4>
                    <p className="text-xs text-zinc-400">{task.assignee} · {task.priority} · due {task.dueDate}</p>
                  </article>
                ))}
              </div>
            </section>
          );
        })}
      </div>

      <Panel title="Activity and telemetry stream">
        <ul className="space-y-2 text-sm text-zinc-300">
          {activity.map((row) => (
            <li key={row.id} className="rounded border border-zinc-800 bg-zinc-950/50 p-2">
              <div>{row.text}</div>
              <div className="text-xs text-zinc-500">{row.meta}</div>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
