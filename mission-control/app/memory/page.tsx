"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import ReactMarkdown, { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
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
  score?: number;
  editable?: boolean;
  related?: MemoryItem[];
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

type TimelineData = Record<string, { total: number; memory: number; content: number; files: number; chats: number }>;

const SOURCE_FILTERS = [
  { key: "", label: "All Sources", icon: "🌐" },
  { key: "memory", label: "Memory", icon: "📝" },
  { key: "content", label: "Content", icon: "📰" },
  { key: "files", label: "Files", icon: "📎" },
  { key: "chats", label: "Chats", icon: "💬" },
];

const TYPE_ICONS: Record<string, string> = {
  memory: "📝", chat: "💬", link: "🔗", video: "🎬",
  article: "📄", file: "📎", image: "🖼️", document: "📃",
};

// Highlight search terms in text
function highlightText(text: string, query: string): React.ReactNode {
  if (!query || !text) return text;
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (terms.length === 0) return text;

  const regex = new RegExp(`(${terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "gi");
  const parts = text.split(regex);

  return parts.map((part, i) =>
    terms.some((t) => part.toLowerCase() === t) ? (
      <mark key={i} className="bg-yellow-500/30 text-yellow-200 rounded px-0.5">{part}</mark>
    ) : (
      part
    )
  );
}

// Build custom ReactMarkdown components that highlight search terms in text nodes
function useHighlightedMarkdown(query: string): Components | undefined {
  return useMemo(() => {
    if (!query) return undefined;
    const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
    if (terms.length === 0) return undefined;

    const regex = new RegExp(
      `(${terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`,
      "gi"
    );

    // Wrap text content with highlights
    const wrapText = (text: string): React.ReactNode => {
      const parts = text.split(regex);
      if (parts.length <= 1) return text;
      return parts.map((part, i) =>
        terms.some((t) => part.toLowerCase() === t) ? (
          <mark key={i} className="bg-yellow-500/30 text-yellow-200 rounded px-0.5">{part}</mark>
        ) : (
          part
        )
      );
    };

    // Override common block/inline elements to highlight their text children
    const makeComponent = (Tag: string) => {
      const Comp = ({ children, ...props }: any) => {
        const mapped = Array.isArray(children)
          ? children.map((child: any, i: number) =>
              typeof child === "string" ? <span key={i}>{wrapText(child)}</span> : child
            )
          : typeof children === "string"
          ? wrapText(children)
          : children;
        return <Tag {...props}>{mapped}</Tag>;
      };
      Comp.displayName = `Highlight_${Tag}`;
      return Comp;
    };

    return {
      p: makeComponent("p"),
      li: makeComponent("li"),
      td: makeComponent("td"),
      th: makeComponent("th"),
      h1: makeComponent("h1"),
      h2: makeComponent("h2"),
      h3: makeComponent("h3"),
      h4: makeComponent("h4"),
      strong: makeComponent("strong"),
      em: makeComponent("em"),
    } as Components;
  }, [query]);
}

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
  const [viewMode, setViewMode] = useState<"list" | "timeline">("list");
  const [timelineData, setTimelineData] = useState<TimelineData>({});
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState("");
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();
  const searchRef = useRef<HTMLInputElement>(null);
  const mdComponents = useHighlightedMarkdown(search);

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

  const fetchTimeline = useCallback(async () => {
    try {
      const res = await fetch("/api/memory?timeline=true");
      const result = await res.json();
      setTimelineData(result);
    } catch (error) {
      console.error("Failed to fetch timeline:", error);
    }
  }, []);

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setPage(1);
      fetchMemories(1);
    }, 300);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [search]);

  useEffect(() => { setPage(1); fetchMemories(1); }, [selectedTag, selectedSource]);
  useEffect(() => { fetchMemories(page); }, [page]);
  useEffect(() => { if (viewMode === "timeline") fetchTimeline(); }, [viewMode, fetchTimeline]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "/" && !editing && document.activeElement?.tagName !== "INPUT" && document.activeElement?.tagName !== "TEXTAREA") {
        e.preventDefault();
        searchRef.current?.focus();
      }
      if (e.key === "Escape") {
        if (editing) { setEditing(false); return; }
        if (selectedItem) { setSelectedItem(null); return; }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [editing, selectedItem]);

  const fetchFullItem = async (item: MemoryItem) => {
    setSelectedItem(item);
    setEditing(false);
    setLoadingDetail(true);
    try {
      const res = await fetch(`/api/memory?id=${encodeURIComponent(item.id)}&related=true`);
      const full = await res.json();
      if (full && !full.error) setSelectedItem(full);
    } catch {} finally {
      setLoadingDetail(false);
    }
  };

  const handleSave = async () => {
    if (!selectedItem) return;
    setSaving(true);
    setSaveMsg("");
    try {
      const res = await fetch("/api/memory", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: selectedItem.id, content: editContent }),
      });
      const result = await res.json();
      if (result.success) {
        setSaveMsg("Saved!");
        setSelectedItem({ ...selectedItem, fullContent: editContent, content: editContent.slice(0, 500) });
        setEditing(false);
        fetchMemories(page); // Refresh list
        setTimeout(() => setSaveMsg(""), 2000);
      } else {
        setSaveMsg(`Error: ${result.error}`);
      }
    } catch {
      setSaveMsg("Failed to save");
    } finally {
      setSaving(false);
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
  const dynamicTags = Object.entries(tagCounts).sort((a, b) => b[1] - a[1]).slice(0, 15);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-[rgba(255,255,255,0.06)]">
        <div>
          <h1 className="text-xl font-bold text-white">Memory</h1>
          <p className="text-xs text-gray-500 mt-1">Your entire digital life, searchable</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex gap-1 bg-[rgba(255,255,255,0.03)] rounded-lg p-1 border border-[rgba(255,255,255,0.08)]">
            <button
              onClick={() => setViewMode("list")}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${viewMode === "list" ? "bg-[rgba(124,92,252,0.15)] text-[#a78bfa]" : "text-gray-500 hover:text-white"}`}
            >
              List
            </button>
            <button
              onClick={() => setViewMode("timeline")}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${viewMode === "timeline" ? "bg-[rgba(124,92,252,0.15)] text-[#a78bfa]" : "text-gray-500 hover:text-white"}`}
            >
              Timeline
            </button>
          </div>
          <span className="text-[10px] text-gray-600 ml-2">Press / to search</span>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="px-6 py-4 border-b border-[rgba(255,255,255,0.04)] bg-[rgba(255,255,255,0.02)]">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Icon name="search" className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
            <input
              ref={searchRef}
              type="text"
              placeholder="Search memories, chats, files, content... (results ranked by relevance)"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.08)] rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-indigo-500/50"
            />
          </div>
        </div>
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
        {dynamicTags.length > 0 && (
          <div className="flex items-center gap-2 mt-3 overflow-x-auto pb-1">
            <button
              onClick={() => setSelectedTag("")}
              className={`px-2.5 py-1 rounded text-[10px] font-medium whitespace-nowrap transition-all ${!selectedTag ? "bg-white/10 text-white" : "text-gray-600 hover:text-gray-400"}`}
            >
              All tags
            </button>
            {dynamicTags.map(([tag, count]) => (
              <button
                key={tag}
                onClick={() => setSelectedTag(selectedTag === tag ? "" : tag)}
                className={`px-2.5 py-1 rounded text-[10px] font-medium whitespace-nowrap transition-all ${
                  selectedTag === tag ? "bg-[rgba(124,92,252,0.15)] text-[#a78bfa]" : "text-gray-600 hover:text-gray-400"
                }`}
              >
                #{tag} <span className="opacity-50">{count}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-6">
        {viewMode === "timeline" ? (
          <TimelineView data={timelineData} onDateClick={(date) => { setSearch(date); setViewMode("list"); }} />
        ) : loading && items.length === 0 ? (
          <div className="text-center text-gray-500 py-12">Loading...</div>
        ) : items.length === 0 ? (
          <EmptyState search={search} selectedTag={selectedTag} selectedSource={selectedSource} onClear={() => { setSearch(""); setSelectedTag(""); setSelectedSource(""); }} />
        ) : (
          <div className="grid gap-3">
            {search && items[0]?.score !== undefined && (
              <div className="text-[10px] text-gray-600 mb-1">Ranked by relevance - best matches first</div>
            )}
            {items.map((item) => (
              <button
                key={item.id}
                onClick={() => fetchFullItem(item)}
                className="flex items-start gap-4 p-4 rounded-xl bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.04)] hover:border-[rgba(255,255,255,0.1)] transition-all text-left group"
              >
                <div className="text-2xl flex-shrink-0">{getTypeIcon(item.type)}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-white truncate">
                      {search ? highlightText(item.title, search) : item.title}
                    </span>
                    {item.score !== undefined && item.score > 0 && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-yellow-500/10 text-yellow-400 flex-shrink-0">
                        {item.score}pts
                      </span>
                    )}
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
                  <p className="text-xs text-gray-500 line-clamp-2 mb-2">
                    {search ? highlightText(item.content.slice(0, 200), search) : item.content.slice(0, 200)}
                  </p>
                  <div className="flex items-center gap-2">
                    {item.tags.slice(0, 4).map((tag) => (
                      <span key={tag} className="text-[10px] px-2 py-0.5 rounded bg-[rgba(255,255,255,0.05)] text-gray-500">#{tag}</span>
                    ))}
                    {item.tags.length > 4 && <span className="text-[10px] text-gray-600">+{item.tags.length - 4}</span>}
                    {item.fileSize && <span className="text-[10px] text-gray-600 ml-auto">{formatSize(item.fileSize)}</span>}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedItem && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => { setSelectedItem(null); setEditing(false); }}>
          <div className="bg-[#12121a] border border-[rgba(255,255,255,0.1)] rounded-xl w-full max-w-3xl max-h-[85vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
            {/* Modal header */}
            <div className="flex items-start justify-between p-6 border-b border-[rgba(255,255,255,0.06)] flex-shrink-0">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">{getTypeIcon(selectedItem.type)}</span>
                  <h2 className="text-lg font-semibold text-white truncate">{selectedItem.title}</h2>
                  {selectedItem.editable && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-green-500/10 text-green-500 flex-shrink-0">editable</span>
                  )}
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
              <div className="flex items-center gap-2 flex-shrink-0 ml-4">
                {selectedItem.editable && !editing && (
                  <button
                    onClick={() => { setEditing(true); setEditContent(selectedItem.fullContent || selectedItem.content); }}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white/5 border border-[rgba(255,255,255,0.08)] text-gray-400 hover:text-white hover:bg-white/10 transition-all"
                  >
                    <Icon name="edit" size={12} className="inline mr-1" />
                    Edit
                  </button>
                )}
                {editing && (
                  <>
                    <button
                      onClick={() => setEditing(false)}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium border border-[rgba(255,255,255,0.08)] text-gray-400 hover:text-white transition-all"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSave}
                      disabled={saving}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[rgba(124,92,252,0.15)] border border-indigo-500/30 text-indigo-400 hover:bg-[rgba(124,92,252,0.25)] transition-all disabled:opacity-50"
                    >
                      {saving ? "Saving..." : "Save"}
                    </button>
                  </>
                )}
                {saveMsg && <span className="text-xs text-green-400">{saveMsg}</span>}
                <button onClick={() => { setSelectedItem(null); setEditing(false); }} className="text-gray-500 hover:text-white">
                  <Icon name="close" size={20} />
                </button>
              </div>
            </div>

            {/* Modal content */}
            <div className="flex-1 overflow-y-auto p-6">
              {loadingDetail ? (
                <div className="text-center text-gray-500 py-8">Loading full content...</div>
              ) : editing ? (
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className="w-full h-full min-h-[400px] bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)] rounded-lg p-4 text-sm text-gray-300 font-mono leading-relaxed resize-none outline-none focus:border-indigo-500/50"
                  spellCheck={false}
                />
              ) : (
                <div className="prose prose-invert prose-sm max-w-none
                  prose-headings:text-white prose-headings:font-semibold prose-headings:border-b prose-headings:border-[rgba(255,255,255,0.06)] prose-headings:pb-2
                  prose-h1:text-lg prose-h2:text-base prose-h3:text-sm
                  prose-p:text-gray-300 prose-p:leading-relaxed
                  prose-a:text-indigo-400 prose-a:no-underline hover:prose-a:underline
                  prose-strong:text-white
                  prose-code:text-[#a78bfa] prose-code:bg-[rgba(124,92,252,0.1)] prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs
                  prose-pre:bg-[rgba(255,255,255,0.03)] prose-pre:border prose-pre:border-[rgba(255,255,255,0.08)] prose-pre:rounded-lg
                  prose-li:text-gray-400
                  prose-table:border-collapse
                  prose-th:text-left prose-th:text-gray-400 prose-th:border-b prose-th:border-[rgba(255,255,255,0.1)] prose-th:py-2 prose-th:px-3
                  prose-td:text-gray-300 prose-td:border-b prose-td:border-[rgba(255,255,255,0.04)] prose-td:py-2 prose-td:px-3
                  prose-blockquote:border-indigo-500/30 prose-blockquote:text-gray-400
                  prose-hr:border-[rgba(255,255,255,0.06)]
                ">
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
                    {selectedItem.fullContent || selectedItem.content}
                  </ReactMarkdown>
                </div>
              )}

              {/* Related Memories */}
              {!editing && selectedItem.related && selectedItem.related.length > 0 && (
                <div className="mt-8 pt-6 border-t border-[rgba(255,255,255,0.06)]">
                  <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                    <span>🔗</span> Related Memories
                  </h3>
                  <div className="grid gap-2">
                    {selectedItem.related.map((rel) => (
                      <button
                        key={rel.id}
                        onClick={() => fetchFullItem(rel)}
                        className="flex items-center gap-3 p-3 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.05)] hover:border-[rgba(255,255,255,0.1)] transition-all text-left"
                      >
                        <span className="text-lg">{getTypeIcon(rel.type)}</span>
                        <div className="flex-1 min-w-0">
                          <span className="text-xs font-medium text-white truncate block">{rel.title}</span>
                          <span className="text-[10px] text-gray-500">{formatDate(rel.date)} - {rel.source}</span>
                        </div>
                        <div className="flex gap-1">
                          {rel.tags.slice(0, 2).map((t) => (
                            <span key={t} className="text-[9px] px-1.5 py-0.5 rounded bg-[rgba(255,255,255,0.05)] text-gray-500">#{t}</span>
                          ))}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Modal footer */}
            <div className="px-6 py-4 border-t border-[rgba(255,255,255,0.06)] flex items-center gap-3 flex-shrink-0">
              <div className="flex items-center gap-2 flex-wrap flex-1">
                {selectedItem.tags.map((tag) => (
                  <span key={tag} className="text-xs px-2 py-1 rounded bg-[rgba(124,92,252,0.1)] text-[#a78bfa]">#{tag}</span>
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
            <span className="text-gray-500">{page} / {pages}</span>
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

// Timeline heatmap component
function TimelineView({ data, onDateClick }: { data: TimelineData; onDateClick: (date: string) => void }) {
  // Generate last 90 days
  const days = useMemo(() => {
    const result: Array<{ date: string; dayOfWeek: number; count: number; breakdown: TimelineData[string] | null }> = [];
    const today = new Date();
    for (let i = 89; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(today.getDate() - i);
      const dateStr = d.toISOString().split("T")[0];
      result.push({
        date: dateStr,
        dayOfWeek: d.getDay(),
        count: data[dateStr]?.total || 0,
        breakdown: data[dateStr] || null,
      });
    }
    return result;
  }, [data]);

  // Group by week for the grid
  const weeks = useMemo(() => {
    const result: typeof days[] = [];
    let currentWeek: typeof days = [];
    // Pad the first week
    if (days.length > 0) {
      for (let i = 0; i < days[0].dayOfWeek; i++) {
        currentWeek.push({ date: "", dayOfWeek: i, count: 0, breakdown: null });
      }
    }
    for (const day of days) {
      currentWeek.push(day);
      if (day.dayOfWeek === 6) {
        result.push(currentWeek);
        currentWeek = [];
      }
    }
    if (currentWeek.length > 0) result.push(currentWeek);
    return result;
  }, [days]);

  const maxCount = Math.max(...days.map((d) => d.count), 1);
  const totalItems = Object.values(data).reduce((sum, d) => sum + d.total, 0);
  const activeDays = Object.keys(data).length;

  const getColor = (count: number) => {
    if (count === 0) return "bg-[rgba(255,255,255,0.03)]";
    const intensity = count / maxCount;
    if (intensity < 0.25) return "bg-indigo-500/20";
    if (intensity < 0.5) return "bg-indigo-500/40";
    if (intensity < 0.75) return "bg-indigo-500/60";
    return "bg-indigo-500/80";
  };

  const dayLabels = ["Sun", "", "Tue", "", "Thu", "", "Sat"];

  return (
    <div>
      {/* Stats */}
      <div className="flex items-center gap-6 mb-6">
        <div className="text-center">
          <div className="text-2xl font-bold text-white">{totalItems}</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Total Items</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-white">{activeDays}</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Active Days</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-white">{activeDays > 0 ? Math.round(totalItems / activeDays) : 0}</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Avg / Day</div>
        </div>
      </div>

      {/* Heatmap */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-white mb-3">Last 90 Days</h3>
        <div className="flex gap-1">
          {/* Day labels */}
          <div className="flex flex-col gap-1 mr-1">
            {dayLabels.map((label, i) => (
              <div key={i} className="h-[14px] text-[9px] text-gray-600 flex items-center">{label}</div>
            ))}
          </div>
          {/* Week columns */}
          {weeks.map((week, wi) => (
            <div key={wi} className="flex flex-col gap-1">
              {week.map((day, di) => (
                <button
                  key={di}
                  onClick={() => day.date && day.count > 0 && onDateClick(day.date)}
                  disabled={!day.date || day.count === 0}
                  className={`w-[14px] h-[14px] rounded-sm ${getColor(day.count)} ${
                    day.date && day.count > 0 ? "cursor-pointer hover:ring-1 hover:ring-indigo-400/50" : ""
                  } transition-all`}
                  title={day.date ? `${day.date}: ${day.count} items` : ""}
                />
              ))}
            </div>
          ))}
        </div>
        {/* Legend */}
        <div className="flex items-center gap-2 mt-3 text-[10px] text-gray-600">
          <span>Less</span>
          <div className="w-[12px] h-[12px] rounded-sm bg-[rgba(255,255,255,0.03)]" />
          <div className="w-[12px] h-[12px] rounded-sm bg-indigo-500/20" />
          <div className="w-[12px] h-[12px] rounded-sm bg-indigo-500/40" />
          <div className="w-[12px] h-[12px] rounded-sm bg-indigo-500/60" />
          <div className="w-[12px] h-[12px] rounded-sm bg-indigo-500/80" />
          <span>More</span>
        </div>
      </div>

      {/* Daily breakdown for recent days */}
      <div>
        <h3 className="text-sm font-semibold text-white mb-3">Recent Activity</h3>
        <div className="grid gap-2">
          {days
            .filter((d) => d.count > 0)
            .reverse()
            .slice(0, 10)
            .map((day) => (
              <button
                key={day.date}
                onClick={() => onDateClick(day.date)}
                className="flex items-center gap-4 p-3 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.04)] transition-all text-left"
              >
                <span className="text-xs font-medium text-white w-24">{day.date}</span>
                <div className="flex-1 flex items-center gap-3">
                  {day.breakdown && day.breakdown.memory > 0 && (
                    <span className="text-[10px] text-indigo-400">📝 {day.breakdown.memory}</span>
                  )}
                  {day.breakdown && day.breakdown.content > 0 && (
                    <span className="text-[10px] text-purple-400">📰 {day.breakdown.content}</span>
                  )}
                  {day.breakdown && day.breakdown.files > 0 && (
                    <span className="text-[10px] text-amber-400">📎 {day.breakdown.files}</span>
                  )}
                  {day.breakdown && day.breakdown.chats > 0 && (
                    <span className="text-[10px] text-green-400">💬 {day.breakdown.chats}</span>
                  )}
                </div>
                <span className="text-xs text-gray-500">{day.count} items</span>
              </button>
            ))}
        </div>
      </div>
    </div>
  );
}

function EmptyState({ search, selectedTag, selectedSource, onClear }: {
  search: string; selectedTag: string; selectedSource: string; onClear: () => void;
}) {
  return (
    <div className="text-center text-gray-500 py-12">
      <div className="text-4xl mb-4">🧠</div>
      {search ? (
        <>
          <p>No results for &ldquo;{search}&rdquo;</p>
          <p className="text-xs mt-2">Try different keywords or clear filters</p>
          <button onClick={onClear} className="mt-4 px-4 py-2 rounded-lg text-xs bg-white/5 border border-[rgba(255,255,255,0.08)] text-gray-400 hover:text-white transition-all">
            Clear all filters
          </button>
        </>
      ) : selectedTag || selectedSource ? (
        <>
          <p>No items match this filter</p>
          <button onClick={onClear} className="mt-4 px-4 py-2 rounded-lg text-xs bg-white/5 border border-[rgba(255,255,255,0.08)] text-gray-400 hover:text-white transition-all">
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
  );
}
