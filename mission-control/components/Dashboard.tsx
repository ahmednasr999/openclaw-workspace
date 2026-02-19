"use client";

import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";

export function Dashboard() {
  const tasks = useQuery(api.tasks.getTasks);

  if (tasks === undefined) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading dashboard...</div>
      </div>
    );
  }

  // Calculate stats
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

  const byCategory = {
    "Job Search": tasks.filter((t) => t.category === "Job Search").length,
    Content: tasks.filter((t) => t.category === "Content").length,
    Networking: tasks.filter((t) => t.category === "Networking").length,
    Applications: tasks.filter((t) => t.category === "Applications").length,
    Interviews: tasks.filter((t) => t.category === "Interviews").length,
  };

  const byPriority = {
    High: tasks.filter((t) => t.priority === "High").length,
    Medium: tasks.filter((t) => t.priority === "Medium").length,
    Low: tasks.filter((t) => t.priority === "Low").length,
  };

  return (
    <div className="space-y-8">
      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-green-900/50 to-green-800/30 rounded-xl p-6">
          <div className="text-4xl font-bold text-green-400">{completedThisWeek}</div>
          <div className="text-sm text-gray-400 mt-1">Completed This Week</div>
        </div>
        
        <div className="bg-gradient-to-br from-yellow-900/50 to-yellow-800/30 rounded-xl p-6">
          <div className="text-4xl font-bold text-yellow-400">{inProgress}</div>
          <div className="text-sm text-gray-400 mt-1">In Progress</div>
        </div>
        
        <div className="bg-gradient-to-br from-red-900/50 to-red-800/30 rounded-xl p-6">
          <div className="text-4xl font-bold text-red-400">{overdue}</div>
          <div className="text-sm text-gray-400 mt-1">Overdue</div>
        </div>
        
        <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 rounded-xl p-6">
          <div className="text-4xl font-bold text-blue-400">{tasks.length}</div>
          <div className="text-sm text-gray-400 mt-1">Total Tasks</div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-2 gap-6">
        {/* By Category */}
        <div className="bg-gray-900/50 rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4">Tasks by Category</h3>
          <div className="space-y-3">
            {Object.entries(byCategory).map(([category, count]) => (
              <div key={category} className="flex items-center gap-3">
                <span className="text-xl">{["🎯", "📝", "🤝", "📋", "🎤"][
                  ["Job Search", "Content", "Networking", "Applications", "Interviews"].indexOf(category)
                ]}</span>
                <div className="flex-1">
                  <div className="flex justify-between text-sm mb-1">
                    <span>{category}</span>
                    <span className="text-gray-400">{count}</span>
                  </div>
                  <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${tasks.length > 0 ? (count / tasks.length) * 100 : 0}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* By Priority */}
        <div className="bg-gray-900/50 rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4">Tasks by Priority</h3>
          <div className="space-y-3">
            {Object.entries(byPriority).map(([priority, count]) => (
              <div key={priority} className="flex items-center gap-3">
                <span className="text-xl">{["🔴", "🟡", "🟢"][
                  ["High", "Medium", "Low"].indexOf(priority)
                ]}</span>
                <div className="flex-1">
                  <div className="flex justify-between text-sm mb-1">
                    <span>{priority}</span>
                    <span className="text-gray-400">{count}</span>
                  </div>
                  <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        priority === "High" ? "bg-red-500" : priority === "Medium" ? "bg-yellow-500" : "bg-green-500"
                      }`}
                      style={{ width: `${tasks.length > 0 ? (count / tasks.length) * 100 : 0}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-gray-900/50 rounded-xl p-6">
        <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
        <div className="space-y-2">
          {tasks.slice(0, 5).map((task) => (
            <div key={task._id} className="flex items-center gap-3 py-2 border-b border-gray-800 last:border-0">
              <span className={
                task.status === "Completed" ? "text-green-400" :
                task.status === "In Progress" ? "text-yellow-400" : "text-gray-400"
              }>
                {task.status === "Completed" ? "✅" :
                 task.status === "In Progress" ? "🔄" :
                 task.status === "OpenClaw Tasks" ? "🤖" : "📋"}
              </span>
              <span className="flex-1">{task.title}</span>
              <span className="text-sm text-gray-500">{task.assignee}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
