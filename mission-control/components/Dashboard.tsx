"use client";

interface Task {
  id: number;
  title: string;
  status: string;
  priority: string;
  category: string;
  dueDate?: string;
  completedDate?: string;
  assignee: string;
  createdAt: string;
}

interface DashboardProps {
  tasks: Task[];
}

export function Dashboard({ tasks }: DashboardProps) {
  // Stats
  const completedThisWeek = tasks.filter((t) => {
    if (t.status !== "Completed") return false;
    const completed = new Date(t.completedDate || "");
    const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    return completed >= weekAgo;
  }).length;

  const inProgress = tasks.filter((t) => t.status === "In Progress").length;
  const overdue = tasks.filter((t) => {
    if (!t.dueDate || t.status === "Completed") return false;
    return new Date(t.dueDate) < new Date();
  }).length;

  const byCategory: Record<string, { count: number; icon: string }> = {
    "Job Search": { count: tasks.filter((t) => t.category === "Job Search").length, icon: "🎯" },
    Content: { count: tasks.filter((t) => t.category === "Content").length, icon: "📝" },
    Networking: { count: tasks.filter((t) => t.category === "Networking").length, icon: "🤝" },
    Applications: { count: tasks.filter((t) => t.category === "Applications").length, icon: "📋" },
    Interviews: { count: tasks.filter((t) => t.category === "Interviews").length, icon: "🎤" },
    Task: { count: tasks.filter((t) => t.category === "Task").length, icon: "📌" },
  };

  const byPriority: Record<string, { count: number; color: string; bg: string }> = {
    High: { count: tasks.filter((t) => t.priority === "High").length, color: "text-red-400", bg: "bg-red-500" },
    Medium: { count: tasks.filter((t) => t.priority === "Medium").length, color: "text-yellow-400", bg: "bg-yellow-500" },
    Low: { count: tasks.filter((t) => t.priority === "Low").length, color: "text-green-400", bg: "bg-green-500" },
  };

  const byAssignee = {
    Ahmed: tasks.filter((t) => t.assignee === "Ahmed" && t.status !== "Completed").length,
    OpenClaw: tasks.filter((t) => t.assignee === "OpenClaw" && t.status !== "Completed").length,
    Both: tasks.filter((t) => t.assignee === "Both" && t.status !== "Completed").length,
  };

  // Completion rate
  const completionRate = tasks.length > 0 ? Math.round((tasks.filter(t => t.status === "Completed").length / tasks.length) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="stat-card stat-card-green glass rounded-xl p-5">
          <div className="text-3xl font-bold text-green-400">{completedThisWeek}</div>
          <div className="text-xs text-gray-400 mt-1">Completed This Week</div>
          <div className="mt-3 h-1 bg-gray-800 rounded-full overflow-hidden">
            <div className="h-full bg-green-500 rounded-full" style={{ width: `${completionRate}%` }} />
          </div>
          <div className="text-[10px] text-gray-600 mt-1">{completionRate}% completion rate</div>
        </div>
        
        <div className="stat-card stat-card-yellow glass rounded-xl p-5">
          <div className="text-3xl font-bold text-yellow-400">{inProgress}</div>
          <div className="text-xs text-gray-400 mt-1">In Progress</div>
        </div>
        
        <div className="stat-card stat-card-red glass rounded-xl p-5">
          <div className="text-3xl font-bold text-red-400">{overdue}</div>
          <div className="text-xs text-gray-400 mt-1">Overdue</div>
          {overdue > 0 && <div className="text-[10px] text-red-500 mt-2">⚠️ Needs attention</div>}
        </div>
        
        <div className="stat-card stat-card-blue glass rounded-xl p-5">
          <div className="text-3xl font-bold text-indigo-400">{tasks.length}</div>
          <div className="text-xs text-gray-400 mt-1">Total Tasks</div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* By Category */}
        <div className="glass rounded-xl p-5">
          <h3 className="text-sm font-semibold mb-4 text-gray-300">By Category</h3>
          <div className="space-y-3">
            {Object.entries(byCategory).map(([category, { count, icon }]) => (
              <div key={category} className="flex items-center gap-3">
                <span className="text-sm">{icon}</span>
                <div className="flex-1">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-400">{category}</span>
                    <span className="text-gray-500">{count}</span>
                  </div>
                  <div className="h-1.5 bg-gray-800/50 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-500 rounded-full transition-all duration-500"
                      style={{ width: `${tasks.length > 0 ? (count / tasks.length) * 100 : 0}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* By Priority */}
        <div className="glass rounded-xl p-5">
          <h3 className="text-sm font-semibold mb-4 text-gray-300">By Priority</h3>
          <div className="space-y-3">
            {Object.entries(byPriority).map(([priority, { count, color, bg }]) => (
              <div key={priority} className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${bg}`} />
                <div className="flex-1">
                  <div className="flex justify-between text-xs mb-1">
                    <span className={color}>{priority}</span>
                    <span className="text-gray-500">{count}</span>
                  </div>
                  <div className="h-1.5 bg-gray-800/50 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${bg}`}
                      style={{ width: `${tasks.length > 0 ? (count / tasks.length) * 100 : 0}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Assignee breakdown */}
          <div className="mt-6 pt-4 border-t border-white/5">
            <h4 className="text-xs font-semibold text-gray-400 mb-3">Active by Assignee</h4>
            <div className="flex gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm">👤</span>
                <span className="text-xs text-blue-400">{byAssignee.Ahmed}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm">🤖</span>
                <span className="text-xs text-purple-400">{byAssignee.OpenClaw}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm">👥</span>
                <span className="text-xs text-indigo-400">{byAssignee.Both}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="glass rounded-xl p-5">
          <h3 className="text-sm font-semibold mb-4 text-gray-300">Recent Activity</h3>
          <div className="space-y-2">
            {tasks
              .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
              .slice(0, 8)
              .map((task) => (
              <div key={task.id} className="flex items-center gap-2 py-1.5 border-b border-white/5 last:border-0">
                <span className="text-xs">
                  {task.status === "Completed" ? "✅" :
                   task.status === "In Progress" ? "🔄" :
                   task.status === "OpenClaw Tasks" ? "🤖" : "📋"}
                </span>
                <span className="flex-1 text-xs text-gray-400 truncate">{task.title}</span>
                <span className={`text-[10px] ${
                  task.assignee === "Ahmed" ? "text-blue-500" : "text-purple-500"
                }`}>{task.assignee === "Ahmed" ? "👤" : "🤖"}</span>
              </div>
            ))}
            {tasks.length === 0 && (
              <div className="text-gray-600 text-center py-6 text-xs">No tasks yet</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
