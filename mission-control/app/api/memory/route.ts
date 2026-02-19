import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const MEMORY_DIR = "/root/.openclaw/workspace/memory";
const WORKSPACE = "/root/.openclaw/workspace";

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

function getMemoryFiles(): MemoryItem[] {
  const items: MemoryItem[] = [];
  
  try {
    if (!fs.existsSync(MEMORY_DIR)) return items;
    
    const files = fs.readdirSync(MEMORY_DIR).filter(f => f.endsWith(".md"));
    
    for (const file of files) {
      const filePath = path.join(MEMORY_DIR, file);
      const content = fs.readFileSync(filePath, "utf-8");
      
      // Parse frontmatter
      let date = new Date().toISOString();
      let tags: string[] = [];
      let title = file.replace(".md", "");
      
      // Extract from content
      const lines = content.split("\n");
      for (const line of lines) {
        if (line.startsWith("## ")) {
          title = line.replace("## ", "").trim();
          break;
        }
      }
      
      // Extract tags if present
      const tagMatch = content.match(/#\w+/g);
      if (tagMatch) {
        tags = tagMatch.map(t => t.replace("#", ""));
      }
      
      items.push({
        id: file,
        type: "memory",
        title,
        content: content.slice(0, 500) + (content.length > 500 ? "..." : ""),
        date,
        tags,
        source: file,
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
    // Check for any downloaded/saved content
    const downloadsDir = path.join(WORKSPACE, "docs", "content-claw");
    if (fs.existsSync(downloadsDir)) {
      const caughtDir = path.join(downloadsDir, "caught");
      if (fs.existsSync(caughtDir)) {
        const files = fs.readdirSync(caughtDir);
        for (const file of files) {
          if (file.endsWith(".md") || file.endsWith(".txt")) {
            const filePath = path.join(caughtDir, file);
            const content = fs.readFileSync(filePath, "utf-8");
            
            items.push({
              id: file,
              type: file.includes("video") ? "video" : file.includes("link") ? "link" : "article",
              title: file.replace(/\.(md|txt)$/, "").slice(0, 50),
              content: content.slice(0, 300),
              date: new Date(fs.statSync(filePath).mtime).toISOString(),
              tags: ["content", "saved"],
              source: file,
            });
          }
        }
      }
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
    if (!fs.existsSync(inboundDir)) return items;
    
    const files = fs.readdirSync(inboundDir);
    for (const file of files) {
      const filePath = path.join(inboundDir, file);
      const stats = fs.statSync(filePath);
      
      // Categorize by extension
      let type: MemoryItem["type"] = "file";
      if (file.match(/\.(jpg|jpeg|png|gif|webp)$/i)) type = "image";
      else if (file.match(/\.(pdf)$/i)) type = "file";
      else if (file.match(/\.(docx?|txt)$/i)) type = "document";
      else continue;
      
      items.push({
        id: file,
        type,
        title: file,
        content: `File received: ${file} (${Math.round(stats.size / 1024)} KB)`,
        date: stats.mtime.toISOString(),
        tags: ["inbound", "file"],
        source: "telegram",
      });
    }
  } catch (e) {
    console.error("Error reading inbound:", e);
  }
  
  return items;
}

function getChatSessions(): MemoryItem[] {
  const items: MemoryItem[] = [];
  
  try {
    const sessionsDir = "/root/.openclaw/agents/main/sessions";
    if (!fs.existsSync(sessionsDir)) return items;
    
    const files = fs.readdirSync(sessionsDir).filter(f => f.endsWith(".jsonl"));
    
    for (const file of files) {
      const filePath = path.join(sessionsDir, file);
      const content = fs.readFileSync(filePath, "utf-8");
      const stats = fs.statSync(filePath);
      
      // Parse JSONL and extract messages
      const lines = content.split("\n").filter(Boolean);
      let messages: string[] = [];
      
      for (const line of lines) {
        try {
          const msg = JSON.parse(line);
          if (msg.role === "user" && msg.content) {
            messages.push(`Ahmed: ${msg.content.slice(0, 100)}`);
          }
          if (msg.role === "assistant" && msg.content) {
            messages.push(`NASR: ${msg.content.slice(0, 100)}`);
          }
        } catch {}
      }
      
      const chatContent = messages.join("\n").slice(0, 500);
      const dateStr = stats.mtime.toISOString();
      
      items.push({
        id: file,
        type: "chat",
        title: `Chat - ${file.slice(0, 16)}`,
        content: chatContent || "Chat session",
        date: dateStr,
        tags: ["chat", "session", "conversation"],
        source: "telegram",
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
    
    let items: MemoryItem[] = [];
    
    // Get all sources
    items = [
      ...getMemoryFiles(),
      ...getSharedContent(),
      ...getInboundFiles(),
      ...getChatSessions(),
    ];
    
    // Filter by tag
    if (tag) {
      items = items.filter(item => 
        item.tags.some(t => t.toLowerCase().includes(tag.toLowerCase()))
      );
    }
    
    // Filter by search query
    if (query) {
      items = items.filter(item =>
        item.title.toLowerCase().includes(query) ||
        item.content.toLowerCase().includes(query) ||
        item.tags.some(t => t.toLowerCase().includes(query))
      );
    }
    
    // Sort by date
    items.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    
    return NextResponse.json(items);
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch memories" }, { status: 500 });
  }
}
