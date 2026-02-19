import Database from "better-sqlite3";
import path from "path";

const DB_PATH = path.join(process.cwd(), "mission-control.db");
const db = new Database(DB_PATH);

// Enable WAL mode for better concurrent reads
db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");

// Create tables
db.exec(`
  CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    assignee TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Inbox',
    priority TEXT NOT NULL DEFAULT 'Medium',
    category TEXT NOT NULL DEFAULT 'Job Search',
    dueDate TEXT,
    completedDate TEXT,
    relatedTo TEXT,
    createdAt TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS task_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taskId INTEGER NOT NULL,
    type TEXT NOT NULL,
    content TEXT,
    author TEXT NOT NULL DEFAULT 'System',
    createdAt TEXT NOT NULL,
    FOREIGN KEY (taskId) REFERENCES tasks(id) ON DELETE CASCADE
  );

  CREATE TABLE IF NOT EXISTS subtasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taskId INTEGER NOT NULL,
    title TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    createdAt TEXT NOT NULL,
    FOREIGN KEY (taskId) REFERENCES tasks(id) ON DELETE CASCADE
  );
`);

// Create content_posts table
db.exec(`
  CREATE TABLE IF NOT EXISTS content_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    hook TEXT,
    body TEXT,
    platform TEXT NOT NULL DEFAULT 'LinkedIn',
    contentType TEXT NOT NULL DEFAULT 'Post',
    status TEXT NOT NULL DEFAULT 'Ideas',
    hashtags TEXT,
    imageUrl TEXT,
    publishDate TEXT,
    assignee TEXT NOT NULL DEFAULT 'Both',
    priority TEXT NOT NULL DEFAULT 'Medium',
    createdAt TEXT NOT NULL,
    updatedAt TEXT
  );

  CREATE TABLE IF NOT EXISTS content_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    postId INTEGER NOT NULL,
    type TEXT NOT NULL,
    content TEXT,
    author TEXT NOT NULL DEFAULT 'System',
    createdAt TEXT NOT NULL,
    FOREIGN KEY (postId) REFERENCES content_posts(id) ON DELETE CASCADE
  );
`);

