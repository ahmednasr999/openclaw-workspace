"use client";

import { useState } from "react";

interface NewContentFormProps {
  onClose: () => void;
  onPostAdded: () => void;
}

export function NewContentForm({ onClose, onPostAdded }: NewContentFormProps) {
  const [form, setForm] = useState({
    title: "",
    platform: "LinkedIn",
    contentType: "Post",
    assignee: "Both",
    priority: "Medium",
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await fetch("/api/content", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, status: "Ideas", createdAt: new Date().toISOString() }),
      });
      onPostAdded();
      onClose();
    } catch (error) {
      console.error("Error creating post:", error);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 modal-overlay flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="glass-strong rounded-2xl w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">New Content</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors text-xl">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Title</label>
            <input
              type="text"
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Content idea..."
              className="w-full search-input rounded-lg px-4 py-2.5 text-white text-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Platform</label>
              <select value={form.platform} onChange={(e) => setForm({ ...form, platform: e.target.value })} className="w-full search-input rounded-lg px-3 py-2.5 text-white text-sm bg-transparent">
                <option value="LinkedIn" className="bg-gray-900">LinkedIn</option>
                <option value="X" className="bg-gray-900">X</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Type</label>
              <select value={form.contentType} onChange={(e) => setForm({ ...form, contentType: e.target.value })} className="w-full search-input rounded-lg px-3 py-2.5 text-white text-sm bg-transparent">
                <option value="Post" className="bg-gray-900">Post</option>
                <option value="Article" className="bg-gray-900">Article</option>
                <option value="Carousel" className="bg-gray-900">Carousel</option>
                <option value="Video" className="bg-gray-900">Video</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Assignee</label>
              <select value={form.assignee} onChange={(e) => setForm({ ...form, assignee: e.target.value })} className="w-full search-input rounded-lg px-3 py-2.5 text-white text-sm bg-transparent">
                <option value="Ahmed" className="bg-gray-900">Ahmed</option>
                <option value="OpenClaw" className="bg-gray-900">OpenClaw</option>
                <option value="Both" className="bg-gray-900">Both</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Priority</label>
              <div className="flex gap-2">
                {["High", "Medium", "Low"].map((p) => (
                  <button key={p} type="button" onClick={() => setForm({ ...form, priority: p })}
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

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 px-4 py-2.5 glass rounded-lg hover:bg-white/5 transition-all text-sm text-gray-400">Cancel</button>
            <button type="submit" disabled={submitting} className="flex-1 px-6 py-2.5 btn-primary text-white text-sm disabled:opacity-50">
              {submitting ? "Creating..." : "Create Post"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
