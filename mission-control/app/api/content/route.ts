import { NextResponse } from "next/server";
import Database from "better-sqlite3";
import path from "path";

const DB_PATH = path.join(process.cwd(), "mission-control.db");
const db = new Database(DB_PATH);

export const dynamic = "force-dynamic";

// Create posts table
db.exec(`
  CREATE TABLE IF NOT EXISTS content_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    platform TEXT NOT NULL,
    contentType TEXT NOT NULL,
    status TEXT DEFAULT "Draft",
    assignee TEXT,
    priority TEXT,
    createdAt TEXT NOT NULL,
    updatedAt TEXT
  );
`);

export async function GET() {
  try {
    const posts = db.prepare("SELECT * FROM content_posts ORDER BY createdAt DESC").all();
    return NextResponse.json(posts);
  } catch (error) {
    console.error("Fetch error:", error);
    return NextResponse.json({ error: "Failed to fetch posts" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { title, content, platform, contentType, assignee, priority } = body;

    if (!title || !platform || !contentType) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    const now = new Date().toISOString();
    const result = db.prepare(`
      INSERT INTO content_posts (title, content, platform, contentType, status, assignee, priority, createdAt, updatedAt)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      title,
      content || "",
      platform,
      contentType,
      "Draft",
      assignee || "Ahmed",
      priority || "Medium",
      now,
      now
    );

    const post = db.prepare("SELECT * FROM content_posts WHERE id = ?").get(result.lastInsertRowid);

    return NextResponse.json(post, { status: 201 });
  } catch (error) {
    console.error("Create error:", error);
    return NextResponse.json({ error: "Failed to create post" }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  try {
    const body = await request.json();
    const { id, status, content, assignee, priority, title } = body;

    if (!id) {
      return NextResponse.json({ error: "ID required" }, { status: 400 });
    }

    const now = new Date().toISOString();
    
    // Check if post exists and get current status
    const existing = db.prepare("SELECT * FROM content_posts WHERE id = ?").get(id);
    if (!existing) {
      return NextResponse.json({ error: "Post not found" }, { status: 404 });
    }

    // Update post
    db.prepare(`
      UPDATE content_posts
      SET status = COALESCE(?, status),
          content = COALESCE(?, content),
          assignee = COALESCE(?, assignee),
          priority = COALESCE(?, priority),
          title = COALESCE(?, title),
          updatedAt = ?
      WHERE id = ?
    `).run(status, content, assignee, priority, title, now, id);

    const updated = db.prepare("SELECT * FROM content_posts WHERE id = ?").get(id);

    // Trigger posting if status changed to Published
    if (status === "Published" && existing.status !== "Published") {
      try {
        // Post to the appropriate platform
        if (updated.platform === "LinkedIn" || updated.platform === "Both") {
          await fetch("http://localhost:3001/api/content/linkedin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              content: updated.content,
              title: updated.title
            })
          });
        }
        
        if (updated.platform === "X" || updated.platform === "Both") {
          await fetch("http://localhost:3001/api/content/x", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              content: updated.content
            })
          });
        }
      } catch (e) {
        console.error("Posting error:", e);
      }
    }

    return NextResponse.json(updated);
  } catch (error) {
    console.error("Update error:", error);
    return NextResponse.json({ error: "Failed to update post" }, { status: 500 });
  }
}

export async function DELETE(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get("id");

    if (!id) {
      return NextResponse.json({ error: "ID required" }, { status: 400 });
    }

    db.prepare("DELETE FROM content_posts WHERE id = ?").run(id);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Delete error:", error);
    return NextResponse.json({ error: "Failed to delete post" }, { status: 500 });
  }
}

// Placeholder functions for actual posting (to be implemented)
/*
async function postToLinkedIn(content: string, title: string) {
  // Use LinkedIn API or browser automation
}

async function postToX(content: string) {
  // Use X API or browser automation
}
*/
