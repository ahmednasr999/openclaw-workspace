"use client";

import { useState, useEffect, useRef } from "react";
import { Icon } from "./Icon";

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
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(true);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const saveTimeout = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetch(`/api/content/${post.id}/activity`).then(r => r.json()).then(setActivity).catch(() => {});
  }, [post.id]);

  const autoSave = () => {
    if (saveTimeout.current) clearTimeout(saveTimeout.current);
    setSaved(false);
    saveTimeout.current = setTimeout(async () => {
      setSaving(true);
      try {
        await fetch("/api/content", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: post.id, ...form }),
        });
        setSaving(false);
        setSaved(true);
        setLastSaved(new Date());
        onPostUpdated();
      } catch (error) {
        console.error("Error saving:", error);
        setSaving(false);
      }
    }, 1500);
  };

  const handleChange = (field: string, value: string) => {
    setForm((f) => ({ ...f, [field]: value }));
    autoSave();
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
    switch (type) {
      case "created": return "New";
      case "status_change": return "Status";
      case "updated": return "Edit";
      case "comment": return "Comment";
      default: return "Action";
    }
  };

  const linkedInCharLimit = 3000;
  const bodyChars = (form.body || "").length;
  const hookChars = (form.hook || "").length;
  const isOverLimit = bodyChars > linkedInCharLimit;

  const formatBody = (text: string) => {
    return text.split("\n\n").map((p, i) => (
      <p key={i} className="mb-4 text-sm leading-relaxed text-gray-200">{p}</p>
    ));
  };

  return (
    <div className="fixed inset-0 modal-overlay flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-[#0e0e16] border border-[rgba(255,255,255,0.1)] rounded-2xl w-full max-w-5xl max-h-[92vh] flex flex-col overflow-hidden" onClick={(e) => e.stopPropagation()}>
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[rgba(255,255,255,0.06)]">
          <div className="flex items-center gap-4">
            <h2 className="text-base font-semibold text-white">{form.title || "Untitled Post"}</h2>
            <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${form.status === "Published" ? "bg-green-500/20 text-green-400" : "bg-indigo-500/20 text-indigo-300"}`}>
              {form.status}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500">
              {saving ? "Saving..." : saved ? "✓" : "●"}
              {lastSaved && saved && <span className="ml-1 text-gray-600">· {lastSaved.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>}
            </span>
            <button onClick={onClose} className="w-8 h-8 rounded-lg flex items-center justify-center text-gray-500 hover:text-white hover:bg-white/5 transition-all">✕</button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-6 py-3 border-b border-[rgba(255,255,255,0.06)]">
          {(["content", "details", "activity"] as const).map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${
                tab === t ? "bg-[rgba(124,92,252,0.15)] text-[#a78bfa]" : "text-gray-500 hover:text-white"
              }`}
            >
              {t === "content" ? "Write" : t === "details" ? "Details" : `Activity (${activity.length})`}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex">
          {tab === "content" ? (
            <>
              {/* Editor */}
              <div className="flex-1 overflow-y-auto p-6 space-y-5 border-r border-[rgba(255,255,255,0.06)]">
                <div>
                  <input type="text" value={form.title} onChange={(e) => handleChange("title", e.target.value)}
                    placeholder="Post title..."
                    className="w-full bg-transparent text-lg font-semibold text-white placeholder-gray-600 outline-none border-b border-transparent focus:border-indigo-500/50 pb-2 transition-all" />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Hook / Opening</label>
                    <span className={`text-xs ${hookChars > 150 ? "text-yellow-400" : "text-gray-600"}`}>{hookChars}/150</span>
                  </div>
                  <textarea value={form.hook} onChange={(e) => handleChange("hook", e.target.value)}
                    placeholder="Grab attention with your opening line..."
                    className="w-full bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 outline-none focus:border-indigo-500/50 focus:bg-[rgba(255,255,255,0.05)] transition-all resize-none"
                    style={{ minHeight: 80 }} />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Body</label>
                    <span className={`text-xs ${isOverLimit ? "text-red-400" : bodyChars > linkedInCharLimit * 0.9 ? "text-yellow-400" : "text-gray-600"}`}>
                      {bodyChars.toLocaleString()}/{linkedInCharLimit.toLocaleString()}
                    </span>
                  </div>
                  <textarea value={form.body} onChange={(e) => handleChange("body", e.target.value)}
                    placeholder="Write your content here... Markdown-style line breaks are respected."
                    className="w-full bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 outline-none focus:border-indigo-500/50 focus:bg-[rgba(255,255,255,0.05)] transition-all resize-none"
                    style={{ minHeight: 350, fontFamily: "Inter, system-ui, sans-serif", lineHeight: 1.7 }} />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Hashtags</label>
                  <input type="text" value={form.hashtags} onChange={(e) => handleChange("hashtags", e.target.value)}
                    placeholder="#leadership #management"
                    className="w-full bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 outline-none focus:border-indigo-500/50 focus:bg-[rgba(255,255,255,0.05)] transition-all" />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Image URL (optional)</label>
                  <input type="text" value={form.imageUrl} onChange={(e) => handleChange("imageUrl", e.target.value)}
                    placeholder="https://..."
                    className="w-full bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 outline-none focus:border-indigo-500/50 focus:bg-[rgba(255,255,255,0.05)] transition-all" />
                </div>
              </div>

              {/* Live Preview */}
              <div className="w-[420px] overflow-y-auto bg-[#0a0a0f] p-5">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">A</div>
                  <div>
                    <div className="text-sm text-white font-medium">Ahmed Nasr</div>
                    <div className="text-[10px] text-gray-500">Senior Technology Executive</div>
                  </div>
                </div>

                {form.hook && (
                  <p className="text-sm text-white font-medium mb-3 leading-relaxed">{form.hook}</p>
                )}
                
                {form.body && (
                  <div className="text-sm text-gray-300 leading-relaxed mb-4 whitespace-pre-wrap">{form.body}</div>
                )}

                {form.imageUrl && (
                  <div className="rounded-lg overflow-hidden mb-4 border border-[rgba(255,255,255,0.1)]">
                    <img src={form.imageUrl} alt="Post attachment" className="w-full h-auto" onError={(e) => { e.currentTarget.style.display = "none"; }} />
                  </div>
                )}

                {form.hashtags && (
                  <p className="text-sm text-[#0a66c2] font-medium">{form.hashtags}</p>
                )}

                <div className="mt-6 pt-4 border-t border-[rgba(255,255,255,0.06)]">
                  <div className="flex items-center gap-4 text-gray-500">
                    <span className="text-xs">👍 ❤️ 💡</span>
                    <span className="text-xs">42 comments</span>
                  </div>
                </div>
              </div>
            </>
          ) : tab === "details" ? (
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Platform</label>
                  <select value={form.platform} onChange={(e) => handleChange("platform", e.target.value)}
                    className="w-full bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)] rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-indigo-500/50">
                    <option value="LinkedIn">LinkedIn</option>
                    <option value="X">X</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Content Type</label>
                  <select value={form.contentType} onChange={(e) => handleChange("contentType", e.target.value)}
                    className="w-full bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)] rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-indigo-500/50">
                    <option value="Post">Post</option>
                    <option value="Article">Article</option>
                    <option value="Carousel">Carousel</option>
                    <option value="Video">Video</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">Status</label>
                <div className="flex flex-wrap gap-2">
                  {statuses.map((s) => (
                    <button key={s} onClick={() => handleChange("status", s)}
                      className={`px-3 py-2 rounded-lg text-xs font-medium transition-all border ${
                        form.status === s
                          ? s === "Published" ? "border-green-500/50 bg-green-500/10 text-green-400" : "border-indigo-500/50 bg-indigo-500/10 text-indigo-300"
                          : "border-[rgba(255,255,255,0.08)] text-gray-500 hover:border-[rgba(255,255,255,0.15)] hover:text-gray-300"
                      }`}
                    >{s}</button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Assignee</label>
                  <select value={form.assignee} onChange={(e) => handleChange("assignee", e.target.value)}
                    className="w-full bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)] rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-indigo-500/50">
                    <option value="Ahmed">Ahmed</option>
                    <option value="OpenClaw">OpenClaw</option>
                    <option value="Both">Both</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Priority</label>
                  <div className="flex gap-2">
                    {["High", "Medium", "Low"].map((p) => (
                      <button key={p} onClick={() => handleChange("priority", p)}
                        className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all border ${
                          form.priority === p
                            ? p === "High" ? "border-red-500/50 bg-red-500/10 text-red-400" : p === "Medium" ? "border-yellow-500/50 bg-yellow-500/10 text-yellow-400" : "border-green-500/50 bg-green-500/10 text-green-400"
                            : "border-[rgba(255,255,255,0.08)] text-gray-500 hover:border-[rgba(255,255,255,0.15)]"
                        }`}
                      >{p}</button>
                    ))}
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Publish Date</label>
                <input type="date" value={form.publishDate} onChange={(e) => handleChange("publishDate", e.target.value)}
                  className="w-full bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)] rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-indigo-500/50" />
              </div>

              <div className="pt-4 border-t border-[rgba(255,255,255,0.06)]">
                <button onClick={handleDelete} className="px-4 py-2 rounded-lg text-xs font-medium text-red-400 hover:bg-red-500/10 transition-all">Delete Post</button>
              </div>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <div className="flex gap-3">
                <input type="text" value={newComment} onChange={(e) => setNewComment(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddComment()}
                  placeholder="Add a comment..."
                  className="flex-1 bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 outline-none focus:border-indigo-500/50" />
                <button onClick={handleAddComment} className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium text-white transition-all">Post</button>
              </div>
              <div className="space-y-2">
                {activity.map((a) => (
                  <div key={a.id} className="flex items-start gap-3 p-3 rounded-lg hover:bg-white/5 transition-all">
                    <span className="text-base">{activityIcon(a.type)}</span>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm ${a.type === "comment" ? "text-white" : "text-gray-400"}`}>{a.content}</p>
                      <p className="text-[10px] text-gray-600 mt-1">{a.author} · {timeAgo(a.createdAt)}</p>
                    </div>
                  </div>
                ))}
                {activity.length === 0 && <div className="text-center py-12 text-gray-600 text-sm">No activity yet</div>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
