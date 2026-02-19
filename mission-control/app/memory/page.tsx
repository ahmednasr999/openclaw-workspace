"use client";

import { useState, useEffect } from "react";
import { Icon } from "@/components/Icon";

interface MemoryItem {
  id: string;
  type: "memory" | "chat" | "link" | "video" | "article" | "file" | "image" | "document";
  title: string;
  content: string;
  date: string;
  tags: string[];
  source: string;
  url?: string;
}

const TAGS = ["all", "memory", "content", "file", "inbound", "chat", "preferences", "decisions", "lessons", "daily"];

const TYPE_ICONS: Record<string, string> = {
  memory: "📝",
  chat: "💬",
  link: "🔗",
  video: "🎬",
  article: "📄",
  file: "📎",
  image: "🖼️",
  document: "📃",
};

export default function MemoryPage() {
  const [items, setItems] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedTag, setSelectedTag] = useState("all");
  const [selectedItem, setSelectedItem] = useState<MemoryItem | null>(null);

  useEffect(() => {
    fetchMemories();
  }, [search, selectedTag]);

  const fetchMemories = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set("q", search);
      if (selectedTag !== "all") params.set("tag", selectedTag);
      
      const res = await fetch(`/api/memory?${params}`);
      const data = await res.json();
      setItems(data);
    } catch (error) {
      console.error("Failed to fetch memories:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  };

  const getTypeIcon = (type: string) => TYPE_ICONS[type] || "📄";

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[rgba(255,255,255,0.06)]">
        <h1 className="text-xl font-bold text-white">Memory</h1>
        <p className="text-xs text-gray-500 mt-1">Your entire digital life, searchable</p>
      </div>

      {/* Search & Filters */}
      <div className="px-6 py-4 border-b border-[rgba(255,255,255,0.04)] bg-[rgba(255,255,255,0.02)]">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Icon name="search" className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
            <input
              type="text"
              placeholder="Search memories, chats, files, content..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.08)] rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-indigo-500/50"
            />
          </div>
        </div>
        
        {/* Tags */}
        <div className="flex items-center gap-2 mt-4 overflow-x-auto pb-1">
          {TAGS.map((tag) => (
            <button
              key={tag}
              onClick={() => setSelectedTag(tag)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                selectedTag === tag
                  ? "bg-[rgba(124,92,252,0.15)] text-[#a78bfa] border border-indigo-500/30"
                  : "text-gray-500 hover:text-white border border-transparent hover:border-[rgba(255,255,255,0.08)]"
              }`}
            >
              {tag.charAt(0).toUpperCase() + tag.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-auto p-6">
        {loading ? (
          <div className="text-center text-gray-500 py-12">Loading...</div>
        ) : items.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            <div className="text-4xl mb-4">🧠</div>
            <p>No memories found</p>
            <p className="text-xs mt-2">Try a different search or tag</p>
          </div>
        ) : (
          <div className="grid gap-3">
            {items.map((item) => (
              <button
                key={item.id}
                onClick={() => setSelectedItem(item)}
                className="flex items-start gap-4 p-4 rounded-xl bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.04)] hover:border-[rgba(255,255,255,0.1)] transition-all text-left group"
              >
                <div className="text-2xl">{getTypeIcon(item.type)}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-white truncate">{item.title}</span>
                    <span className="text-[10px] text-gray-600">{formatDate(item.date)}</span>
                  </div>
                  <p className="text-xs text-gray-500 line-clamp-2 mb-2">{item.content}</p>
                  <div className="flex items-center gap-2">
                    {item.tags.slice(0, 4).map((tag) => (
                      <span key={tag} className="text-[10px] px-2 py-0.5 rounded bg-[rgba(255,255,255,0.05)] text-gray-500">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedItem && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setSelectedItem(null)}>
          <div className="bg-[#12121a] border border-[rgba(255,255,255,0.1)] rounded-xl w-full max-w-2xl max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between p-6 border-b border-[rgba(255,255,255,0.06)]">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">{getTypeIcon(selectedItem.type)}</span>
                  <h2 className="text-lg font-semibold text-white">{selectedItem.title}</h2>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span>{formatDate(selectedItem.date)}</span>
                  <span>•</span>
                  <span>{selectedItem.source}</span>
                </div>
              </div>
              <button onClick={() => setSelectedItem(null)} className="text-gray-500 hover:text-white">
                <Icon name="close" size={20} />
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{selectedItem.content}</p>
              {selectedItem.content.length === 0 && (
                <p className="text-gray-600 text-sm italic">No additional content available</p>
              )}
            </div>
            <div className="px-6 py-4 border-t border-[rgba(255,255,255,0.06)] flex items-center gap-2 flex-wrap">
              {selectedItem.tags.map((tag) => (
                <span key={tag} className="text-xs px-2 py-1 rounded bg-[rgba(124,92,252,0.1)] text-[#a78bfa]">
                  #{tag}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="px-6 py-3 border-t border-[rgba(255,255,255,0.06)] text-xs text-gray-600">
        {items.length} memories found {search && `for "${search}"`}
      </div>
    </div>
  );
}
