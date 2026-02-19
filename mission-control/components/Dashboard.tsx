"use client";

import { useState, useEffect } from "react";

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

interface ContentPost {
  id: number;
  title: string;
  status: string;
  platform: string;
  contentType: string;
  assignee: string;
  priority: string;
  createdAt: string;
}

interface DashboardProps {
  tasks: Task[];
}

function isAgentAssignee(assignee: string): boolean {
  const upper = assignee.toUpperCase();
  return (
    upper.includes("NASR") ||
    upper.includes("OPENCLAW") ||
    upper === "QA AGENT" ||
    upper.includes("QA")
  );
}

export function Dashboard({ tasks }: DashboardProps) {
  const [posts, setPosts] = useState<ContentPost[]>([]);
  const [loadingPosts, setLoadingPosts] = useState(true);

  useEffect(() => {
    fetch("/api/content")
      .then((r) => r.json())
      .then((data) => {
        setPosts(Array.isArray(data) ? data : []);
        setLoadingPosts(false);
      })
      .catch(() => setLoadingPosts(false));
  }, []);

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
    "Job Search": { count: tasks.filter((t) => t.category === "Job Search").length, icon: "targetAgent" },
    Content: { count: tasks.filter((t) => t.category === "Content").length, icon: "pen" },
    Networking: { count: tasks.filter((t) => t.category === "Networking").length, icon: "handshake" },
    Applications: { count: tasks.filter((t) => t.category === "Applications").length, icon: "folder" },
    Interviews: { count: tasks.filter((t) => t.category === "Interviews").length, icon: "mic" },
    Task: { count: tasks.filter((t) => t.category === "Task").length, icon: "pin" },
  };

  const byPriority: Record<string, { count: number; color: string; bg: string }> = {
    High: { count: tasks.filter((t) => t.priority === "High").length, color: "text-red-400", bg: "bg-red-500" },
    Medium: { count: tasks.filter((t) => t.priority === "Medium").length, color: "text-yellow-400", bg: "bg-yellow-500" },
    Low: { count: tasks.filter((t) => t.priority === "Low").length, color: "text-green-400", bg: "bg-green-500" },
  };

  // Fixed assignee breakdown: detect NASR/OpenClaw/QA as agent
  const activeTasks = tasks.filter((t) => t.status !== "Completed");
  const byAssignee = {
    Ahmed: activeTasks.filter((t) => t.assignee === "Ahmed").length,
    Agents: activeTasks.filter((t) => isAgentAssignee(t.assignee) && t.assignee !== "Ahmed" && t.assignee !== "Both").length,
    Both: activeTasks.filter((t) => t.assignee === "Both").length,
  };

  // Completion rate
  const completionRate = tasks.length > 0 ? Math.round((tasks.filter(t => t.status === "Completed").length / tasks.length) * 100) : 0;

  // Content pipeline stats
  const totalPosts = posts.length;
  const publishedPosts = posts.filter((p) => p.status === "Published").length;
  const draftPosts = posts.filter((p) => p.status === "Draft").length;
  const reviewPosts = posts.filter((p) => p.status === "Review").length;

  // This week mini timeline (last 7 days, tasks completed per day)
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(today);
    d.setDate(d.getDate() - (6 - i));
    return d;
  });
  const dayLabels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const weekData = weekDays.map((day) => {
    const nextDay = new Date(day);
    nextDay.setDate(nextDay.getDate() + 1);
    const count = tasks.filter((t) => {
      if (t.status !== "Completed" || !t.completedDate) return false;
      const d = new Date(t.completedDate);
      return d >= day && d < nextDay;
    }).length;
    return { label: dayLabels[day.getDay()], count, isToday: day.getTime() === today.getTime() };
  });
  const maxDayCount = Math.max(...weekData.map((d) => d.count), 1);

  // Agent team summary: core vs specialist
  const coreAgents = ["NASR", "QA Agent", "Scheduler"];
  const specialistAgents = ["NASR (Coder)", "NASR (Writer)", "NASR (Research)", "NASR (CV)", "OpenClaw"];
  const agentTaskCounts: Record<string, number> = {};
  activeTasks.forEach((t) => {
    if (isAgentAssignee(t.assignee) && t.assignee !== "Both") {
      agentTaskCounts[t.assignee] = (agentTaskCounts[t.assignee] || 0) + 1;
    }
  });

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

      {/* Content Pipeline Stats */}
      <div className="glass rounded-xl p-5">
        <h3 className="text-sm font-semibold mb-4 text-gray-300 flex items-center gap-2">
          <span><Icon name="pen" size={16}/></span> Content Pipeline
        </h3>
        {loadingPosts ? (
          <div className="text-xs text-gray-600 text-center py-2">Loading...</div>
        ) : (
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: "Total", value: totalPosts, color: "text-indigo-400" },
              { label: "Drafts", value: draftPosts, color: "text-yellow-400" },
              { label: "In Review", value: reviewPosts, color: "text-pink-400" },
              { label: "Published", value: publishedPosts, color: "text-green-400" },
            ].map(({ label, value, color }) => (
              <div key={label} className="text-center">
                <div className={`text-2xl font-bold ${color}`}>{value}</div>
                <div className="text-[10px] text-gray-500 mt-0.5">{label}</div>
              </div>
            ))}
          </div>
        )}
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

        {/* By Priority + Assignee */}
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

          {/* Fixed Assignee breakdown */}
          <div className="mt-6 pt-4 border-t border-white/5">
            <h4 className="text-xs font-semibold text-gray-400 mb-3">Active by Assignee</h4>
            <div className="flex gap-4">
              <div className="flex items-center gap-2" title="Ahmed">
                <span className="text-sm"><Icon name="user" size={16}/></span>
                <span className="text-xs text-blue-400">{byAssignee.Ahmed}</span>
                <span className="text-[10px] text-gray-600">Ahmed</span>
              </div>
              <div className="flex items-center gap-2" title="AI Agents (NASR/OpenClaw/QA)">
                <span className="text-sm">robot</span>
                <span className="text-xs text-purple-400">{byAssignee.Agents}</span>
                <span className="text-[10px] text-gray-600">Agents</span>
              </div>
              <div className="flex items-center gap-2" title="Both">
                <span className="text-sm"><Icon name="users" size={16}/></span>
                <span className="text-xs text-indigo-400">{byAssignee.Both}</span>
                <span className="text-[10px] text-gray-600">Both</span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity - clickable */}
        <div className="glass rounded-xl p-5">
          <h3 className="text-sm font-semibold mb-4 text-gray-300">Recent Activity</h3>
          <div className="space-y-2">
            {tasks
              .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
              .slice(0, 8)
              .map((task) => (
                <div
                  key={task.id}
                  className="flex items-center gap-2 py-1.5 border-b border-white/5 last:border-0 cursor-pointer hover:bg-white/5 rounded px-1 transition-colors"
                  onClick={() => {}}
                >
                  <span className="text-xs">
                    {task.status === "Completed" ? "check" :
                     task.status === "In Progress" ? "🔄" :
                     task.status === "OpenClaw Tasks" ? "robot" : "folder"}
                  </span>
                  <span className="flex-1 text-xs text-gray-400 truncate">{task.title}</span>
                  <span className={`text-[10px] ${
                    isAgentAssignee(task.assignee) ? "text-purple-500" : "text-blue-500"
                  }`}>
                    {isAgentAssignee(task.assignee) ? "robot" : "user"}
                  </span>
                </div>
              ))}
            {tasks.length === 0 && (
              <div className="text-gray-600 text-center py-6 text-xs">No tasks yet</div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Row: This Week Timeline + Agent Team Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* This Week Mini Timeline */}
        <div className="glass rounded-xl p-5">
          <h3 className="text-sm font-semibold mb-4 text-gray-300">This Week – Tasks Completed</h3>
          <div className="flex items-end gap-2 h-24">
            {weekData.map((day, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                <div className="flex-1 flex items-end w-full">
                  <div
                    className={`w-full rounded-t transition-all duration-500 ${
                      day.isToday ? "bg-indigo-500" : "bg-indigo-500/30"
                    }`}
                    style={{
                      height: `${day.count > 0 ? Math.max((day.count / maxDayCount) * 100, 8) : 4}%`,
                      minHeight: day.count > 0 ? "8px" : "2px",
                    }}
                    title={`${day.count} completed`}
                  />
                </div>
                <span className={`text-[9px] ${day.isToday ? "text-indigo-400 font-bold" : "text-gray-600"}`}>
                  {day.label}
                </span>
                {day.count > 0 && (
                  <span className="text-[9px] text-gray-500">{day.count}</span>
                )}
              </div>
            ))}
          </div>
          <div className="mt-2 text-[10px] text-gray-600 text-center">
            {weekData.reduce((a, d) => a + d.count, 0)} tasks completed this week
          </div>
        </div>

        {/* Agent Team Summary */}
        <div className="glass rounded-xl p-5">
          <h3 className="text-sm font-semibold mb-4 text-gray-300 flex items-center justify-between">
            <span>robot Agent Team</span>
            <span className="text-[10px] text-gray-600 font-normal">Active tasks</span>
          </h3>
          <div className="space-y-3">
            <div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Core – Always Running</div>
              <div className="space-y-1.5">
                {coreAgents.map((name) => {
                  const count = agentTaskCounts[name] || 0;
                  return (
                    <div key={name} className="flex items-center gap-2">
                      <span className="text-sm">{name === "NASR" ? "targetAgent" : name === "QA Agent" ? "shieldAgent" : "clockAgent"}</span>
                      <span className="text-xs text-gray-400 flex-1">{name}</span>
                      {count > 0 ? (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/15 text-indigo-400">{count}</span>
                      ) : (
                        <span className="text-[10px] text-gray-700">idle</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="pt-2 border-t border-white/5">
              <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Specialists – Per Task</div>
              <div className="space-y-1.5">
                {specialistAgents.map((name) => {
                  const count = agentTaskCounts[name] || 0;
                  const icons: Record<string, string> = {
                    "NASR (Coder)": "codeAgent",
                    "NASR (Writer)": "penAgent",
                    "NASR (Research)": "searchAgent",
                    "NASR (CV)": "documentAgent",
                    "OpenClaw": "robot",
                  };
                  return (
                    <div key={name} className="flex items-center gap-2">
                      <span className="text-sm">{icons[name] || "robot"}</span>
                      <span className="text-xs text-gray-400 flex-1">{name}</span>
                      {count > 0 ? (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/15 text-purple-400">{count}</span>
                      ) : (
                        <span className="text-[10px] text-gray-700">—</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
