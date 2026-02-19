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

  // Update task status
  updateStatus: (id: number, status: string, completedDate?: string) => {
    const stmt = db.prepare(`
      UPDATE tasks SET status = ?, completedDate = ? WHERE id = ?
    `);
    return stmt.run(status, completedDate || null, id);
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
