"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Icon } from "@/components/Icon";

interface MemoryItem {
  id: string;
  type: "memory" | "chat" | "link" | "video" | "article" | "file" | "image" | "document";
  title: string;
  content: string;
  fullContent?: string;
  date: string;
  tags: string[];
  source: string;
  sourceCategory: "memory" | "content" | "files" | "chats";
  url?: string;
  filePath?: string;
  fileSize?: number;
}

interface APIResponse {
  items: MemoryItem[];
  total: number;
  page: number;
  limit: number;
  pages: number;
  tagCounts: Record<string, number>;
  sourceCounts: Record<string, number>;
}

const SOURCE_FILTERS = [
  { key: "", label: "All Sources", icon: "🌐" },
  { key: "memory", label: "Memory", icon: "📝" },
  { key: "content", label: "Content", icon: "📰" },
  { key: "files", label: "Files", icon: "📎" },
  { key: "chats", label: "Chats", icon: "💬" },
];

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
  const [data, setData] = useState<APIResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedTag, setSelectedTag] = useState("");
  const [selectedSource, setSelectedSource] = useState("");
  const [selectedItem, setSelectedItem] = useState<MemoryItem | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [page, setPage] = useState(1);
  const [copied, setCopied] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const fetchMemories = useCallback(async (p = page) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set("q", search);
      if (selectedTag) params.set("tag", selectedTag);
      if (selectedSource) params.set("source", selectedSource);
      params.set("page", String(p));
      params.set("limit", "50");

      const res = await fetch(`/api/memory?${params}`);
      const result = await res.json();
      setData(result);
    } catch (error) {
      console.error("Failed to fetch memories:", error);
    } finally {
      setLoading(false);
    }
  }, [search, selectedTag, selectedSource, page]);

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setPage(1);
      fetchMemories(1);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [search]);

  // Immediate fetch on filter change
  useEffect(() => {
    setPage(1);
    fetchMemories(1);
  }, [selectedTag, selectedSource]);

  // Fetch on page change
  useEffect(() => {
    fetchMemories(page);
  }, [page]);

  const fetchFullItem = async (item: MemoryItem) => {
    setSelectedItem(item);
    setLoadingDetail(true);
    try {
      const res = await fetch(`/api/memory?id=${encodeURIComponent(item.id)}`);
      const full = await res.json();
      if (full && !full.error) {
        setSelectedItem(full);
      }
    } catch {
      // Keep the preview version
    } finally {
      setLoadingDetail(false);
    }
  };

  const copyContent = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "Africa/Cairo" });
  };

  const formatSize = (bytes?: number) => {
    if (!bytes) return "";
    if (bytes > 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${Math.round(bytes / 1024)} KB`;
  };

  const getTypeIcon = (type: string) => TYPE_ICONS[type] || "📄";

  const items = data?.items || [];
  const tagCounts = data?.tagCounts || {};
  const sourceCounts = data?.sourceCounts || {};
  const total = data?.total || 0;
  const pages = data?.pages || 1;

  // Build dynamic tag list from actual data, sorted by count
  const dynamicTags = Object.entries(tagCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 15);

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

        {/* Source filters */}
        <div className="flex items-center gap-2 mt-3">
          {SOURCE_FILTERS.map((sf) => {
            const count = sf.key ? sourceCounts[sf.key] || 0 : total;
            return (
              <button
                key={sf.key}
                onClick={() => setSelectedSource(sf.key)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all flex items-center gap-1.5 ${
                  selectedSource === sf.key
                    ? "bg-[rgba(124,92,252,0.15)] text-[#a78bfa] border border-indigo-500/30"
                    : "text-gray-500 hover:text-white border border-transparent hover:border-[rgba(255,255,255,0.08)]"
                }`}
              >
                <span>{sf.icon}</span>
                <span>{sf.label}</span>
                <span className="text-[10px] opacity-60">({count})</span>
              </button>
            );
          })}
        </div>

        {/* Dynamic tags */}
        {dynamicTags.length > 0 && (
          <div className="flex items-center gap-2 mt-3 overflow-x-auto pb-1">
            <button
              onClick={() => setSelectedTag("")}
              className={`px-2.5 py-1 rounded text-[10px] font-medium whitespace-nowrap transition-all ${
                !selectedTag
                  ? "bg-white/10 text-white"
                  : "text-gray-600 hover:text-gray-400"
              }`}
            >
              All tags
            </button>
            {dynamicTags.map(([tag, count]) => (
              <button
                key={tag}
                onClick={() => setSelectedTag(selectedTag === tag ? "" : tag)}
                className={`px-2.5 py-1 rounded text-[10px] font-medium whitespace-nowrap transition-all ${
                  selectedTag === tag
                    ? "bg-[rgba(124,92,252,0.15)] text-[#a78bfa]"
                    : "text-gray-600 hover:text-gray-400"
                }`}
              >
                #{tag} <span className="opacity-50">{count}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Results */}
      <div className="flex-1 overflow-auto p-6">
        {loading && items.length === 0 ? (
          <div className="text-center text-gray-500 py-12">Loading...</div>
        ) : items.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            <div className="text-4xl mb-4">🧠</div>
            {search ? (
              <>
                <p>No results for &ldquo;{search}&rdquo;</p>
                <p className="text-xs mt-2">Try different keywords or clear filters</p>
                <button
                  onClick={() => { setSearch(""); setSelectedTag(""); setSelectedSource(""); }}
                  className="mt-4 px-4 py-2 rounded-lg text-xs bg-white/5 border border-[rgba(255,255,255,0.08)] text-gray-400 hover:text-white transition-all"
                >
                  Clear all filters
                </button>
              </>
            ) : selectedTag || selectedSource ? (
              <>
                <p>No items match this filter</p>
                <button
                  onClick={() => { setSelectedTag(""); setSelectedSource(""); }}
                  className="mt-4 px-4 py-2 rounded-lg text-xs bg-white/5 border border-[rgba(255,255,255,0.08)] text-gray-400 hover:text-white transition-all"
                >
                  Clear filters
                </button>
              </>
            ) : (
              <>
                <p>No memories yet</p>
                <p className="text-xs mt-2">Memory files, shared content, and chat sessions will appear here</p>
              </>
            )}
          </div>
        ) : (
          <div className="grid gap-3">
            {items.map((item) => (
              <button
                key={item.id}
                onClick={() => fetchFullItem(item)}
                className="flex items-start gap-4 p-4 rounded-xl bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.04)] hover:border-[rgba(255,255,255,0.1)] transition-all text-left group"
              >
                <div className="text-2xl flex-shrink-0">{getTypeIcon(item.type)}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-white truncate">{item.title}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded flex-shrink-0 ${
                      item.sourceCategory === "memory" ? "bg-indigo-500/10 text-indigo-400" :
                      item.sourceCategory === "content" ? "bg-purple-500/10 text-purple-400" :
                      item.sourceCategory === "files" ? "bg-amber-500/10 text-amber-400" :
                      "bg-green-500/10 text-green-400"
                    }`}>
                      {item.sourceCategory}
                    </span>
                    <span className="text-[10px] text-gray-600 flex-shrink-0">{formatDate(item.date)}</span>
                  </div>
                  <p className="text-xs text-gray-500 line-clamp-2 mb-2">{item.content}</p>
                  <div className="flex items-center gap-2">
                    {item.tags.slice(0, 4).map((tag) => (
                      <span key={tag} className="text-[10px] px-2 py-0.5 rounded bg-[rgba(255,255,255,0.05)] text-gray-500">
                        #{tag}
                      </span>
                    ))}
                    {item.tags.length > 4 && (
                      <span className="text-[10px] text-gray-600">+{item.tags.length - 4}</span>
                    )}
                    {item.fileSize && (
                      <span className="text-[10px] text-gray-600 ml-auto">{formatSize(item.fileSize)}</span>
                    )}
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
          <div className="bg-[#12121a] border border-[rgba(255,255,255,0.1)] rounded-xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
            {/* Modal header */}
            <div className="flex items-start justify-between p-6 border-b border-[rgba(255,255,255,0.06)] flex-shrink-0">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">{getTypeIcon(selectedItem.type)}</span>
                  <h2 className="text-lg font-semibold text-white truncate">{selectedItem.title}</h2>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span>{formatDate(selectedItem.date)}</span>
                  <span>-</span>
                  <span>{selectedItem.source}</span>
                  {selectedItem.fileSize && (
                    <>
                      <span>-</span>
                      <span>{formatSize(selectedItem.fileSize)}</span>
                    </>
                  )}
                </div>
              </div>
              <button onClick={() => setSelectedItem(null)} className="text-gray-500 hover:text-white flex-shrink-0 ml-4">
                <Icon name="close" size={20} />
              </button>
            </div>

            {/* Modal content */}
            <div className="flex-1 overflow-y-auto p-6">
              {loadingDetail ? (
                <div className="text-center text-gray-500 py-8">Loading full content...</div>
              ) : (
                <pre className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap font-sans">
                  {selectedItem.fullContent || selectedItem.content}
                </pre>
              )}
              {!loadingDetail && !selectedItem.fullContent && !selectedItem.content && (
                <p className="text-gray-600 text-sm italic">No content available</p>
              )}
            </div>

            {/* Modal footer with actions */}
            <div className="px-6 py-4 border-t border-[rgba(255,255,255,0.06)] flex items-center gap-3 flex-shrink-0">
              <div className="flex items-center gap-2 flex-wrap flex-1">
                {selectedItem.tags.map((tag) => (
                  <span key={tag} className="text-xs px-2 py-1 rounded bg-[rgba(124,92,252,0.1)] text-[#a78bfa]">
                    #{tag}
                  </span>
                ))}
              </div>
              <button
                onClick={() => copyContent(selectedItem.fullContent || selectedItem.content)}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white/5 border border-[rgba(255,255,255,0.08)] text-gray-400 hover:text-white hover:bg-white/10 transition-all flex-shrink-0"
              >
                {copied ? "✓ Copied" : "Copy"}
              </button>
              {selectedItem.filePath && (
                <span className="text-[10px] text-gray-600 truncate max-w-[200px]" title={selectedItem.filePath}>
                  {selectedItem.filePath}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Footer with pagination */}
      <div className="px-6 py-3 border-t border-[rgba(255,255,255,0.06)] flex items-center justify-between text-xs text-gray-600">
        <span>
          {total} {total === 1 ? "item" : "items"} found
          {search && ` for "${search}"`}
          {selectedTag && ` tagged #${selectedTag}`}
        </span>
        {pages > 1 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="px-2 py-1 rounded hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              ← Prev
            </button>
            <span className="text-gray-500">
              {page} / {pages}
            </span>
            <button
              onClick={() => setPage(Math.min(pages, page + 1))}
              disabled={page >= pages}
              className="px-2 py-1 rounded hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
