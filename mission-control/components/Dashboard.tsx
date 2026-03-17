"use client";

import { useState, useEffect } from "react";
import { Icon } from "./Icon";

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
  return upper.includes("NASR") || upper.includes("OPENCLAW") || upper === "QA AGENT" || upper.includes("QA");
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return mins + "m ago";
  const hours = Math.floor(mins / 60);
  if (hours < 24) return hours + "h ago";
  const days = Math.floor(hours / 24);
  return days + "d ago";
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

  const activeTasks = tasks.filter((t) => t.status !== "Completed");
  const completionRate = tasks.length > 0 ? Math.round((tasks.filter(t => t.status === "Completed").length / tasks.length) * 100) : 0;

  // Content pipeline stats
  const totalPosts = posts.length;
  const publishedPosts = posts.filter((p) => p.status === "Published").length;
  const draftPosts = posts.filter((p) => p.status === "Draft").length;
  const reviewPosts = posts.filter((p) => p.status === "Review").length;

  // This week timeline
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

  // Agent team summary
  const coreAgents = ["NASR", "QA Agent", "Scheduler"];
  const specialistAgents = ["NASR (Coder)", "NASR (Writer)", "NASR (Research)", "NASR (CV)", "OpenClaw"];
  const agentTaskCounts: Record<string, number> = {};
  activeTasks.forEach((t) => {
    if (isAgentAssignee(t.assignee) && t.assignee !== "Both") {
      agentTaskCounts[t.assignee] = (agentTaskCounts[t.assignee] || 0) + 1;
    }
  });

  // Upcoming deadlines (next 7 days)
  const upcomingDeadlines = tasks
    .filter((t) => t.dueDate && t.status !== "Completed")
    .sort((a, b) => new Date(a.dueDate!).getTime() - new Date(b.dueDate!).getTime())
    .slice(0, 5);

  // Recent CVs (from history)
  const recentCvs = tasks
    .filter((t) => t.category === "Applications" && t.title.includes("CV"))
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, 3);

  // Job search stats
  const jobSearchTasks = tasks.filter((t) => t.category === "Job Search");
  const applicationTasks = tasks.filter((t) => t.category === "Applications");
  const interviewTasks = tasks.filter((t) => t.category === "Interviews");

  return (
    <div className="space-y-6">
      
      {/* Quick Actions */}
      <div className="glass rounded-xl p-4">
        <h3 className="text-xs font-semibold text-gray-400 mb-3 uppercase tracking-wider">Quick Actions</h3>
        <div className="flex flex-wrap gap-2">
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[rgba(124,92,252,0.15)] border border-indigo-500/30 text-indigo-400 hover:bg-[rgba(124,92,252,0.25)] transition-all text-xs font-medium">
            <span>📄</span> Create CV
          </button>
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[rgba(124,92,252,0.15)] border border-indigo-500/30 text-indigo-400 hover:bg-[rgba(124,92,252,0.25)] transition-all text-xs font-medium">
            <span>✍️</span> New Content
          </button>
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[rgba(124,92,252,0.15)] border border-indigo-500/30 text-indigo-400 hover:bg-[rgba(124,92,252,0.25)] transition-all text-xs font-medium">
            <span>📋</span> Add Task
          </button>
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[rgba(124,92,252,0.15)] border border-indigo-500/30 text-indigo-400 hover:bg-[rgba(124,92,252,0.25)] transition-all text-xs font-medium">
            <span>🔍</span> Job Search
          </button>
        </div>
      </div>

      {/* Quick Stats Row */}
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
        </div>

        <div className="stat-card stat-card-purple glass rounded-xl p-5">
          <div className="text-3xl font-bold text-purple-400">{publishedPosts}</div>
          <div className="text-xs text-gray-400 mt-1">Content Published</div>
        </div>
      </div>

      {/* Job Search Stats */}
      <div className="glass rounded-xl p-5">
        <h3 className="text-xs font-semibold text-gray-400 mb-4 uppercase tracking-wider">Job Search Overview</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.05)]">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">🎯</span>
              <span className="text-xs text-gray-500">Active Searches</span>
            </div>
            <div className="text-2xl font-bold text-white">{jobSearchTasks.length}</div>
          </div>
          <div className="p-4 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.05)]">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">📨</span>
              <span className="text-xs text-gray-500">Applications</span>
            </div>
            <div className="text-2xl font-bold text-white">{applicationTasks.length}</div>
          </div>
          <div className="p-4 rounded-lg bg-[rgba(255,255,255,0)] border border-[rgba(255,255,255,0.05]}">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">🎤</span>
              <span className="text-xs text-gray-500">Interviews</span>
            </div>
            <div className="text-2xl font-bold text-white">{interviewTasks.length}</div>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        
        {/* Upcoming Deadlines */}
        <div className="glass rounded-xl p-5">
          <h3 className="text-xs font-semibold text-gray-400 mb-4 uppercase tracking-wider flex items-center gap-2">
            <span>⏰</span> Upcoming Deadlines
          </h3>
          <div className="space-y-2">
            {upcomingDeadlines.map((task) => {
              const dueDate = new Date(task.dueDate!);
              const daysLeft = Math.ceil((dueDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
              const isUrgent = daysLeft <= 2;
              
              return (
                <div key={task.id} className="flex items-center gap-3 p-3 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.04)] hover:border-indigo-500/20 transition-all">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg ${isUrgent ? "bg-red-500/20" : "bg-indigo-500/20"}`}>
                    {isUrgent ? "🚨" : "📋"}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-white truncate">{task.title}</div>
                    <div className={`text-[10px] ${isUrgent ? "text-red-400" : "text-gray-500"}`}>
                      {daysLeft === 0 ? "Due today" : daysLeft === 1 ? "Due tomorrow" : `${daysLeft} days left`}
                    </div>
                  </div>
                  <span className={`text-[10px] px-2 py-1 rounded ${isUrgent ? "bg-red-500/20 text-red-400" : "bg-gray-700 text-gray-400"}`}>
                    {task.priority}
                  </span>
                </div>
              );
            })}
            {upcomingDeadlines.length === 0 && (
              <div className="text-center py-6 text-gray-500 text-xs">
                <span className="text-2xl mb-2 block">✅</span>
                No upcoming deadlines
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="glass rounded-xl p-5">
          <h3 className="text-xs font-semibold text-gray-400 mb-4 uppercase tracking-wider flex items-center gap-2">
            <span>📋</span> Recent Activity
          </h3>
          <div className="space-y-2">
            {tasks
              .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
              .slice(0, 6)
              .map((task) => (
                <div key={task.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-[rgba(255,255,255,0.02)] transition-all cursor-pointer">
                  <span className="text-sm">
                    {task.status === "Completed" ? "✅" :
                     task.status === "In Progress" ? "🔄" :
                     task.status === "OpenClaw Tasks" ? "🤖" : "📁"}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-white truncate">{task.title}</div>
                    <div className="text-[10px] text-gray-600">{timeAgo(task.createdAt)}</div>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded ${isAgentAssignee(task.assignee) ? "bg-purple-500/20 text-purple-400" : "bg-blue-500/20 text-blue-400"}`}>
                    {isAgentAssignee(task.assignee) ? "🤖" : "👤"}
                  </span>
                </div>
              ))}
            {tasks.length === 0 && (
              <div className="text-center py-6 text-gray-500 text-xs">
                No activity yet
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        
        {/* This Week Timeline */}
        <div className="glass rounded-xl p-5">
          <h3 className="text-xs font-semibold text-gray-400 mb-4 uppercase tracking-wider">This Week – Tasks Completed</h3>
          <div className="flex items-end gap-2 h-24">
            {weekData.map((day, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                <div className="flex-1 flex items-end w-full">
                  <div
                    className={`w-full rounded-t transition-all duration-500 ${day.isToday ? "bg-indigo-500" : "bg-indigo-500/30"}`}
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
                {day.count > 0 && <span className="text-[9px] text-gray-500">{day.count}</span>}
              </div>
            ))}
          </div>
          <div className="mt-2 text-[10px] text-gray-600 text-center">
            {weekData.reduce((a, d) => a + d.count, 0)} tasks completed this week
          </div>
        </div>

        {/* Favorite Links */}
        <div className="glass rounded-xl p-5">
          <h3 className="text-xs font-semibold text-gray-400 mb-4 uppercase tracking-wider flex items-center gap-2">
            <span>⭐</span> Quick Links
          </h3>
          <div className="grid grid-cols-2 gap-2">
            <a href="https://www.linkedin.com" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 p-3 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.05)] hover:border-indigo-500/30 transition-all">
              <span className="text-lg">💼</span>
              <span className="text-xs text-white">LinkedIn</span>
            </a>
            <a href="https://jobs.lever.co" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 p-3 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.05)] hover:border-indigo-500/30 transition-all">
              <span className="text-lg">🚪</span>
              <span className="text-xs text-white">Lever</span>
            </a>
            <a href="https://jobs.ashbyhq.com" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 p-3 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.05)] hover:border-indigo-500/30 transition-all">
              <span className="text-lg">🎯</span>
              <span className="text-xs text-white">Ashby</span>
            </a>
            <a href="https://greenhouse.io" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 p-3 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.05)] hover:border-indigo-500/30 transition-all">
              <span className="text-lg">🌿</span>
              <span className="text-xs text-white">Greenhouse</span>
            </a>
            <a href="https://workday.com" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 p-3 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.05)] hover:border-indigo-500/30 transition-all">
              <span className="text-lg">💼</span>
              <span className="text-xs text-white">Workday</span>
            </a>
            <a href="https://indeed.com" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 p-3 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.05)] hover:border-indigo-500/30 transition-all">
              <span className="text-lg">✅</span>
              <span className="text-xs text-white">Indeed</span>
            </a>
          </div>
        </div>
      </div>

      {/* Category & Priority Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass rounded-xl p-5">
          <h3 className="text-xs font-semibold text-gray-400 mb-4 uppercase tracking-wider">By Category</h3>
          <div className="space-y-3">
            {Object.entries(byCategory).map(([cat, data]) => (
              <div key={cat} className="flex items-center gap-3">
                <span className="text-sm">{data.icon === "targetAgent" ? "🎯" : data.icon === "pen" ? "✍️" : data.icon === "handshake" ? "🤝" : data.icon === "folder" ? "📁" : data.icon === "mic" ? "🎤" : "📌"}</span>
                <span className="flex-1 text-xs text-gray-400">{cat}</span>
                <span className="text-xs font-medium text-white">{data.count}</span>
                <div className="w-16 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                  <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${tasks.length > 0 ? (data.count / tasks.length) * 100 : 0}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="glass rounded-xl p-5">
          <h3 className="text-xs font-semibold text-gray-400 mb-4 uppercase tracking-wider">By Priority</h3>
          <div className="space-y-3">
            {Object.entries(byPriority).map(([pri, data]) => (
              <div key={pri} className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${data.bg}`} />
                <span className="flex-1 text-xs text-gray-400">{pri}</span>
                <span className="text-xs font-medium text-white">{data.count}</span>
                <div className="w-16 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${tasks.length > 0 ? (data.count / tasks.length) * 100 : 0}%`, backgroundColor: pri === "High" ? "#ef4444" : pri === "Medium" ? "#eab308" : "#22c55e" }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Agent Team Summary */}
      <div className="glass rounded-xl p-5">
        <h3 className="text-xs font-semibold text-gray-400 mb-4 uppercase tracking-wider flex items-center gap-2">
          <span>🤖</span> Agent Team – Active Tasks
        </h3>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-3">Core – Always Running</div>
            <div className="space-y-2">
              {coreAgents.map((name) => {
                const count = agentTaskCounts[name] || 0;
                const icons: Record<string, string> = { "NASR": "🎯", "QA Agent": "✅", "Scheduler": "⏰" };
                return (
                  <div key={name} className="flex items-center gap-2">
                    <span className="text-sm">{icons[name] || "🤖"}</span>
                    <span className="text-xs text-gray-400 flex-1">{name}</span>
                    {count > 0 ? (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400">{count}</span>
                    ) : <span className="text-[10px] text-gray-600">idle</span>}
                  </div>
                );
              })}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-3">Specialists – Per Task</div>
            <div className="space-y-2">
              {specialistAgents.map((name) => {
                const count = agentTaskCounts[name] || 0;
                const icons: Record<string, string> = { "NASR (Coder)": "{ }", "NASR (Writer)": "✎", "NASR (Research)": "🔍", "NASR (CV)": "📄", "OpenClaw": "🦞" };
                return (
                  <div key={name} className="flex items-center gap-2">
                    <span className="text-sm font-mono">{icons[name] || "🤖"}</span>
                    <span className="text-xs text-gray-400 flex-1">{name}</span>
                    {count > 0 ? (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/20 text-purple-400">{count}</span>
                    ) : <span className="text-[10px] text-gray-600">—</span>}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
