"use client";

import { useState, useEffect } from "react";

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

interface Activity {
  id: number;
  taskId: number;
  type: string;
  content: string;
  author: string;
  createdAt: string;
}

interface Subtask {
  id: number;
  taskId: number;
  title: string;
  completed: number;
  createdAt: string;
}

interface EditTaskFormProps {
  task: Task;
  onClose: () => void;
  onTaskUpdated: () => void;
}

export function EditTaskForm({ task, onClose, onTaskUpdated }: EditTaskFormProps) {
  const [form, setForm] = useState({
    title: task.title,
    description: task.description || "",
    assignee: task.assignee,
    priority: task.priority,
    category: task.category,
    status: task.status,
    dueDate: task.dueDate || "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [tab, setTab] = useState<"details" | "subtasks" | "activity">("details");
  const [activity, setActivity] = useState<Activity[]>([]);
  const [subtasks, setSubtasks] = useState<Subtask[]>([]);
  const [newComment, setNewComment] = useState("");
  const [newSubtask, setNewSubtask] = useState("");

  useEffect(() => {
    fetch(`/api/tasks/${task.id}/activity`).then(r => r.json()).then(setActivity).catch(() => {});
    fetch(`/api/tasks/${task.id}/subtasks`).then(r => r.json()).then(setSubtasks).catch(() => {});
  }, [task.id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await fetch("/api/tasks", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: task.id,
          ...form,
          completedDate: form.status === "Completed" ? new Date().toISOString() : null,
        }),
      });
      onTaskUpdated();
      onClose();
    } catch (error) {
      console.error("Error updating task:", error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Delete this task?")) return;
    try {
      await fetch(`/api/tasks?id=${task.id}`, { method: "DELETE" });
      onTaskUpdated();
      onClose();
    } catch (error) {
      console.error("Error deleting task:", error);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;
    await fetch(`/api/tasks/${task.id}/activity`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: newComment, author: "Ahmed" }),
    });
    setNewComment("");
    const data = await fetch(`/api/tasks/${task.id}/activity`).then(r => r.json());
    setActivity(data);
  };

  const handleAddSubtask = async () => {
    if (!newSubtask.trim()) return;
    await fetch(`/api/tasks/${task.id}/subtasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: newSubtask }),
    });
    setNewSubtask("");
    const data = await fetch(`/api/tasks/${task.id}/subtasks`).then(r => r.json());
    setSubtasks(data);
  };

  const handleToggleSubtask = async (subtaskId: number) => {
    await fetch(`/api/tasks/${task.id}/subtasks`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subtaskId }),
    });
    const data = await fetch(`/api/tasks/${task.id}/subtasks`).then(r => r.json());
    setSubtasks(data);
  };

  const handleDeleteSubtask = async (subtaskId: number) => {
    await fetch(`/api/tasks/${task.id}/subtasks?subtaskId=${subtaskId}`, { method: "DELETE" });
    const data = await fetch(`/api/tasks/${task.id}/subtasks`).then(r => r.json());
    setSubtasks(data);
  };

  const statuses = ["Inbox", "My Tasks", "OpenClaw Tasks", "In Progress", "QA", "Review", "Completed"];

  const activityIcon = (type: string) => {
    switch (type) {
      case "created": return "🆕";
      case "status_change": return "📋";
      case "updated": return "✏️";
      case "comment": return "💬";
      case "subtask_added": return "☑️";
      default: return "📌";
    }
  };

  const timeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  return (
    <div className="fixed inset-0 modal-overlay flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="glass-strong rounded-2xl w-full max-w-lg max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 pb-0">
          <h2 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            Edit Task
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors text-xl">✕</button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-6 pt-4">
          {(["details", "subtasks", "activity"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${
                tab === t ? "bg-indigo-500/20 text-indigo-300" : "text-gray-500 hover:text-white"
              }`}
            >
              {t === "details" ? "📝 Details" : t === "subtasks" ? `☑️ Subtasks (${subtasks.length})` : `💬 Activity (${activity.length})`}
            </button>
          ))}
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {tab === "details" && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Title</label>
                <input
                  type="text"
                  required
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="w-full search-input rounded-lg px-4 py-2.5 text-white text-sm"
                />
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  className="w-full search-input rounded-lg px-4 py-2.5 text-white text-sm h-20 resize-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Status</label>
                <div className="flex flex-wrap gap-2">
                  {statuses.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setForm({ ...form, status: s })}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                        form.status === s
                          ? s === "Review" ? "bg-pink-500/20 text-pink-300 border border-pink-500/30" : "btn-primary text-white"
                          : "glass hover:bg-white/5 text-gray-500"
                      }`}
                    >
                      {s === "Review" ? "👀 " : ""}{s}
                    </button>
                  ))}
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Assignee</label>
                  <select
                    value={form.assignee}
                    onChange={(e) => setForm({ ...form, assignee: e.target.value })}
                    className="w-full search-input rounded-lg px-3 py-2.5 text-white text-sm bg-transparent"
                  >
                    <option value="Ahmed" className="bg-gray-900">👤 Ahmed</option>
                    <option value="OpenClaw" className="bg-gray-900">🤖 OpenClaw</option>
                    <option value="NASR (Coder)" className="bg-gray-900">💻 NASR (Coder)</option>
                    <option value="NASR (Writer)" className="bg-gray-900">✍️ NASR (Writer)</option>
                    <option value="NASR (Research)" className="bg-gray-900">🔍 NASR (Research)</option>
                    <option value="NASR (CV)" className="bg-gray-900">📄 NASR (CV)</option>
                    <option value="QA Agent" className="bg-gray-900">🛡️ QA Agent</option>
                    <option value="Both" className="bg-gray-900">👥 Both</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Priority</label>
                  <div className="flex gap-2">
                    {["High", "Medium", "Low"].map((p) => (
                      <button
                        key={p}
                        type="button"
                        onClick={() => setForm({ ...form, priority: p })}
                        className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${
                          form.priority === p
                            ? p === "High" ? "priority-high" : p === "Medium" ? "priority-medium" : "priority-low"
                            : "glass hover:bg-white/5 text-gray-500"
                        }`}
                      >
                        {p === "High" ? "🔴" : p === "Medium" ? "🟡" : "🟢"}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Category</label>
                  <select
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                    className="w-full search-input rounded-lg px-3 py-2.5 text-white text-sm bg-transparent"
                  >
                    <option value="Job Search" className="bg-gray-900">🎯 Job Search</option>
                    <option value="Content" className="bg-gray-900">📝 Content</option>
                    <option value="Networking" className="bg-gray-900">🤝 Networking</option>
                    <option value="Applications" className="bg-gray-900">📋 Applications</option>
                    <option value="Interviews" className="bg-gray-900">🎤 Interviews</option>
                    <option value="Task" className="bg-gray-900">📌 Task</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Due Date</label>
                  <input
                    type="date"
                    value={form.dueDate}
                    onChange={(e) => setForm({ ...form, dueDate: e.target.value })}
                    className="w-full search-input rounded-lg px-3 py-2.5 text-white text-sm bg-transparent"
                  />
                </div>
              </div>

              <div className="text-xs text-gray-600 flex justify-between pt-1">
                <span>Created: {new Date(task.createdAt).toLocaleDateString()}</span>
                <span>ID: #{task.id}</span>
              </div>
              
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={handleDelete} className="px-4 py-2.5 glass rounded-lg hover:bg-red-500/10 transition-all text-sm text-red-400">
                  🗑️ Delete
                </button>
                <div className="flex-1" />
                <button type="button" onClick={onClose} className="px-4 py-2.5 glass rounded-lg hover:bg-white/5 transition-all text-sm text-gray-400">
                  Cancel
                </button>
                <button type="submit" disabled={submitting} className="px-6 py-2.5 btn-primary text-white text-sm disabled:opacity-50">
                  {submitting ? "Saving..." : "Save"}
                </button>
              </div>
            </form>
          )}

          {tab === "subtasks" && (
            <div className="space-y-3">
              {/* Add subtask */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newSubtask}
                  onChange={(e) => setNewSubtask(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddSubtask()}
                  placeholder="Add a subtask..."
                  className="flex-1 search-input rounded-lg px-4 py-2.5 text-white text-sm"
                />
                <button onClick={handleAddSubtask} className="btn-primary text-white text-sm px-4">Add</button>
              </div>

              {/* Progress bar */}
              {subtasks.length > 0 && (
                <div>
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>{subtasks.filter(s => s.completed).length}/{subtasks.length} done</span>
                    <span>{Math.round((subtasks.filter(s => s.completed).length / subtasks.length) * 100)}%</span>
                  </div>
                  <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-green-500 rounded-full transition-all duration-300"
                      style={{ width: `${(subtasks.filter(s => s.completed).length / subtasks.length) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Subtask list */}
              <div className="space-y-1">
                {subtasks.map((sub) => (
                  <div key={sub.id} className="flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-white/5 group">
                    <button
                      onClick={() => handleToggleSubtask(sub.id)}
                      className={`w-5 h-5 rounded border-2 flex items-center justify-center text-xs transition-all ${
                        sub.completed 
                          ? "bg-green-500/20 border-green-500 text-green-400" 
                          : "border-gray-600 hover:border-indigo-500"
                      }`}
                    >
                      {sub.completed ? "✓" : ""}
                    </button>
                    <span className={`flex-1 text-sm ${sub.completed ? "line-through text-gray-600" : "text-white"}`}>
                      {sub.title}
                    </span>
                    <button
                      onClick={() => handleDeleteSubtask(sub.id)}
                      className="text-gray-600 hover:text-red-400 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      ✕
                    </button>
                  </div>
                ))}
                {subtasks.length === 0 && (
                  <div className="text-center py-8 text-gray-600 text-xs">No subtasks yet. Break this task into smaller steps.</div>
                )}
              </div>
            </div>
          )}

          {tab === "activity" && (
            <div className="space-y-3">
              {/* Add comment */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddComment()}
                  placeholder="Add a comment..."
                  className="flex-1 search-input rounded-lg px-4 py-2.5 text-white text-sm"
                />
                <button onClick={handleAddComment} className="btn-primary text-white text-sm px-4">Post</button>
              </div>

              {/* Activity feed */}
              <div className="space-y-1">
                {activity.map((a) => (
                  <div key={a.id} className="flex items-start gap-3 py-2 px-3 rounded-lg">
                    <span className="text-sm mt-0.5">{activityIcon(a.type)}</span>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm ${a.type === "comment" ? "text-white" : "text-gray-400"}`}>
                        {a.content}
                      </p>
                      <div className="flex gap-2 text-[10px] text-gray-600 mt-0.5">
                        <span>{a.author}</span>
                        <span>-</span>
                        <span>{timeAgo(a.createdAt)}</span>
                      </div>
                    </div>
                  </div>
                ))}
                {activity.length === 0 && (
                  <div className="text-center py-8 text-gray-600 text-xs">No activity yet.</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
