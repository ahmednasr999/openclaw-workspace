import { NextResponse } from "next/server";
import Database from "better-sqlite3";
import path from "path";

const DB_PATH = path.join(process.cwd(), "mission-control.db");
const db = new Database(DB_PATH);

// Create knowledge table
db.exec(`
  CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,
    source TEXT,
    author TEXT DEFAULT "Agent",
    createdAt TEXT NOT NULL,
    updatedAt TEXT
  );
`);

export const dynamic = "force-dynamic";

// Query knowledge base
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get("q") || "";
    const category = searchParams.get("category");

    let sql = "SELECT * FROM knowledge WHERE 1=1";
    const params: string[] = [];

    if (category) {
      sql += " AND category = ?";
      params.push(category);
    }

    if (query) {
      sql += " AND (title LIKE ? OR content LIKE ? OR tags LIKE ?)";
      const searchTerm = `%${query}%`;
      params.push(searchTerm, searchTerm, searchTerm);
    }

    sql += " ORDER BY createdAt DESC LIMIT 50";

    const results = db.prepare(sql).all(...params);

    return NextResponse.json({
      query,
      category,
      resultCount: results.length,
      knowledge: results.map((r: any) => ({
        ...r,
        tags: r.tags ? JSON.parse(r.tags) : []
      }))
    });
  } catch (error) {
    console.error("Knowledge query error:", error);
    return NextResponse.json({ error: "Failed to query knowledge" }, { status: 500 });
  }
}

// Add to knowledge base
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { category, title, content, tags, source, author } = body;

    if (!category || !title || !content) {
      return NextResponse.json({ error: "category, title, and content required" }, { status: 400 });
    }

    const now = new Date().toISOString();
    const result = db.prepare(`
      INSERT INTO knowledge (category, title, content, tags, source, author, createdAt, updatedAt)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      category,
      title,
      content,
      JSON.stringify(tags || []),
      source || "",
      author || "Agent",
      now,
      now
    );

    const entry = db.prepare("SELECT * FROM knowledge WHERE id = ?").get(result.lastInsertRowid);

    return NextResponse.json({
      success: true,
      entry: {
        ...entry,
        tags: entry.tags ? JSON.parse(entry.tags) : []
      },
      message: "Knowledge added"
    });
  } catch (error) {
    console.error("Knowledge add error:", error);
    return NextResponse.json({ error: "Failed to add knowledge" }, { status: 500 });
  }
}
