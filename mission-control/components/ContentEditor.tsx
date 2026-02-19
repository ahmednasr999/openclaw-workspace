"use client";

import { useState, useEffect } from "react";

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

interface Activity {
  id: number;
  postId: number;
  type: string;
  content: string;
  author: string;
  createdAt: string;
}

interface ContentEditorProps {
  post: ContentPost;
  onClose: () => void;
  onPostUpdated: () => void;
}

export function ContentEditor({ post, onClose, onPostUpdated }: ContentEditorProps) {
  const [form, setForm] = useState({
    title: post.title,
    hook: post.hook || "",
    body: post.body || "",
    platform: post.platform,
    contentType: post.contentType,
    status: post.status,
    hashtags: post.hashtags || "",
    imageUrl: post.imageUrl || "",
    publishDate: post.publishDate || "",
    assignee: post.assignee,
    priority: post.priority,
  });
  const [tab, setTab] = useState<"content" | "details" | "activity">("content");
  const [activity, setActivity] = useState<Activity[]>([]);
  const [newComment, setNewComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetch(`/api/content/${post.id}/activity`).then(r => r.json()).then(setActivity).catch(() => {});
  }, [post.id]);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await fetch("/api/content", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: post.id, ...form }),
      });
      onPostUpdated();
      onClose();
    } catch (error) {
      console.error("Error updating post:", error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Delete this post?")) return;
    await fetch(`/api/content?id=${post.id}`, { method: "DELETE" });
    onPostUpdated();
    onClose();
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;
    await fetch(`/api/content/${post.id}/activity`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: newComment, author: "Ahmed" }),
    });
    setNewComment("");
    const data = await fetch(`/api/content/${post.id}/activity`).then(r => r.json());
    setActivity(data);
  };

  const statuses = ["Ideas", "Outline", "Draft", "Design", "Review", "Published"];

  const timeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  const activityIcon = (type: string) => {
    switch (type) { case "created": return "🆕"; case "status_change": return "📋"; case "updated": return "✏️"; case "comment": return "💬"; default: return "📌"; }
  };

  return (
    <div className="fixed inset-0 modal-overlay flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="glass-strong rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 pb-0">
          <h2 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">Edit Content</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors text-xl">✕</button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-6 pt-4">
          {(["content", "details", "activity"] as const).map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${tab === t ? "bg-indigo-500/20 text-indigo-300" : "text-gray-500 hover:text-white"}`}
            >
              {t === "content" ? "📝 Content" : t === "details" ? "⚙️ Details" : `💬 Activity (${activity.length})`}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {tab === "content" && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Title</label>
                <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="w-full search-input rounded-lg px-4 py-2.5 text-white text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Hook (Opening Line)</label>
                <textarea value={form.hook} onChange={(e) => setForm({ ...form, hook: e.target.value })}
                  placeholder="The attention-grabbing opening..."
                  className="w-full search-input rounded-lg px-4 py-2.5 text-white text-sm h-20 resize-none" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Body</label>
                <textarea value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })}
                  placeholder="Write your content here... Markdown supported."
                  className="w-full search-input rounded-lg px-4 py-2.5 text-white text-sm resize-y"
                  style={{ minHeight: 300, fontFamily: "monospace" }} />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Hashtags</label>
                <input type="text" value={form.hashtags} onChange={(e) => setForm({ ...form, hashtags: e.target.value })}
                  placeholder="#marketing #leadership"
                  className="w-full search-input rounded-lg px-4 py-2.5 text-white text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Image URL</label>
                <input type="text" value={form.imageUrl} onChange={(e) => setForm({ ...form, imageUrl: e.target.value })}
                  placeholder="https://..."
                  className="w-full search-input rounded-lg px-4 py-2.5 text-white text-sm" />
              </div>

              {/* Preview */}
              {(form.hook || form.body) && (
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">LinkedIn Preview</label>
                  <div className="glass rounded-lg p-4 space-y-2">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">A</div>
                      <div>
                        <div className="text-xs text-white font-medium">Ahmed Nasr</div>
                        <div className="text-[10px] text-gray-500">Just now · 🌐</div>
                      </div>
                    </div>
                    {form.hook && <p className="text-sm text-white font-medium">{form.hook}</p>}
                    {form.body && <p className="text-xs text-gray-400 whitespace-pre-wrap">{form.body.slice(0, 200)}{form.body.length > 200 ? "..." : ""}</p>}
                    {form.hashtags && <p className="text-xs text-blue-400">{form.hashtags}</p>}
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={onClose} className="px-4 py-2.5 glass rounded-lg hover:bg-white/5 transition-all text-sm text-gray-400">Cancel</button>
                <div className="flex-1" />
                <button onClick={handleSubmit} disabled={submitting} className="px-6 py-2.5 btn-primary text-white text-sm disabled:opacity-50">
                  {submitting ? "Saving..." : "Save"}
                </button>
              </div>
            </div>
          )}

          {tab === "details" && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Platform</label>
                  <select value={form.platform} onChange={(e) => setForm({ ...form, platform: e.target.value })} className="w-full search-input rounded-lg px-3 py-2.5 text-white text-sm bg-transparent">
                    <option value="LinkedIn" className="bg-gray-900">LinkedIn</option>
                    <option value="X" className="bg-gray-900">X</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Content Type</label>
                  <select value={form.contentType} onChange={(e) => setForm({ ...form, contentType: e.target.value })} className="w-full search-input rounded-lg px-3 py-2.5 text-white text-sm bg-transparent">
                    <option value="Post" className="bg-gray-900">Post</option>
                    <option value="Article" className="bg-gray-900">Article</option>
                    <option value="Carousel" className="bg-gray-900">Carousel</option>
                    <option value="Video" className="bg-gray-900">Video</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Status</label>
                <div className="flex flex-wrap gap-2">
                  {statuses.map((s) => (
                    <button key={s} type="button" onClick={() => setForm({ ...form, status: s })}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${form.status === s ? "btn-primary text-white" : "glass hover:bg-white/5 text-gray-500"}`}
                    >{s}</button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Assignee</label>
                  <select value={form.assignee} onChange={(e) => setForm({ ...form, assignee: e.target.value })} className="w-full search-input rounded-lg px-3 py-2.5 text-white text-sm bg-transparent">
                    <option value="Ahmed" className="bg-gray-900">👤 Ahmed</option>
                    <option value="OpenClaw" className="bg-gray-900">🤖 OpenClaw</option>
                    <option value="Both" className="bg-gray-900">👥 Both</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Priority</label>
                  <div className="flex gap-2">
                    {["High", "Medium", "Low"].map((p) => (
                      <button key={p} type="button" onClick={() => setForm({ ...form, priority: p })}
                        className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${form.priority === p ? p === "High" ? "priority-high" : p === "Medium" ? "priority-medium" : "priority-low" : "glass hover:bg-white/5 text-gray-500"}`}
                      >{p === "High" ? "🔴" : p === "Medium" ? "🟡" : "🟢"}</button>
                    ))}
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Publish Date</label>
                <input type="date" value={form.publishDate} onChange={(e) => setForm({ ...form, publishDate: e.target.value })}
                  className="w-full search-input rounded-lg px-3 py-2.5 text-white text-sm bg-transparent" />
              </div>

              <div className="text-xs text-gray-600 flex justify-between pt-1">
                <span>Created: {new Date(post.createdAt).toLocaleDateString()}</span>
                <span>ID: #{post.id}</span>
              </div>

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={handleDelete} className="px-4 py-2.5 glass rounded-lg hover:bg-red-500/10 transition-all text-sm text-red-400">🗑️ Delete</button>
                <div className="flex-1" />
                <button type="button" onClick={onClose} className="px-4 py-2.5 glass rounded-lg hover:bg-white/5 transition-all text-sm text-gray-400">Cancel</button>
                <button onClick={handleSubmit} disabled={submitting} className="px-6 py-2.5 btn-primary text-white text-sm disabled:opacity-50">
                  {submitting ? "Saving..." : "Save"}
                </button>
              </div>
            </div>
          )}

          {tab === "activity" && (
            <div className="space-y-3">
              <div className="flex gap-2">
                <input type="text" value={newComment} onChange={(e) => setNewComment(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddComment()}
                  placeholder="Add a comment..." className="flex-1 search-input rounded-lg px-4 py-2.5 text-white text-sm" />
                <button onClick={handleAddComment} className="btn-primary text-white text-sm px-4">Post</button>
              </div>
              <div className="space-y-1">
                {activity.map((a) => (
                  <div key={a.id} className="flex items-start gap-3 py-2 px-3 rounded-lg">
                    <span className="text-sm mt-0.5">{activityIcon(a.type)}</span>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm ${a.type === "comment" ? "text-white" : "text-gray-400"}`}>{a.content}</p>
                      <div className="flex gap-2 text-[10px] text-gray-600 mt-0.5">
                        <span>{a.author}</span><span>-</span><span>{timeAgo(a.createdAt)}</span>
                      </div>
                    </div>
                  </div>
                ))}
                {activity.length === 0 && <div className="text-center py-8 text-gray-600 text-xs">No activity yet.</div>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
