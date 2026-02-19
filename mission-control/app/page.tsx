"use client";

import { useState, useEffect, useCallback } from "react";
import { TaskBoard } from "@/components/TaskBoard";
import { Dashboard } from "@/components/Dashboard";
import { TaskForm } from "@/components/TaskForm";
import { EditTaskForm } from "@/components/EditTaskForm";
import { Logo } from "@/components/Logo";

interface Task {
  id: number;
  title: string;
  description?: string;
  assignee: string;
  priority: string;
  category: string;
  status: string;
  dueDate?: string;
  completedDate?: string;
  createdAt: string;
  subtaskCount?: number;
  subtaskDone?: number;
}

export default function Home() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [view, setView] = useState<"board" | "dashboard">("board");
  const [showForm, setShowForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [search, setSearch] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [sidebarPage, setSidebarPage] = useState("tasks");

  const fetchTasks = useCallback(async () => {
    try {
      const res = await fetch("/api/tasks");
      const data = await res.json();
      setTasks(data);
    } catch (error) {
      console.error("Failed to fetch tasks:", error);
    }
  }, []);

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 10000);
    return () => clearInterval(interval);
  }, [fetchTasks]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchTasks();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const filteredTasks = tasks.filter((task) => {
    if (search && !task.title.toLowerCase().includes(search.toLowerCase()) &&
        !task.description?.toLowerCase().includes(search.toLowerCase())) return false;
    if (filterCategory && task.category !== filterCategory) return false;
    if (filterPriority && task.priority !== filterPriority) return false;
    return true;
  });

  const totalTasks = tasks.length;
  const inProgress = tasks.filter(t => t.status === "In Progress").length;
  const inReview = tasks.filter(t => t.status === "Review").length;
  const completed = tasks.filter(t => t.status === "Completed").length;
  const highPriority = tasks.filter(t => t.priority === "High" && t.status !== "Completed").length;

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="flex items-center gap-3 logo-container cursor-pointer">
            <Logo size={34} />
            <div>
              <div className="text-[13px] font-semibold text-white tracking-tight">Mission Control</div>
              <div className="text-[10px] text-[var(--text-muted)] tracking-wide">COMMAND CENTER</div>
            </div>
          </div>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-label">Workspace</div>
          <div
            className={`sidebar-item ${sidebarPage === "tasks" ? "active" : ""}`}
            onClick={() => { setSidebarPage("tasks"); setView("board"); }}
          >
            <span className="icon">📋</span>
            <span>Task Board</span>
          </div>
          <div
            className={`sidebar-item ${sidebarPage === "dashboard" ? "active" : ""}`}
            onClick={() => { setSidebarPage("dashboard"); setView("dashboard"); }}
          >
            <span className="icon">📊</span>
            <span>Dashboard</span>
          </div>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-label">Pipelines</div>
          <div className="sidebar-item">
            <span className="icon">🎯</span>
            <span>Job Search</span>
            <span className="ml-auto text-[10px] text-[var(--text-muted)]">
              {tasks.filter(t => t.category === "Job Search" && t.status !== "Completed").length}
            </span>
          </div>
          <div className="sidebar-item">
            <span className="icon">📝</span>
            <span>Content</span>
            <span className="ml-auto text-[10px] text-[var(--text-muted)]">
              {tasks.filter(t => t.category === "Content" && t.status !== "Completed").length}
            </span>
          </div>
          <div className="sidebar-item">
            <span className="icon">🤝</span>
            <span>Networking</span>
            <span className="ml-auto text-[10px] text-[var(--text-muted)]">
              {tasks.filter(t => t.category === "Networking" && t.status !== "Completed").length}
            </span>
          </div>
        </div>

        <div className="sidebar-section mt-auto">
          <div className="sidebar-label">Quick Stats</div>
          <div className="px-3 space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-muted)]">Active</span>
              <span className="text-white font-medium">{totalTasks - completed}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-muted)]">In Review</span>
              <span className="text-[var(--pink)] font-medium">{inReview}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-muted)]">Completed</span>
              <span className="text-[var(--success)] font-medium">{completed}</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Header */}
        <div className="page-header">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="page-title">
                {view === "board" ? "Task Board" : "Dashboard"}
              </h1>
              <p className="page-subtitle">
                {totalTasks} tasks - {highPriority} high priority - {inReview} awaiting review
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[var(--success)] pulse-slow"></div>
              <span className="text-[11px] text-[var(--text-muted)]">Live</span>
            </div>
          </div>
        </div>

        {/* Toolbar */}
        <div className="toolbar">
          <input
            type="text"
            placeholder="Search tasks..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="toolbar-search"
          />
          
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="toolbar-btn bg-transparent"
          >
            <option value="">All Categories</option>
            <option value="Job Search">Job Search</option>
            <option value="Content">Content</option>
            <option value="Networking">Networking</option>
            <option value="Applications">Applications</option>
            <option value="Interviews">Interviews</option>
            <option value="Task">Task</option>
          </select>

          <select
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value)}
            className="toolbar-btn bg-transparent"
          >
            <option value="">All Priorities</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>

          <div className="flex-1" />

          <div className="view-toggle">
            <button
              onClick={() => { setView("board"); setSidebarPage("tasks"); }}
              className={view === "board" ? "active" : ""}
            >
              Board
            </button>
            <button
              onClick={() => { setView("dashboard"); setSidebarPage("dashboard"); }}
              className={view === "dashboard" ? "active" : ""}
            >
              Dashboard
            </button>
          </div>

          <button onClick={handleRefresh} className={`toolbar-btn ${isRefreshing ? "animate-spin" : ""}`}>
            🔄
          </button>

          <button onClick={() => setShowForm(true)} className="toolbar-btn toolbar-btn-primary">
            + New Task
          </button>
        </div>

        {/* Stats */}
        <div className="stats-bar grid-cols-2 md:grid-cols-4">
          <div className="stat-card stat-card-purple">
            <div className="stat-number">{totalTasks}</div>
            <div className="stat-label">Total Tasks</div>
          </div>
          <div className="stat-card stat-card-yellow">
            <div className="stat-number">{inProgress}</div>
            <div className="stat-label">In Progress</div>
          </div>
          <div className="stat-card stat-card-red">
            <div className="stat-number">{highPriority}</div>
            <div className="stat-label">High Priority</div>
          </div>
          <div className="stat-card stat-card-green">
            <div className="stat-number">{completed}</div>
            <div className="stat-label">Completed</div>
          </div>
        </div>

        {/* Content */}
        <div className="board-container">
          {view === "board" ? (
            <TaskBoard
              tasks={filteredTasks}
              onRefresh={fetchTasks}
              onEditTask={setEditingTask}
            />
          ) : (
            <Dashboard tasks={tasks} />
          )}
        </div>

        {/* Modals */}
        {showForm && (
          <TaskForm onClose={() => setShowForm(false)} onTaskAdded={fetchTasks} />
        )}
        {editingTask && (
          <EditTaskForm
            task={editingTask}
            onClose={() => setEditingTask(null)}
            onTaskUpdated={fetchTasks}
          />
        )}
      </main>
    </div>
  );
}
