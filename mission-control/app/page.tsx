"use client";

import { useState, useEffect, useCallback } from "react";
import { TaskBoard } from "@/components/TaskBoard";
import { ContentBoard } from "@/components/ContentBoard";
import { Dashboard } from "@/components/Dashboard";
import { TaskForm } from "@/components/TaskForm";
import { EditTaskForm } from "@/components/EditTaskForm";
import { NewContentForm } from "@/components/NewContentForm";
import { ContentEditor } from "@/components/ContentEditor";
import { Icon } from "@/components/Icon";
import { Logo } from "@/components/Logo";
import dynamic from "next/dynamic";

const CalendarPage = dynamic(() => import("@/app/calendar/page"), { ssr: false });
const MemoryPage = dynamic(() => import("@/app/memory/page"), { ssr: false });
const TeamBoard = dynamic(() => import("@/components/TeamBoard").then(m => ({ default: m.TeamBoard })), { ssr: false });
const CVHistoryPage = dynamic(() => import("@/components/CVHistory").then(m => ({ default: m.CVHistoryPage })), { ssr: false });

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

interface ContentPost {
  id: number;
  title: string;
  hook?: string;
  body?: string;
  platform: string;
  contentType: string;
  status: string;
  hashtags?: string;
  imageUrl?: string;
  publishDate?: string;
  assignee: string;
  priority: string;
  createdAt: string;
  updatedAt?: string;
}

type ActiveBoard = "tasks" | "content" | "calendar" | "memory" | "team" | "cv" | "dashboard";

