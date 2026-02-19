import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const MEMORY_DIR = "/root/.openclaw/workspace/memory";
const WORKSPACE = "/root/.openclaw/workspace";

export const dynamic = "force-dynamic";

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
}

// Extract H1 title from markdown content
function extractTitle(content: string, fallbackFilename: string): string {
  const lines = content.split("\n");
  for (const line of lines) {
    const h1 = line.match(/^# (.+)/);
    if (h1) return h1[1].trim();
  }
  for (const line of lines) {
    const h2 = line.match(/^## (.+)/);
    if (h2) return h2[1].trim();
  }
  return fallbackFilename
    .replace(/\.(md|txt|json)$/, "")
    .replace(/[-_]/g, " ")
    .replace(/^\d{4}-\d{2}-\d{2}\s*/, "");
}

// Extract tags from content - exclude markdown headers
function extractTags(content: string): string[] {
  const tags = new Set<string>();
  const lines = content.split("\n");
  for (const line of lines) {
    if (line.match(/^#{1,6}\s/)) continue;
    const matches = line.match(/(?:^|\s)#(\w+)/g);
    if (matches) {
      for (const m of matches) {
        const tag = m.trim().replace("#", "").toLowerCase();
        if (tag.length > 1 && tag.length < 30) tags.add(tag);
      }
    }
  }
  return Array.from(tags);
}

function preview(content: string, maxLen = 500): string {
  if (content.length <= maxLen) return content;
  return content.slice(0, maxLen) + "...";
}

// Search relevance scoring
function scoreItem(item: MemoryItem, query: string): number {
  if (!query) return 0;
  const q = query.toLowerCase();
  const terms = q.split(/\s+/).filter(Boolean);
  let score = 0;

  for (const term of terms) {
    const titleLower = item.title.toLowerCase();
    const contentLower = (item.fullContent || item.content).toLowerCase();

    // Title exact match (highest)
    if (titleLower === q) score += 100;
    // Title contains term
    else if (titleLower.includes(term)) score += 50;

    // Tag exact match
    if (item.tags.some((t) => t === term)) score += 30;

    // Content match - count occurrences (capped)
    const contentMatches = contentLower.split(term).length - 1;
    score += Math.min(contentMatches * 3, 30);

    // Source/filename match
    if (item.source.toLowerCase().includes(term)) score += 15;
  }

  // Recency boost (items from last 7 days get a small boost)
  const ageMs = Date.now() - new Date(item.date).getTime();
  const ageDays = ageMs / (1000 * 60 * 60 * 24);
  if (ageDays < 1) score += 10;
  else if (ageDays < 7) score += 5;

  return score;
}

// Find related items based on shared tags and content overlap
function findRelated(target: MemoryItem, allItems: MemoryItem[], maxResults = 5): string[] {
  const scores: Array<{ id: string; score: number }> = [];

  for (const item of allItems) {
    if (item.id === target.id) continue;
    let score = 0;

    // Shared tags
    for (const tag of target.tags) {
      if (item.tags.includes(tag)) score += 10;
    }

    // Same source category
    if (item.sourceCategory === target.sourceCategory) score += 3;

    // Title word overlap
    const targetWords = new Set(target.title.toLowerCase().split(/\s+/));
    const itemWords = item.title.toLowerCase().split(/\s+/);
    for (const w of itemWords) {
      if (w.length > 3 && targetWords.has(w)) score += 8;
    }

    // Content keyword overlap (sample first 200 chars)
    const targetSample = (target.fullContent || target.content).toLowerCase().slice(0, 500);
    const itemSample = (item.fullContent || item.content).toLowerCase().slice(0, 500);
    const keywords = extractKeywords(targetSample);
    for (const kw of keywords) {
      if (itemSample.includes(kw)) score += 5;
    }

    // Close in time (within 2 days)
    const timeDiff = Math.abs(new Date(target.date).getTime() - new Date(item.date).getTime());
    if (timeDiff < 2 * 24 * 60 * 60 * 1000) score += 4;

    if (score > 5) scores.push({ id: item.id, score });
  }

  return scores
    .sort((a, b) => b.score - a.score)
    .slice(0, maxResults)
    .map((s) => s.id);
}

// Extract meaningful keywords from text
function extractKeywords(text: string): string[] {
  const stopWords = new Set(["the", "and", "for", "are", "but", "not", "you", "all", "can", "had", "her", "was", "one", "our", "out", "has", "have", "from", "this", "that", "with", "they", "been", "said", "each", "which", "their", "will", "other", "about", "many", "then", "them", "these", "some", "would", "make", "like", "into", "time", "very", "when", "come", "could", "more", "than", "first", "also", "made"]);
  const words = text.match(/\b[a-z]{4,}\b/g) || [];
  const freq: Record<string, number> = {};
  for (const w of words) {
    if (!stopWords.has(w)) freq[w] = (freq[w] || 0) + 1;
  }
  return Object.entries(freq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([w]) => w);
}

// ---- Data loading functions (unchanged logic, condensed) ----

function getMemoryFiles(): MemoryItem[] {
  const items: MemoryItem[] = [];
  try {
    if (!fs.existsSync(MEMORY_DIR)) return items;
    const files = fs.readdirSync(MEMORY_DIR).filter((f) => f.endsWith(".md"));
    for (const file of files) {
      const filePath = path.join(MEMORY_DIR, file);
      const content = fs.readFileSync(filePath, "utf-8");
      const stats = fs.statSync(filePath);
      const tags = extractTags(content);
      if (file.match(/^\d{4}-\d{2}-\d{2}/)) tags.push("daily");
      if (file.includes("lesson")) tags.push("lessons");
      if (file.includes("active-task")) tags.push("tasks");
      if (file.includes("cv") || file.includes("resume")) tags.push("cv");
      if (file.includes("preference")) tags.push("preferences");
      items.push({
        id: `mem-${file}`, type: "memory", title: extractTitle(content, file),
        content: preview(content), fullContent: content,
        date: stats.mtime.toISOString(), tags: Array.from(new Set(tags)),
        source: file, sourceCategory: "memory", filePath, fileSize: stats.size,
        editable: true,
      });
    }
    const rootFiles = ["MEMORY.md", "TOOLS.md", "IDENTITY.md", "USER.md", "SOUL.md", "AGENTS.md"];
    for (const file of rootFiles) {
      const filePath = path.join(WORKSPACE, file);
      if (!fs.existsSync(filePath)) continue;
      const content = fs.readFileSync(filePath, "utf-8");
      const stats = fs.statSync(filePath);
      items.push({
        id: `root-${file}`, type: "memory", title: extractTitle(content, file),
        content: preview(content), fullContent: content,
        date: stats.mtime.toISOString(), tags: ["core", file.replace(".md", "").toLowerCase()],
        source: file, sourceCategory: "memory", filePath, fileSize: stats.size,
        editable: true,
      });
    }
  } catch (e) { console.error("Error reading memory:", e); }
  return items;
}

function getSharedContent(): MemoryItem[] {
  const items: MemoryItem[] = [];
  try {
    const caughtDir = path.join(WORKSPACE, "docs", "content-claw", "caught");
    if (!fs.existsSync(caughtDir)) return items;
    for (const file of fs.readdirSync(caughtDir)) {
      if (!file.endsWith(".md") && !file.endsWith(".txt")) continue;
      const filePath = path.join(caughtDir, file);
      const content = fs.readFileSync(filePath, "utf-8");
      const stats = fs.statSync(filePath);
      const isVideo = content.toLowerCase().includes("youtube") || content.toLowerCase().includes("video");
      items.push({
        id: `content-${file}`, type: isVideo ? "video" : "article",
        title: extractTitle(content, file), content: preview(content, 300), fullContent: content,
        date: stats.mtime.toISOString(), tags: ["content", "saved"],
        source: file, sourceCategory: "content", filePath, fileSize: stats.size,
        editable: true,
      });
    }
  } catch (e) { console.error("Error reading content:", e); }
  return items;
}

function getInboundFromDir(dir: string): MemoryItem[] {
  const items: MemoryItem[] = [];
  for (const file of fs.readdirSync(dir)) {
    const filePath = path.join(dir, file);
    const stats = fs.statSync(filePath);
    if (stats.isDirectory()) continue;
    let type: MemoryItem["type"] = "file";
    const ext = path.extname(file).toLowerCase();
    if ([".jpg", ".jpeg", ".png", ".gif", ".webp"].includes(ext)) type = "image";
    else if (ext === ".pdf") type = "document";
    else if ([".doc", ".docx", ".txt", ".rtf"].includes(ext)) type = "document";
    else if ([".json", ".csv", ".xlsx", ".xls"].includes(ext)) type = "file";
    else if ([".mp4", ".mov", ".avi", ".webm"].includes(ext)) type = "video";
    const sizeKB = Math.round(stats.size / 1024);
    const sizeMB = (stats.size / (1024 * 1024)).toFixed(1);
    const sizeStr = stats.size > 1024 * 1024 ? `${sizeMB} MB` : `${sizeKB} KB`;
    items.push({
      id: `file-${file}`, type,
      title: file.replace(/^file_\d+---/, "").replace(/[-_]/g, " ").replace(/\.[^.]+$/, "") || file,
      content: `${type.charAt(0).toUpperCase() + type.slice(1)} file (${sizeStr})`,
      date: stats.mtime.toISOString(), tags: ["inbound", type],
      source: file, sourceCategory: "files", filePath, fileSize: stats.size,
    });
  }
  return items;
}

function getInboundFiles(): MemoryItem[] {
  try {
    const dir = path.join(WORKSPACE, "media", "inbound");
    if (fs.existsSync(dir)) return getInboundFromDir(dir);
    const alt = "/root/.openclaw/media/inbound";
    if (fs.existsSync(alt)) return getInboundFromDir(alt);
  } catch (e) { console.error("Error reading inbound:", e); }
  return [];
}

function getChatSessions(): MemoryItem[] {
  const items: MemoryItem[] = [];
  try {
    const sessionsDir = "/root/.openclaw/agents/main/sessions";
    if (!fs.existsSync(sessionsDir)) return items;
    const files = fs.readdirSync(sessionsDir).filter((f) => f.endsWith(".jsonl"));
    const sortedFiles = files
      .map((f) => ({ name: f, mtime: fs.statSync(path.join(sessionsDir, f)).mtimeMs }))
      .sort((a, b) => b.mtime - a.mtime)
      .slice(0, 20);
    for (const { name: file } of sortedFiles) {
      const filePath = path.join(sessionsDir, file);
      const stats = fs.statSync(filePath);
      const fd = fs.openSync(filePath, "r");
      const buf = Buffer.alloc(Math.min(stats.size, 50 * 1024));
      fs.readSync(fd, buf, 0, buf.length, 0);
      fs.closeSync(fd);
      const content = buf.toString("utf-8");
      const lines = content.split("\n").filter(Boolean);
      const messages: string[] = [];
      for (const line of lines) {
        try {
          const msg = JSON.parse(line);
          if (msg.role === "user" && msg.content)
            messages.push(`Ahmed: ${typeof msg.content === "string" ? msg.content.slice(0, 80) : "[complex]"}`);
          if (msg.role === "assistant" && msg.content)
            messages.push(`NASR: ${typeof msg.content === "string" ? msg.content.slice(0, 80) : "[complex]"}`);
        } catch {}
      }
      const sessionDate = new Date(stats.mtime).toLocaleDateString("en-US", {
        month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "Africa/Cairo",
      });
      items.push({
        id: `chat-${file}`, type: "chat",
        title: `Chat Session - ${sessionDate}`,
        content: messages.slice(0, 10).join("\n") || "Empty session",
        fullContent: messages.join("\n"),
        date: stats.mtime.toISOString(), tags: ["chat", "session"],
        source: file, sourceCategory: "chats", filePath, fileSize: stats.size,
      });
    }
  } catch (e) { console.error("Error reading chat sessions:", e); }
  return items;
}

// Collect all items (cached per request)
function getAllItems(): MemoryItem[] {
  return [
    ...getMemoryFiles(),
    ...getSharedContent(),
    ...getInboundFiles(),
    ...getChatSessions(),
  ];
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get("q")?.toLowerCase() || "";
    const tag = searchParams.get("tag") || "";
    const source = searchParams.get("source") || "";
    const pageNum = parseInt(searchParams.get("page") || "1", 10);
    const limit = parseInt(searchParams.get("limit") || "50", 10);
    const itemId = searchParams.get("id") || "";
    const related = searchParams.get("related") === "true";
    const timeline = searchParams.get("timeline") === "true";

    const allItems = getAllItems();

    // Single item fetch with optional related items
    if (itemId) {
      const item = allItems.find((i) => i.id === itemId);
      if (!item) return NextResponse.json({ error: "Not found" }, { status: 404 });
      const result: any = { ...item };
      if (related) {
        const relatedIds = findRelated(item, allItems);
        result.related = allItems
          .filter((i) => relatedIds.includes(i.id))
          .map(({ fullContent, ...rest }) => rest);
      }
      return NextResponse.json(result);
    }

    // Timeline data - return date counts for the heatmap
    if (timeline) {
      const counts: Record<string, { total: number; memory: number; content: number; files: number; chats: number }> = {};
      for (const item of allItems) {
        const dateKey = item.date.split("T")[0];
        if (!counts[dateKey]) counts[dateKey] = { total: 0, memory: 0, content: 0, files: 0, chats: 0 };
        counts[dateKey].total++;
        counts[dateKey][item.sourceCategory]++;
      }
      return NextResponse.json(counts);
    }

    let items = allItems;

    // Filter by source category
    if (source) items = items.filter((i) => i.sourceCategory === source);
    // Filter by tag
    if (tag) items = items.filter((i) => i.tags.some((t) => t.toLowerCase() === tag.toLowerCase()));

    // Filter + rank by search query
    if (query) {
      items = items
        .map((item) => ({ ...item, score: scoreItem(item, query) }))
        .filter((item) => item.score > 0)
        .sort((a, b) => (b.score || 0) - (a.score || 0));
    } else {
      // Default: sort by date descending
      items.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    }

    // Compute tag counts
    const tagCounts: Record<string, number> = {};
    for (const item of items) {
      for (const t of item.tags) tagCounts[t] = (tagCounts[t] || 0) + 1;
    }
    const sourceCounts: Record<string, number> = {};
    for (const item of items) {
      sourceCounts[item.sourceCategory] = (sourceCounts[item.sourceCategory] || 0) + 1;
    }

    const total = items.length;
    const start = (pageNum - 1) * limit;
    const paged = items.slice(start, start + limit);
    const stripped = paged.map(({ fullContent, ...rest }) => rest);

    return NextResponse.json({
      items: stripped,
      total, page: pageNum, limit,
      pages: Math.ceil(total / limit),
      tagCounts, sourceCounts,
    });
  } catch (error) {
    console.error("Memory API error:", error);
    return NextResponse.json({ error: "Failed to fetch memories" }, { status: 500 });
  }
}

// PUT - Save/edit a memory file
export async function PUT(request: Request) {
  try {
    const body = await request.json();
    const { id, content } = body;

    if (!id || typeof content !== "string") {
      return NextResponse.json({ error: "Missing id or content" }, { status: 400 });
    }

    // Resolve file path from id
    let filePath: string | null = null;

    if (id.startsWith("root-")) {
      const filename = id.replace("root-", "");
      filePath = path.join(WORKSPACE, filename);
    } else if (id.startsWith("mem-")) {
      const filename = id.replace("mem-", "");
      filePath = path.join(MEMORY_DIR, filename);
    } else if (id.startsWith("content-")) {
      const filename = id.replace("content-", "");
      filePath = path.join(WORKSPACE, "docs", "content-claw", "caught", filename);
    }

    if (!filePath || !fs.existsSync(filePath)) {
      return NextResponse.json({ error: "File not found or not editable" }, { status: 404 });
    }

    // Safety: only allow editing .md and .txt files
    if (!filePath.endsWith(".md") && !filePath.endsWith(".txt")) {
      return NextResponse.json({ error: "Only markdown/text files can be edited" }, { status: 403 });
    }

    fs.writeFileSync(filePath, content, "utf-8");

    return NextResponse.json({ success: true, filePath });
  } catch (error) {
    console.error("Memory save error:", error);
    return NextResponse.json({ error: "Failed to save" }, { status: 500 });
  }
}
