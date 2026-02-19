"use client";

import { useState, useEffect, useCallback } from "react";
import { TaskBoard } from "@/components/TaskBoard";
import { Dashboard } from "@/components/Dashboard";
import { TaskForm } from "@/components/TaskForm";
import { EditTaskForm } from "@/components/EditTaskForm";

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
}

export default function Home() {
  const [view, setView] = useState<"board" | "dashboard">("board");
  const [showForm, setShowForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [search, setSearch] = useState("");
  const [filterCategory, setFilterCategory] = useState("all");
  const [filterPriority, setFilterPriority] = useState("all");
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadTasks = useCallback(async () => {
    try {
      const res = await fetch("/api/tasks");
      const data = await res.json();
      setTasks(data);
    } catch (error) {
      console.error("Error loading tasks:", error);
    }
  }, []);

  useEffect(() => {
    loadTasks();
    const interval = setInterval(loadTasks, 10000);
    return () => clearInterval(interval);
  }, [loadTasks]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadTasks();
    setTimeout(() => setIsRefreshing(false), 600);
  };

  const handleTaskAdded = () => {
    loadTasks();
  };

  const handleEditTask = (task: Task) => {
    setEditingTask(task);
  };

  // Filter tasks
  const filteredTasks = tasks.filter((task) => {
    const matchesSearch = search === "" || 
      task.title.toLowerCase().includes(search.toLowerCase()) ||
      (task.description || "").toLowerCase().includes(search.toLowerCase());
    const matchesCategory = filterCategory === "all" || task.category === filterCategory;
    const matchesPriority = filterPriority === "all" || task.priority === filterPriority;
    return matchesSearch && matchesCategory && matchesPriority;
  });

  // Stats
  const totalTasks = tasks.length;
  const completedTasks = tasks.filter(t => t.status === "Completed").length;
  const inProgressTasks = tasks.filter(t => t.status === "In Progress").length;
  const highPriorityTasks = tasks.filter(t => t.priority === "High" && t.status !== "Completed").length;

  return (
    <main className="min-h-screen text-white">
      {/* Background gradient */}
      <div className="fixed inset-0 bg-[#050510]">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-950/20 via-transparent to-purple-950/20" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-600/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-600/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 p-4 md:p-6 max-w-[1600px] mx-auto">
        {/* Header */}
        <header className="mb-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-xl">
                🎯
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                  Mission Control
                </h1>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 pulse-dot" />
                  <span>Live</span>
                  <span>-</span>
                  <span>{totalTasks} tasks</span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-2 flex-wrap">
              <button
                onClick={handleRefresh}
                className={`px-3 py-2 glass rounded-lg hover:bg-white/5 transition-all ${isRefreshing ? 'animate-spin' : ''}`}
                title="Refresh"
              >
                🔄
              </button>
              <button
                onClick={() => setView("board")}
                className={`px-4 py-2 rounded-lg transition-all ${
                  view === "board" ? "btn-primary" : "glass hover:bg-white/5"
                }`}
              >
                📋 Board
              </button>
              <button
                onClick={() => setView("dashboard")}
                className={`px-4 py-2 rounded-lg transition-all ${
                  view === "dashboard" ? "btn-primary" : "glass hover:bg-white/5"
                }`}
              >
                📊 Dashboard
              </button>
              <button
                onClick={() => setShowForm(true)}
                className="btn-success text-white"
              >
                + New Task
              </button>
            </div>
          </div>

          {/* Quick Stats Bar */}
          <div className="grid grid-cols-4 gap-3 mb-4">
            <div className="glass rounded-lg px-4 py-3 flex items-center gap-3">
              <span className="text-2xl font-bold text-indigo-400">{totalTasks}</span>
              <span className="text-xs text-gray-400">Total</span>
            </div>
            <div className="glass rounded-lg px-4 py-3 flex items-center gap-3">
              <span className="text-2xl font-bold text-yellow-400">{inProgressTasks}</span>
              <span className="text-xs text-gray-400">In Progress</span>
            </div>
            <div className="glass rounded-lg px-4 py-3 flex items-center gap-3">
              <span className="text-2xl font-bold text-green-400">{completedTasks}</span>
              <span className="text-xs text-gray-400">Completed</span>
            </div>
            <div className="glass rounded-lg px-4 py-3 flex items-center gap-3">
              <span className="text-2xl font-bold text-red-400">{highPriorityTasks}</span>
              <span className="text-xs text-gray-400">High Priority</span>
            </div>
          </div>

          {/* Search & Filters */}
          <div className="flex flex-col md:flex-row gap-3">
            <div className="flex-1 relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">🔍</span>
              <input
                type="text"
                placeholder="Search tasks..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full search-input rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-gray-500"
              />
              {search && (
                <button 
                  onClick={() => setSearch("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                >
                  ✕
                </button>
              )}
            </div>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="glass rounded-lg px-3 py-2.5 text-sm text-white bg-transparent"
            >
              <option value="all" className="bg-gray-900">All Categories</option>
              <option value="Job Search" className="bg-gray-900">🎯 Job Search</option>
              <option value="Content" className="bg-gray-900">📝 Content</option>
              <option value="Networking" className="bg-gray-900">🤝 Networking</option>
              <option value="Applications" className="bg-gray-900">📋 Applications</option>
              <option value="Interviews" className="bg-gray-900">🎤 Interviews</option>
              <option value="Task" className="bg-gray-900">📌 Task</option>
            </select>
            <select
              value={filterPriority}
              onChange={(e) => setFilterPriority(e.target.value)}
              className="glass rounded-lg px-3 py-2.5 text-sm text-white bg-transparent"
            >
              <option value="all" className="bg-gray-900">All Priorities</option>
              <option value="High" className="bg-gray-900">🔴 High</option>
              <option value="Medium" className="bg-gray-900">🟡 Medium</option>
              <option value="Low" className="bg-gray-900">🟢 Low</option>
            </select>
          </div>
        </header>

        {/* Main Content */}
        {view === "board" ? (
          <TaskBoard 
            tasks={filteredTasks} 
            onRefresh={loadTasks} 
            onEditTask={handleEditTask}
          />
        ) : (
          <Dashboard tasks={filteredTasks} />
        )}

        {/* Task Form Modal */}
        {showForm && (
          <TaskForm 
            onClose={() => setShowForm(false)} 
            onTaskAdded={handleTaskAdded} 
          />
        )}

        {/* Edit Task Modal */}
        {editingTask && (
          <EditTaskForm 
            task={editingTask}
            onClose={() => setEditingTask(null)} 
            onTaskUpdated={loadTasks} 
          />
        )}
      </div>
    </main>
  );
}