export const sqliteDb = {
  // ---- TASKS ----
  getAllTasks: () => {
    const tasks = db.prepare("SELECT * FROM tasks ORDER BY createdAt DESC").all() as any[];
    // Attach subtask counts
    const subtaskStmt = db.prepare("SELECT taskId, COUNT(*) as total, SUM(completed) as done FROM subtasks GROUP BY taskId");
    const subtaskMap: Record<number, { total: number; done: number }> = {};
    for (const row of subtaskStmt.all() as any[]) {
      subtaskMap[row.taskId] = { total: row.total, done: row.done };
    }
    return tasks.map(t => ({
      ...t,
      subtaskCount: subtaskMap[t.id]?.total || 0,
      subtaskDone: subtaskMap[t.id]?.done || 0,
    }));
  },

  getTaskById: (id: number) => {
    return db.prepare("SELECT * FROM tasks WHERE id = ?").get(id);
  },

  addTask: (task: {
    title: string;
    description?: string;
    assignee: string;
    status: string;
    priority: string;
    category: string;
    dueDate?: string;
    completedDate?: string;
    relatedTo?: string[];
    createdAt: string;
  }) => {
    const stmt = db.prepare(`
      INSERT INTO tasks (title, description, assignee, status, priority, category, dueDate, completedDate, relatedTo, createdAt)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    const result = stmt.run(
      task.title,
      task.description || null,
      task.assignee,
      task.status,
      task.priority,
      task.category,
      task.dueDate || null,
      task.completedDate || null,
      task.relatedTo ? JSON.stringify(task.relatedTo) : null,
      task.createdAt
    );
    // Log activity
    const taskId = result.lastInsertRowid as number;
    sqliteDb.addActivity(taskId, "created", "Task created", task.assignee);
    return taskId;
  },

  updateStatus: (id: number, status: string, completedDate?: string) => {
    const old = db.prepare("SELECT status FROM tasks WHERE id = ?").get(id) as any;
    const stmt = db.prepare("UPDATE tasks SET status = ?, completedDate = ? WHERE id = ?");
    const result = stmt.run(status, completedDate || null, id);
    if (old && old.status !== status) {
      sqliteDb.addActivity(id, "status_change", `${old.status} → ${status}`, "System");
    }
    return result;
  },

  updateTask: (id: number, fields: {
    title?: string;
    description?: string;
    assignee?: string;
    status?: string;
    priority?: string;
    category?: string;
    dueDate?: string;
    completedDate?: string;
  }) => {
    const old = db.prepare("SELECT * FROM tasks WHERE id = ?").get(id) as any;
    const updates: string[] = [];
    const values: any[] = [];
    const changes: string[] = [];

    if (fields.title !== undefined) { updates.push("title = ?"); values.push(fields.title); }
    if (fields.description !== undefined) { updates.push("description = ?"); values.push(fields.description || null); }
    if (fields.assignee !== undefined) { updates.push("assignee = ?"); values.push(fields.assignee); }
    if (fields.status !== undefined) { 
      updates.push("status = ?"); values.push(fields.status);
      if (old && old.status !== fields.status) changes.push(`Status: ${old.status} → ${fields.status}`);
    }
    if (fields.priority !== undefined) { 
      updates.push("priority = ?"); values.push(fields.priority);
      if (old && old.priority !== fields.priority) changes.push(`Priority: ${old.priority} → ${fields.priority}`);
    }
    if (fields.category !== undefined) { updates.push("category = ?"); values.push(fields.category); }
    if (fields.dueDate !== undefined) { updates.push("dueDate = ?"); values.push(fields.dueDate || null); }
    if (fields.completedDate !== undefined) { updates.push("completedDate = ?"); values.push(fields.completedDate); }

    if (updates.length === 0) return;

    values.push(id);
    const stmt = db.prepare(`UPDATE tasks SET ${updates.join(", ")} WHERE id = ?`);
    const result = stmt.run(...values);

    if (changes.length > 0) {
      sqliteDb.addActivity(id, "updated", changes.join("; "), "User");
    }

    return result;
  },

  deleteTask: (id: number) => {
    return db.prepare("DELETE FROM tasks WHERE id = ?").run(id);
  },

  // ---- ACTIVITY LOG ----
  addActivity: (taskId: number, type: string, content: string, author: string) => {
    const stmt = db.prepare("INSERT INTO task_activity (taskId, type, content, author, createdAt) VALUES (?, ?, ?, ?, ?)");
    return stmt.run(taskId, type, content, author, new Date().toISOString());
  },

  getActivity: (taskId: number, limit = 20) => {
    return db.prepare("SELECT * FROM task_activity WHERE taskId = ? ORDER BY createdAt DESC LIMIT ?").all(taskId, limit);
  },

  // ---- SUBTASKS ----
  getSubtasks: (taskId: number) => {
    return db.prepare("SELECT * FROM subtasks WHERE taskId = ? ORDER BY id ASC").all(taskId);
  },

  addSubtask: (taskId: number, title: string) => {
    const stmt = db.prepare("INSERT INTO subtasks (taskId, title, createdAt) VALUES (?, ?, ?)");
    const result = stmt.run(taskId, title, new Date().toISOString());
    sqliteDb.addActivity(taskId, "subtask_added", `Added: ${title}`, "User");
    return result.lastInsertRowid;
  },

  toggleSubtask: (id: number) => {
    const sub = db.prepare("SELECT * FROM subtasks WHERE id = ?").get(id) as any;
    if (!sub) return;
    const newVal = sub.completed ? 0 : 1;
    db.prepare("UPDATE subtasks SET completed = ? WHERE id = ?").run(newVal, id);
    return newVal;
  },

  deleteSubtask: (id: number) => {
    return db.prepare("DELETE FROM subtasks WHERE id = ?").run(id);
  },

  // ---- CONTENT POSTS ----
  getAllPosts: () => {
    return db.prepare("SELECT * FROM content_posts ORDER BY createdAt DESC").all() as any[];
  },

  getPostById: (id: number) => {
    return db.prepare("SELECT * FROM content_posts WHERE id = ?").get(id);
  },

  addPost: (post: {
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
  }) => {
    const stmt = db.prepare(`
      INSERT INTO content_posts (title, hook, body, platform, contentType, status, hashtags, imageUrl, publishDate, assignee, priority, createdAt)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    const result = stmt.run(
      post.title, post.hook || null, post.body || null, post.platform, post.contentType,
      post.status, post.hashtags || null, post.imageUrl || null, post.publishDate || null,
      post.assignee, post.priority, post.createdAt
    );
    const postId = result.lastInsertRowid as number;
    sqliteDb.addContentActivity(postId, "created", "Post created", post.assignee);
    return postId;
  },

  updatePost: (id: number, fields: Record<string, any>) => {
    const old = db.prepare("SELECT * FROM content_posts WHERE id = ?").get(id) as any;
    const updates: string[] = [];
    const values: any[] = [];
    const changes: string[] = [];
    const allowed = ["title", "hook", "body", "platform", "contentType", "status", "hashtags", "imageUrl", "publishDate", "assignee", "priority"];

    for (const key of allowed) {
      if (fields[key] !== undefined) {
        updates.push(`${key} = ?`);
        values.push(fields[key] || null);
        if (old && old[key] !== fields[key]) changes.push(`${key}: ${old[key]} → ${fields[key]}`);
      }
    }
    if (updates.length === 0) return;
    updates.push("updatedAt = ?");
    values.push(new Date().toISOString());
    values.push(id);
    db.prepare(`UPDATE content_posts SET ${updates.join(", ")} WHERE id = ?`).run(...values);
    if (changes.length > 0) {
      sqliteDb.addContentActivity(id, "updated", changes.join("; "), "User");
    }
  },

  deletePost: (id: number) => {
    return db.prepare("DELETE FROM content_posts WHERE id = ?").run(id);
  },

  // ---- CONTENT ACTIVITY ----
  addContentActivity: (postId: number, type: string, content: string, author: string) => {
    const stmt = db.prepare("INSERT INTO content_activity (postId, type, content, author, createdAt) VALUES (?, ?, ?, ?, ?)");
    return stmt.run(postId, type, content, author, new Date().toISOString());
  },

  getContentActivity: (postId: number, limit = 20) => {
    return db.prepare("SELECT * FROM content_activity WHERE postId = ? ORDER BY createdAt DESC LIMIT ?").all(postId, limit);
  },
};

export default sqliteDb;
