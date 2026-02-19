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
}

// Extract H1 title from markdown content
function extractTitle(content: string, fallbackFilename: string): string {
  const lines = content.split("\n");
  for (const line of lines) {
    // Match # Title but not ## or ###
    const h1 = line.match(/^# (.+)/);
    if (h1) return h1[1].trim();
  }
  // Fallback: first ## header
  for (const line of lines) {
    const h2 = line.match(/^## (.+)/);
    if (h2) return h2[1].trim();
  }
  // Clean filename fallback
  return fallbackFilename
    .replace(/\.(md|txt|json)$/, "")
    .replace(/[-_]/g, " ")
    .replace(/^\d{4}-\d{2}-\d{2}\s*/, ""); // Strip leading date
}

// Extract tags from content - exclude markdown headers
function extractTags(content: string): string[] {
  const tags = new Set<string>();
  const lines = content.split("\n");
  for (const line of lines) {
    // Skip markdown headers
    if (line.match(/^#{1,6}\s/)) continue;
    // Match #word tags in body text
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

// Truncate content for preview
function preview(content: string, maxLen = 500): string {
  if (content.length <= maxLen) return content;
  return content.slice(0, maxLen) + "...";
}

function getMemoryFiles(): MemoryItem[] {
  const items: MemoryItem[] = [];

  try {
    if (!fs.existsSync(MEMORY_DIR)) return items;

    const files = fs.readdirSync(MEMORY_DIR).filter((f) => f.endsWith(".md"));

    for (const file of files) {
      const filePath = path.join(MEMORY_DIR, file);
      const content = fs.readFileSync(filePath, "utf-8");
      const stats = fs.statSync(filePath);

      const title = extractTitle(content, file);
      const tags = extractTags(content);

      // Auto-tag based on filename patterns
      if (file.match(/^\d{4}-\d{2}-\d{2}/)) tags.push("daily");
      if (file.includes("lesson")) tags.push("lessons");
      if (file.includes("active-task")) tags.push("tasks");
      if (file.includes("cv") || file.includes("resume")) tags.push("cv");
      if (file.includes("preference")) tags.push("preferences");

      items.push({
        id: `mem-${file}`,
        type: "memory",
        title,
        content: preview(content),
        fullContent: content,
        date: stats.mtime.toISOString(),
        tags: Array.from(new Set(tags)),
        source: file,
        sourceCategory: "memory",
        filePath,
        fileSize: stats.size,
      });
    }

    // Also include root workspace .md files (MEMORY.md, TOOLS.md, etc.)
    const rootFiles = ["MEMORY.md", "TOOLS.md", "IDENTITY.md", "USER.md", "SOUL.md", "AGENTS.md"];
    for (const file of rootFiles) {
      const filePath = path.join(WORKSPACE, file);
      if (!fs.existsSync(filePath)) continue;
      const content = fs.readFileSync(filePath, "utf-8");
      const stats = fs.statSync(filePath);

      items.push({
        id: `root-${file}`,
        type: "memory",
        title: extractTitle(content, file),
        content: preview(content),
        fullContent: content,
        date: stats.mtime.toISOString(),
        tags: ["core", file.replace(".md", "").toLowerCase()],
        source: file,
        sourceCategory: "memory",
        filePath,
        fileSize: stats.size,
      });
    }
  } catch (e) {
    console.error("Error reading memory:", e);
  }

  return items;
}

function getSharedContent(): MemoryItem[] {
  const items: MemoryItem[] = [];

  try {
    const caughtDir = path.join(WORKSPACE, "docs", "content-claw", "caught");
    if (!fs.existsSync(caughtDir)) return items;

    const files = fs.readdirSync(caughtDir);
    for (const file of files) {
      if (!file.endsWith(".md") && !file.endsWith(".txt")) continue;
      const filePath = path.join(caughtDir, file);
      const content = fs.readFileSync(filePath, "utf-8");
      const stats = fs.statSync(filePath);

      const title = extractTitle(content, file);
      const isVideo = content.toLowerCase().includes("youtube") || content.toLowerCase().includes("video");

      items.push({
        id: `content-${file}`,
        type: isVideo ? "video" : "article",
        title,
        content: preview(content, 300),
        fullContent: content,
        date: stats.mtime.toISOString(),
        tags: ["content", "saved"],
        source: file,
        sourceCategory: "content",
        filePath,
        fileSize: stats.size,
      });
    }
  } catch (e) {
    console.error("Error reading content:", e);
  }

  return items;
}

function getInboundFiles(): MemoryItem[] {
  const items: MemoryItem[] = [];

  try {
    const inboundDir = path.join(WORKSPACE, "media", "inbound");
    if (!fs.existsSync(inboundDir)) {
      // Try alternate path
      const altDir = "/root/.openclaw/media/inbound";
      if (!fs.existsSync(altDir)) return items;
      return getInboundFromDir(altDir);
    }
    return getInboundFromDir(inboundDir);
  } catch (e) {
    console.error("Error reading inbound:", e);
  }

  return items;
}

function getInboundFromDir(dir: string): MemoryItem[] {
  const items: MemoryItem[] = [];
  const files = fs.readdirSync(dir);

  for (const file of files) {
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
    // Don't skip unknown types - show them as generic files

    const sizeKB = Math.round(stats.size / 1024);
    const sizeMB = (stats.size / (1024 * 1024)).toFixed(1);
    const sizeStr = stats.size > 1024 * 1024 ? `${sizeMB} MB` : `${sizeKB} KB`;

    items.push({
      id: `file-${file}`,
      type,
      title: file.replace(/^file_\d+---/, "").replace(/[-_]/g, " ").replace(/\.[^.]+$/, "") || file,
      content: `${type.charAt(0).toUpperCase() + type.slice(1)} file (${sizeStr})`,
      date: stats.mtime.toISOString(),
      tags: ["inbound", type],
      source: file,
      sourceCategory: "files",
      filePath,
      fileSize: stats.size,
    });
  }

  return items;
}

function getChatSessions(): MemoryItem[] {
  const items: MemoryItem[] = [];

  try {
    const sessionsDir = "/root/.openclaw/agents/main/sessions";
    if (!fs.existsSync(sessionsDir)) return items;

    const files = fs.readdirSync(sessionsDir).filter((f) => f.endsWith(".jsonl"));

    // Only process the 20 most recent session files to avoid slowness
    const sortedFiles = files
      .map((f) => ({ name: f, mtime: fs.statSync(path.join(sessionsDir, f)).mtimeMs }))
      .sort((a, b) => b.mtime - a.mtime)
      .slice(0, 20);

    for (const { name: file } of sortedFiles) {
      const filePath = path.join(sessionsDir, file);
      const stats = fs.statSync(filePath);

      // Read only first 50KB to avoid memory issues on large sessions
      const fd = fs.openSync(filePath, "r");
      const buf = Buffer.alloc(Math.min(stats.size, 50 * 1024));
      fs.readSync(fd, buf, 0, buf.length, 0);
      fs.closeSync(fd);
      const content = buf.toString("utf-8");

      const lines = content.split("\n").filter(Boolean);
      const messages: string[] = [];
      let userCount = 0;
      let assistantCount = 0;

      for (const line of lines) {
        try {
          const msg = JSON.parse(line);
          if (msg.role === "user" && msg.content) {
            messages.push(`Ahmed: ${typeof msg.content === "string" ? msg.content.slice(0, 80) : "[complex]"}`);
            userCount++;
          }
          if (msg.role === "assistant" && msg.content) {
            messages.push(`NASR: ${typeof msg.content === "string" ? msg.content.slice(0, 80) : "[complex]"}`);
            assistantCount++;
          }
        } catch {
          // Skip malformed lines
        }
      }

      const chatPreview = messages.slice(0, 10).join("\n");
      const dateStr = stats.mtime.toISOString();
      const sessionDate = new Date(stats.mtime).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Africa/Cairo",
      });

      items.push({
        id: `chat-${file}`,
        type: "chat",
        title: `Chat Session - ${sessionDate}`,
        content: chatPreview || "Empty session",
        fullContent: messages.join("\n"),
        date: dateStr,
        tags: ["chat", "session"],
        source: file,
        sourceCategory: "chats",
        filePath,
        fileSize: stats.size,
      });
    }
  } catch (e) {
    console.error("Error reading chat sessions:", e);
  }

  return items;
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get("q")?.toLowerCase() || "";
    const tag = searchParams.get("tag") || "";
    const source = searchParams.get("source") || "";
    const page = parseInt(searchParams.get("page") || "1", 10);
    const limit = parseInt(searchParams.get("limit") || "50", 10);
    const itemId = searchParams.get("id") || "";

    // Single item fetch (for full content on modal open)
    if (itemId) {
      const allItems = [
        ...getMemoryFiles(),
        ...getSharedContent(),
        ...getInboundFiles(),
        ...getChatSessions(),
      ];
      const item = allItems.find((i) => i.id === itemId);
      if (item) return NextResponse.json(item);
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    let items: MemoryItem[] = [
      ...getMemoryFiles(),
      ...getSharedContent(),
      ...getInboundFiles(),
      ...getChatSessions(),
    ];

    // Filter by source category
    if (source) {
      items = items.filter((item) => item.sourceCategory === source);
    }

    // Filter by tag
    if (tag) {
      items = items.filter((item) =>
        item.tags.some((t) => t.toLowerCase() === tag.toLowerCase())
      );
    }

    // Filter by search query
    if (query) {
      items = items.filter(
        (item) =>
          item.title.toLowerCase().includes(query) ||
          item.content.toLowerCase().includes(query) ||
          item.tags.some((t) => t.toLowerCase().includes(query))
      );
    }

    // Sort by date descending
    items.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

    // Compute tag counts before pagination
    const tagCounts: Record<string, number> = {};
    for (const item of items) {
      for (const t of item.tags) {
        tagCounts[t] = (tagCounts[t] || 0) + 1;
      }
    }

    // Source counts
    const sourceCounts: Record<string, number> = {};
    for (const item of items) {
      sourceCounts[item.sourceCategory] = (sourceCounts[item.sourceCategory] || 0) + 1;
    }

    const total = items.length;
    const start = (page - 1) * limit;
    const paged = items.slice(start, start + limit);

    // Strip fullContent from list responses to keep payload small
    const stripped = paged.map(({ fullContent, ...rest }) => rest);

    return NextResponse.json({
      items: stripped,
      total,
      page,
      limit,
      pages: Math.ceil(total / limit),
      tagCounts,
      sourceCounts,
    });
  } catch (error) {
    console.error("Memory API error:", error);
    return NextResponse.json({ error: "Failed to fetch memories" }, { status: 500 });
  }
}
