import { Shell } from "@/components/shell";
import { getTasks, getPipeline, getContentItems, getSystemHealth, getGoals } from "@/lib/sync";
import { DashboardAlertBanner } from "@/components/dashboard-alert-banner";

export const revalidate = 30;

function stageBadgeClass(stage: string): string {
  const s = stage.toLowerCase();
  if (s.includes("interview") || s.includes("offer")) return "bg-amber-900/50 text-amber-300 border border-amber-700";
  if (s.includes("applied") || s.includes("awaiting")) return "bg-blue-900/50 text-blue-300 border border-blue-700";
  if (s.includes("closed") || s.includes("rejected")) return "bg-zinc-800 text-zinc-400 border border-zinc-700";
  return "bg-zinc-800 text-zinc-300 border border-zinc-700";
}

function priorityDotClass(priority: string): string {
  if (priority === "high") return "bg-red-500";
  if (priority === "medium") return "bg-amber-500";
  return "bg-emerald-500";
}

function priorityBorderClass(priority: string): string {
  if (priority === "high") return "priority-high";
  if (priority === "medium") return "priority-medium";
  return "priority-low";
}

interface StatCardProps {
  label: string;
  value: string;
  sub: string;
  colorClass?: string;
}

function StatCard({ label, value, sub, colorClass = "gradient-text" }: StatCardProps) {
  return (
    <div className="glass rounded-[10px] p-5 card-glow group">
      <p className="text-xs font-semibold uppercase tracking-widest text-[#4B6A9B] mb-2">{label}</p>
      <p className={`text-4xl font-bold ${colorClass}`}>{value}</p>
      <p className="mt-2 text-xs text-[#2D4163]">{sub}</p>
    </div>
  );
}

export default async function DashboardPage() {
  const [tasks, pipeline, contentItems, health, goals] = await Promise.all([
    getTasks(),
    getPipeline(),
    getContentItems(),
    getSystemHealth(),
    getGoals(),
  ]);

  const openTasks = tasks.filter((t) => t.status === "in_progress" || t.status === "backlog" || t.status === "review").length;
  const activeApplications = pipeline.filter((p) => {
    const s = p.stage.toLowerCase();
    return !s.includes("closed") && !s.includes("rejected") && p.applied;
  }).length;
  const contentDue = contentItems.filter((c) => c.stage === "draft" || c.stage === "review").length;
  const healthScore = health.score;

  // Check for tasks with deadline within 48 hours
  const checkTime = new Date();
  const urgentTasks = tasks.filter((t) => {
    if (t.status === "done" || !t.dueDate) return false;
    const due = new Date(t.dueDate).getTime();
    const hoursLeft = (due - checkTime.getTime()) / (1000 * 3600);
    return hoursLeft >= 0 && hoursLeft <= 48;
  });

  const topTasks = tasks
    .filter((t) => t.status !== "done" && t.status !== "recurring")
    .sort((a, b) => {
      const po: Record<string, number> = { high: 0, medium: 1, low: 2 };
      return (po[a.priority] ?? 2) - (po[b.priority] ?? 2);
    })
    .slice(0, 5);

  const topPipeline = pipeline
    .filter((p) => {
      const s = p.stage.toLowerCase();
      return !s.includes("closed") && !s.includes("rejected") && p.applied;
    })
    .sort((a, b) => {
      const stageOrder: Record<string, number> = { Interview: 0, Offer: 0, "Awaiting Feedback": 1, Applied: 2, "CV Ready": 3 };
      return (stageOrder[a.stage] ?? 4) - (stageOrder[b.stage] ?? 4);
    })
    .slice(0, 4);

  const topGoals = goals.objectives.filter((o) => o.keyResults.length > 0).slice(0, 4);

  const healthColor = healthScore >= 80 ? "gradient-text-green" : healthScore >= 50 ? "gradient-text-warm" : "gradient-text-warm";

  return (
    <Shell title="Dashboard" description="Snapshot of priorities, execution rhythm, and system health.">
      {/* Alert banner for urgent tasks */}
      <DashboardAlertBanner urgentCount={urgentTasks.length} urgentTitles={urgentTasks.slice(0, 3).map((t) => t.title)} />

      {/* Stat cards */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Open tasks" value={String(openTasks)} sub="active and in-progress" />
        <StatCard label="Active applications" value={String(activeApplications)} sub="non-closed pipeline entries" />
        <StatCard label="Content due" value={String(contentDue)} sub="draft and review items" colorClass="gradient-text-warm" />
        <StatCard
          label="System health"
          value={`${healthScore}%`}
          sub={health.gateway.status === "healthy" ? "gateway healthy" : `gateway: ${health.gateway.status}`}
          colorClass={healthColor}
        />
      </div>

      {/* Lower grid */}
      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        {/* Priority tasks */}
        <div className="glass rounded-[10px] p-4 card-glow">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">Priority tasks</h3>
          {topTasks.length === 0 ? (
            <p className="text-sm text-[#2D4163]">No open tasks.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {topTasks.map((task) => (
                <li
                  key={task.id}
                  className={`glass-light rounded-[8px] p-2.5 flex items-start gap-2.5 transition-smooth hover:bg-[rgba(79,142,247,0.05)] ${priorityBorderClass(task.priority)}`}
                >
                  <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${priorityDotClass(task.priority)}`} />
                  <div className="min-w-0">
                    <p className="truncate text-[#e2e8f0] text-xs font-medium">{task.title}</p>
                    <p className="text-[10px] text-[#4B6A9B] mt-0.5">{task.section}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Job pipeline */}
        <div className="glass rounded-[10px] p-4 card-glow">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">Job pipeline</h3>
          {topPipeline.length === 0 ? (
            <p className="text-sm text-[#2D4163]">No active applications.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {topPipeline.map((entry) => (
                <li key={entry.id} className="glass-light rounded-[8px] p-2.5 transition-smooth hover:bg-[rgba(79,142,247,0.05)]">
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate font-semibold text-[#e2e8f0] text-xs">{entry.company}</p>
                    <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] ${stageBadgeClass(entry.stage)}`}>{entry.stage}</span>
                  </div>
                  <p className="truncate text-[10px] text-[#6B8AAE] mt-0.5">{entry.role}</p>
                  {entry.location && <p className="text-[10px] text-[#2D4163]">{entry.location}</p>}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Goal progress */}
        <div className="glass rounded-[10px] p-4 card-glow">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">Goal progress</h3>
          {topGoals.length === 0 ? (
            <p className="text-sm text-[#2D4163]">No goals with key results.</p>
          ) : (
            <ul className="space-y-4 text-sm">
              {topGoals.map((obj) => (
                <li key={obj.id}>
                  <div className="mb-1.5 flex items-center justify-between gap-2">
                    <p className="truncate text-xs text-[#a8c4e8]">{obj.title}</p>
                    <span className="ml-2 shrink-0 text-[10px] text-[#4B6A9B]">{obj.progress}%</span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-[#1E2D45]">
                    <div
                      className="h-1.5 rounded-full gradient-accent"
                      style={{ width: `${Math.min(100, obj.progress)}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Shell>
  );
}
