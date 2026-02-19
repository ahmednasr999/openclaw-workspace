import Database from "better-sqlite3";
import path from "path";

// Database file location
const DB_PATH = path.join(process.cwd(), "mission-control.db");

// Initialize database
const db = new Database(DB_PATH);

// Create tasks table
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
  )
`);

// Helper functions
export const sqliteDb = {
  // Get all tasks
  getAllTasks: () => {
    const stmt = db.prepare("SELECT * FROM tasks ORDER BY createdAt DESC");
    return stmt.all();
  },

  // Add a task
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
    return result.lastInsertRowid;
  },

  // Update task status only
  updateStatus: (id: number, status: string, completedDate?: string) => {
    const stmt = db.prepare(`
      UPDATE tasks SET status = ?, completedDate = ? WHERE id = ?
    `);
    return stmt.run(status, completedDate || null, id);
  },

  // Update all task fields
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
    const updates: string[] = [];
    const values: any[] = [];

    if (fields.title !== undefined) { updates.push("title = ?"); values.push(fields.title); }
    if (fields.description !== undefined) { updates.push("description = ?"); values.push(fields.description || null); }
    if (fields.assignee !== undefined) { updates.push("assignee = ?"); values.push(fields.assignee); }
    if (fields.status !== undefined) { updates.push("status = ?"); values.push(fields.status); }
    if (fields.priority !== undefined) { updates.push("priority = ?"); values.push(fields.priority); }
    if (fields.category !== undefined) { updates.push("category = ?"); values.push(fields.category); }
    if (fields.dueDate !== undefined) { updates.push("dueDate = ?"); values.push(fields.dueDate || null); }
    if (fields.completedDate !== undefined) { updates.push("completedDate = ?"); values.push(fields.completedDate); }

    if (updates.length === 0) return;

    values.push(id);
    const stmt = db.prepare(`UPDATE tasks SET ${updates.join(", ")} WHERE id = ?`);
    return stmt.run(...values);
  },

  // Delete task
  deleteTask: (id: number) => {
    const stmt = db.prepare("DELETE FROM tasks WHERE id = ?");
    return stmt.run(id);
  },

  // Get task by ID
  getTaskById: (id: number) => {
    const stmt = db.prepare("SELECT * FROM tasks WHERE id = ?");
    return stmt.get(id);
  },
};

export default sqliteDb;