export default function Home() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [posts, setPosts] = useState<ContentPost[]>([]);
  const [activeBoard, setActiveBoard] = useState<ActiveBoard>("dashboard");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [showContentForm, setShowContentForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [editingPost, setEditingPost] = useState<ContentPost | null>(null);
  const [search, setSearch] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchTasks = useCallback(async () => {
    try {
      const res = await fetch("/api/tasks");
      const data = await res.json();
      setTasks(data);
    } catch (error) {
      console.error("Failed to fetch tasks:", error);
    }
  }, []);

  const fetchPosts = useCallback(async () => {
    try {
      const res = await fetch("/api/content");
      const data = await res.json();
      setPosts(data);
    } catch (error) {
      console.error("Failed to fetch posts:", error);
    }
  }, []);

  useEffect(() => {
    fetchTasks();
    fetchPosts();
    const interval = setInterval(() => { fetchTasks(); fetchPosts(); }, 10000);
    return () => clearInterval(interval);
  }, [fetchTasks, fetchPosts]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([fetchTasks(), fetchPosts()]);
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const filteredTasks = tasks.filter((task) => {
    if (search && !task.title.toLowerCase().includes(search.toLowerCase()) &&
        !task.description?.toLowerCase().includes(search.toLowerCase())) return false;
    if (filterCategory && task.category !== filterCategory) return false;
    if (filterPriority && task.priority !== filterPriority) return false;
    return true;
  });

  const filteredPosts = posts.filter((post) => {
    if (search && !post.title.toLowerCase().includes(search.toLowerCase()) &&
        !post.hook?.toLowerCase().includes(search.toLowerCase())) return false;
    if (filterPriority && post.priority !== filterPriority) return false;
    return true;
  });

  const totalTasks = tasks.length;
  const inProgress = tasks.filter(t => t.status === "In Progress").length;
  const inReview = tasks.filter(t => t.status === "Review").length;
  const completed = tasks.filter(t => t.status === "Completed").length;
  const highPriority = tasks.filter(t => t.priority === "High" && t.status !== "Completed").length;

  const totalPosts = posts.length;
  const publishedPosts = posts.filter(p => p.status === "Published").length;
  const activePosts = totalPosts - publishedPosts;

  const boardTitles: Record<ActiveBoard, string> = {
    tasks: "Task Board",
    content: "Content Pipeline",
    calendar: "Calendar",
    memory: "Memory",
    team: "Agent Team",
    cv: "CV Maker",
    dashboard: "Dashboard",
  };

  const boardSubtitles: Record<ActiveBoard, string> = {
    tasks: `${totalTasks} tasks · ${highPriority} high priority · ${inReview} awaiting review`,
    content: `${totalPosts} posts · ${activePosts} active · ${publishedPosts} published`,
    calendar: "Scheduled tasks and proactive work",
    memory: "Your entire digital life",
    team: "Contacts, recruiters, and networking",
    cv: "Tailored CVs with ATS scoring",
    dashboard: `${totalTasks} tasks · ${highPriority} high priority · ${inReview} awaiting review`,
  };

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
            className={`sidebar-item ${activeBoard === "tasks" ? "active" : ""}`}
            onClick={() => setActiveBoard("tasks")}
          >
            <Icon name="board" className="text-gray-400" />
            <span>Task Board</span>
            <span className="ml-auto text-[10px] text-[var(--text-muted)]">{totalTasks - completed}</span>
          </div>
          <div
            className={`sidebar-item ${activeBoard === "content" ? "active" : ""}`}
            onClick={() => setActiveBoard("content")}
          >
            <Icon name="draft" className="text-gray-400" />
            <span>Content Pipeline</span>
            <span className="ml-auto text-[10px] text-[var(--text-muted)]">{activePosts}</span>
          </div>
          <div
            className={`sidebar-item ${activeBoard === "calendar" ? "active" : ""}`}
            onClick={() => setActiveBoard("calendar")}
          >
            <Icon name="calendar" className="text-gray-400" />
            <span>Calendar</span>
          </div>
          <div
            className={`sidebar-item ${activeBoard === "memory" ? "active" : ""}`}
            onClick={() => setActiveBoard("memory")}
          >
            <Icon name="memory" className="text-gray-400" />
            <span>Memory</span>
          </div>
          <div
            className={`sidebar-item ${activeBoard === "team" ? "active" : ""}`}
            onClick={() => setActiveBoard("team")}
          >
            <Icon name="users" className="text-gray-400" />
            <span>Agent Team</span>
          </div>
          <div
            className={`sidebar-item ${activeBoard === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveBoard("dashboard")}
          >
            <Icon name="dashboard" className="text-gray-400" />
            <span>Dashboard</span>
          </div>
          <div
            className={`sidebar-item ${activeBoard === "cv" ? "active" : ""}`}
            onClick={() => setActiveBoard("cv")}
          >
            <Icon name="fileText" className="text-gray-400" />
            <span>CV Maker</span>
          </div>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-label">Pipelines</div>
          <div className="sidebar-item">
            <Icon name="target" className="text-gray-400" />
            <span>Job Search</span>
            <span className="ml-auto text-[10px] text-[var(--text-muted)]">
              {tasks.filter(t => t.category === "Job Search" && t.status !== "Completed").length}
            </span>
          </div>
          <div className="sidebar-item" onClick={() => setActiveBoard("content")}>
            <Icon name="pen" className="text-gray-400" />
            <span>Content</span>
            <span className="ml-auto text-[10px] text-[var(--text-muted)]">{activePosts}</span>
          </div>
          <div className="sidebar-item">
            <Icon name="users" className="text-gray-400" />
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
              <span className="text-[var(--text-muted)]">Active Tasks</span>
              <span className="text-white font-medium">{totalTasks - completed}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-muted)]">Content Posts</span>
              <span className="text-[var(--pink)] font-medium">{activePosts}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-muted)]">Published</span>
              <span className="text-[var(--success)] font-medium">{publishedPosts}</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Header - hidden for team view (TeamBoard has its own) */}
        {activeBoard !== "team" && (
          <div className="page-header">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="page-title">{boardTitles[activeBoard]}</h1>
                <p className="page-subtitle">{boardSubtitles[activeBoard]}</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[var(--success)] pulse-slow"></div>
                <span className="text-[11px] text-[var(--text-muted)]">Live</span>
              </div>
            </div>
          </div>
        )}

        {/* Header - hidden for team and memory views (they have their own) */}
        {activeBoard !== "team" && activeBoard !== "memory" && activeBoard !== "cv" && (
          <div className="page-header">
            {activeBoard !== "calendar" && (
              <input
                type="text"
                placeholder={activeBoard === "content" ? "Search posts..." : "Search tasks..."}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="toolbar-search"
              />
            )}

            {activeBoard === "tasks" && (
              <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)} className="toolbar-btn bg-transparent">
                <option value="">All Categories</option>
                <option value="Job Search">Job Search</option>
                <option value="Content">Content</option>
                <option value="Networking">Networking</option>
                <option value="Applications">Applications</option>
                <option value="Interviews">Interviews</option>
                <option value="Task">Task</option>
              </select>
            )}

            {activeBoard !== "calendar" && (
              <select value={filterPriority} onChange={(e) => setFilterPriority(e.target.value)} className="toolbar-btn bg-transparent">
                <option value="">All Priorities</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            )}

            <div className="flex-1" />

            {activeBoard !== "calendar" && (
              <button onClick={handleRefresh} className={`toolbar-btn ${isRefreshing ? "animate-spin" : ""}`}><Icon name="refresh" /></button>
            )}

            {activeBoard === "tasks" && (
              <button onClick={() => setShowForm(true)} className="toolbar-btn toolbar-btn-primary">+ New Task</button>
            )}
            {activeBoard === "content" && (
              <button onClick={() => setShowContentForm(true)} className="toolbar-btn toolbar-btn-primary">+ New Post</button>
            )}
          </div>
        )}

        {/* Stats */}
        {activeBoard === "tasks" && (
          <div className="stats-bar grid-cols-2 md:grid-cols-4">
            <div className="stat-card stat-card-purple"><div className="stat-number">{totalTasks}</div><div className="stat-label">Total Tasks</div></div>
            <div className="stat-card stat-card-yellow"><div className="stat-number">{inProgress}</div><div className="stat-label">In Progress</div></div>
            <div className="stat-card stat-card-red"><div className="stat-number">{highPriority}</div><div className="stat-label">High Priority</div></div>
            <div className="stat-card stat-card-green"><div className="stat-number">{completed}</div><div className="stat-label">Completed</div></div>
          </div>
        )}
        {activeBoard === "content" && (
          <div className="stats-bar grid-cols-2 md:grid-cols-4">
            <div className="stat-card stat-card-purple"><div className="stat-number">{totalPosts}</div><div className="stat-label">Total Posts</div></div>
            <div className="stat-card stat-card-yellow"><div className="stat-number">{posts.filter(p => p.status === "Draft").length}</div><div className="stat-label">Drafts</div></div>
            <div className="stat-card stat-card-red"><div className="stat-number">{posts.filter(p => p.status === "Review").length}</div><div className="stat-label">In Review</div></div>
            <div className="stat-card stat-card-green"><div className="stat-number">{publishedPosts}</div><div className="stat-label">Published</div></div>
          </div>
        )}

        {/* Content */}
        <div className="board-container">
          {activeBoard === "tasks" && (
            <TaskBoard tasks={filteredTasks} onRefresh={fetchTasks} onEditTask={setEditingTask} />
          )}
          {activeBoard === "content" && (
            <ContentBoard posts={filteredPosts} onRefresh={fetchPosts} onEditPost={setEditingPost} />
          )}
          {activeBoard === "calendar" && (
            <CalendarPage />
          )}
          {activeBoard === "memory" && (
            <MemoryPage />
          )}
          {activeBoard === "team" && (
            <TeamBoard />
          )}
          {activeBoard === "cv" && (
            <CVHistoryPage />
          )}
          {activeBoard === "dashboard" && (
            <Dashboard tasks={tasks} />
          )}
        </div>

        {/* Modals */}
        {showForm && <TaskForm onClose={() => setShowForm(false)} onTaskAdded={fetchTasks} />}
        {editingTask && <EditTaskForm task={editingTask} onClose={() => setEditingTask(null)} onTaskUpdated={fetchTasks} />}
        {showContentForm && <NewContentForm onClose={() => setShowContentForm(false)} onPostAdded={fetchPosts} />}
        {editingPost && <ContentEditor post={editingPost} onClose={() => setEditingPost(null)} onPostUpdated={fetchPosts} />}
      </main>
    </div>
  );
}
