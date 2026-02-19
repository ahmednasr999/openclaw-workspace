"use client";

import { useState } from "react";

interface TaskFormProps {
  onClose: () => void;
  onTaskAdded: () => void;
}

export function TaskForm({ onClose, onTaskAdded }: TaskFormProps) {
  const [form, setForm] = useState({
    title: "",
    description: "",
    assignee: "Ahmed",
    priority: "Medium",
    category: "Job Search",
    dueDate: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    
    const task = {
      title: form.title,
      description: form.description || undefined,
      assignee: form.assignee,
      status: "Inbox",
      priority: form.priority,
      category: form.category,
      dueDate: form.dueDate || undefined,
      createdAt: new Date().toISOString(),
    };

    try {
      await fetch("/api/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(task),
      });
      onTaskAdded();
      onClose();
    } catch (error) {
      console.error("Error adding task:", error);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 modal-overlay flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="glass-strong rounded-2xl p-6 w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            New Task
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors text-xl">✕</button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Title</label>
            <input
              type="text"
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full search-input rounded-lg px-4 py-2.5 text-white text-sm"
              placeholder="What needs to be done?"
              autoFocus
            />
          </div>
          
          {/* Description */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full search-input rounded-lg px-4 py-2.5 text-white text-sm h-20 resize-none"
              placeholder="Add details..."
            />
          </div>
          
          {/* Two columns */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Assignee</label>
              <select
                value={form.assignee}
                onChange={(e) => setForm({ ...form, assignee: e.target.value })}
                className="w-full search-input rounded-lg px-3 py-2.5 text-white text-sm bg-transparent"
              >
                <option value="Ahmed" className="bg-gray-900">Ahmed</option>
                <option value="OpenClaw" className="bg-gray-900">OpenClaw</option>
                <option value="NASR (Coder)" className="bg-gray-900">NASR (Coder)</option>
                <option value="NASR (Writer)" className="bg-gray-900">NASR (Writer)</option>
                <option value="NASR (Research)" className="bg-gray-900">NASR (Research)</option>
                <option value="NASR (CV)" className="bg-gray-900">NASR (CV)</option>
                <option value="QA Agent" className="bg-gray-900">QA Agent</option>
                <option value="Both" className="bg-gray-900">Both</option>
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
                        ? p === "High" ? "priority-high" 
                          : p === "Medium" ? "priority-medium" 
                          : "priority-low"
                        : "glass hover:bg-white/5 text-gray-500"
                    }`}
                  >
                    {p === "High" ? "🔴" : p === "Medium" ? "🟡" : "🟢"} {p}
                  </button>
                ))}
              </div>
            </div>
          </div>
          
          {/* Category + Due Date */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Category</label>
              <select
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="w-full search-input rounded-lg px-3 py-2.5 text-white text-sm bg-transparent"
              >
                <option value="Job Search" className="bg-gray-900">Job Search</option>
                <option value="Content" className="bg-gray-900">Content</option>
                <option value="Networking" className="bg-gray-900">Networking</option>
                <option value="Applications" className="bg-gray-900">📋 Applications</option>
                <option value="Interviews" className="bg-gray-900">Interviews</option>
                <option value="Task" className="bg-gray-900">Task</option>
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
          
          {/* Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 glass rounded-lg hover:bg-white/5 transition-all text-sm text-gray-400"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 py-2.5 btn-success text-white text-sm disabled:opacity-50"
            >
              {submitting ? "Adding..." : "Add Task"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
