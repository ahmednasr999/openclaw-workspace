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

  CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT,
    company TEXT,
    email TEXT,
    phone TEXT,
    linkedin TEXT,
    category TEXT NOT NULL DEFAULT 'Networking',
    status TEXT NOT NULL DEFAULT 'Active',
    warmth TEXT NOT NULL DEFAULT 'Warm',
    notes TEXT,
    lastContactDate TEXT,
    nextFollowUp TEXT,
    source TEXT,
    tags TEXT,
    createdAt TEXT NOT NULL,
    updatedAt TEXT
  );

  CREATE TABLE IF NOT EXISTS contact_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contactId INTEGER NOT NULL,
    type TEXT NOT NULL,
    content TEXT,
    author TEXT NOT NULL DEFAULT 'System',
    createdAt TEXT NOT NULL,
    FOREIGN KEY (contactId) REFERENCES contacts(id) ON DELETE CASCADE
  );

  -- Agents Knowledge Exchange
  CREATE TABLE IF NOT EXISTS knowledge_exchange (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,
    agentId TEXT,
    taskId INTEGER,
    sourceType TEXT DEFAULT 'agent',
    author TEXT NOT NULL DEFAULT 'System',
    createdAt TEXT NOT NULL,
    updatedAt TEXT
  );

  -- CV Maker History
  CREATE TABLE IF NOT EXISTS cv_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jobTitle TEXT NOT NULL,
    company TEXT NOT NULL,
    jobUrl TEXT,
    atsScore INTEGER,
    matchedKeywords TEXT,
    missingKeywords TEXT,
    pdfPath TEXT,
    status TEXT NOT NULL DEFAULT 'Generated',
    notes TEXT,
    createdAt TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taskId INTEGER,
    title TEXT NOT NULL,
    scheduledDate TEXT NOT NULL,
    scheduledTime TEXT,
    type TEXT NOT NULL DEFAULT 'task',
    status TEXT NOT NULL DEFAULT 'scheduled',
    notes TEXT,
    createdAt TEXT NOT NULL
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

  // ---- SCHEDULED TASKS ----
  getScheduledTasks: (startDate?: string, endDate?: string) => {
    let query = "SELECT * FROM scheduled_tasks";
    const params: any[] = [];
    if (startDate && endDate) {
      query += " WHERE scheduledDate >= ? AND scheduledDate <= ?";
      params.push(startDate, endDate);
    } else if (startDate) {
      query += " WHERE scheduledDate >= ?";
      params.push(startDate);
    } else if (endDate) {
      query += " WHERE scheduledDate <= ?";
      params.push(endDate);
    }
    query += " ORDER BY scheduledDate ASC, scheduledTime ASC";
    return db.prepare(query).all(...params) as any[];
  },

  getScheduledTaskById: (id: number) => {
    return db.prepare("SELECT * FROM scheduled_tasks WHERE id = ?").get(id);
  },

  addScheduledTask: (task: {
    taskId?: number;
    title: string;
    scheduledDate: string;
    scheduledTime?: string;
    type: string;
    status: string;
    notes?: string;
    createdAt: string;
  }) => {
    const stmt = db.prepare(`
      INSERT INTO scheduled_tasks (taskId, title, scheduledDate, scheduledTime, type, status, notes, createdAt)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);
    const result = stmt.run(
      task.taskId || null,
      task.title,
      task.scheduledDate,
      task.scheduledTime || null,
      task.type,
      task.status,
      task.notes || null,
      task.createdAt
    );
    return result.lastInsertRowid;
  },

  updateScheduledTask: (id: number, fields: {
    scheduledDate?: string;
    scheduledTime?: string;
    status?: string;
    notes?: string;
  }) => {
    const updates: string[] = [];
    const values: any[] = [];
    if (fields.scheduledDate !== undefined) { updates.push("scheduledDate = ?"); values.push(fields.scheduledDate); }
    if (fields.scheduledTime !== undefined) { updates.push("scheduledTime = ?"); values.push(fields.scheduledTime); }
    if (fields.status !== undefined) { updates.push("status = ?"); values.push(fields.status); }
    if (fields.notes !== undefined) { updates.push("notes = ?"); values.push(fields.notes || null); }
    if (updates.length === 0) return;
    values.push(id);
    return db.prepare(`UPDATE scheduled_tasks SET ${updates.join(", ")} WHERE id = ?`).run(...values);
  },

  deleteScheduledTask: (id: number) => {
    return db.prepare("DELETE FROM scheduled_tasks WHERE id = ?").run(id);
  },

  // ---- CONTACTS ----
  getAllContacts: () => {
    return db.prepare("SELECT * FROM contacts ORDER BY updatedAt DESC, createdAt DESC").all() as any[];
  },

  getContactById: (id: number) => {
    return db.prepare("SELECT * FROM contacts WHERE id = ?").get(id);
  },

  addContact: (contact: {
    name: string;
    role?: string;
    company?: string;
    email?: string;
    phone?: string;
    linkedin?: string;
    category: string;
    status: string;
    warmth: string;
    notes?: string;
    lastContactDate?: string;
    nextFollowUp?: string;
    source?: string;
    tags?: string;
    createdAt: string;
  }) => {
    const stmt = db.prepare(`
      INSERT INTO contacts (name, role, company, email, phone, linkedin, category, status, warmth, notes, lastContactDate, nextFollowUp, source, tags, createdAt, updatedAt)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    const result = stmt.run(
      contact.name, contact.role || null, contact.company || null,
      contact.email || null, contact.phone || null, contact.linkedin || null,
      contact.category, contact.status, contact.warmth,
      contact.notes || null, contact.lastContactDate || null, contact.nextFollowUp || null,
      contact.source || null, contact.tags || null, contact.createdAt, contact.createdAt
    );
    const id = result.lastInsertRowid as number;
    sqliteDb.addContactActivity(id, "created", "Contact added", "User");
    return id;
  },

  updateContact: (id: number, fields: Record<string, any>) => {
    const old = db.prepare("SELECT * FROM contacts WHERE id = ?").get(id) as any;
    const allowed = ["name", "role", "company", "email", "phone", "linkedin", "category", "status", "warmth", "notes", "lastContactDate", "nextFollowUp", "source", "tags"];
    const updates: string[] = [];
    const values: any[] = [];
    const changes: string[] = [];

    for (const key of allowed) {
      if (fields[key] !== undefined) {
        updates.push(`${key} = ?`);
        values.push(fields[key] || null);
        if (old && old[key] !== fields[key]) changes.push(`${key}: ${old[key] || "empty"} → ${fields[key] || "empty"}`);
      }
    }
    if (updates.length === 0) return;
    updates.push("updatedAt = ?");
    values.push(new Date().toISOString());
    values.push(id);
    db.prepare(`UPDATE contacts SET ${updates.join(", ")} WHERE id = ?`).run(...values);
    if (changes.length > 0) {
      sqliteDb.addContactActivity(id, "updated", changes.join("; "), "User");
    }
  },

  deleteContact: (id: number) => {
    return db.prepare("DELETE FROM contacts WHERE id = ?").run(id);
  },

  // ---- CONTACT ACTIVITY ----
  addContactActivity: (contactId: number, type: string, content: string, author: string) => {
    const stmt = db.prepare("INSERT INTO contact_activity (contactId, type, content, author, createdAt) VALUES (?, ?, ?, ?, ?)");
    return stmt.run(contactId, type, content, author, new Date().toISOString());
  },

  getContactActivity: (contactId: number, limit = 20) => {
    return db.prepare("SELECT * FROM contact_activity WHERE contactId = ? ORDER BY createdAt DESC LIMIT ?").all(contactId, limit);
  },

  // ---- KNOWLEDGE EXCHANGE ----
  getAllKnowledge: (options?: { category?: string; q?: string; limit?: number }) => {
    let sql = "SELECT * FROM knowledge_exchange";
    const params: any[] = [];
    const conditions: string[] = [];

    if (options?.category) {
      conditions.push("category = ?");
      params.push(options.category);
    }
    if (options?.q) {
      conditions.push("(title LIKE ? OR content LIKE ? OR tags LIKE ?)");
      const term = `%${options.q}%`;
      params.push(term, term, term);
    }

    if (conditions.length > 0) {
      sql += " WHERE " + conditions.join(" AND ");
    }
    sql += " ORDER BY createdAt DESC";

    if (options?.limit) {
      sql += " LIMIT ?";
      params.push(options.limit);
    }

    return db.prepare(sql).all(...params);
  },

  getKnowledgeById: (id: number) => {
    return db.prepare("SELECT * FROM knowledge_exchange WHERE id = ?").get(id);
  },

  addKnowledge: (entry: {
    category: string;
    title: string;
    content: string;
    tags?: string;
    agentId?: string;
    taskId?: number;
    sourceType?: string;
    author?: string;
  }) => {
    const stmt = db.prepare(`
      INSERT INTO knowledge_exchange (category, title, content, tags, agentId, taskId, sourceType, author, createdAt, updatedAt)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    const now = new Date().toISOString();
    const result = stmt.run(
      entry.category, entry.title, entry.content,
      entry.tags || null, entry.agentId || null, entry.taskId || null,
      entry.sourceType || "agent", entry.author || "System", now, now
    );
    return result.lastInsertRowid as number;
  },

  updateKnowledge: (id: number, fields: { title?: string; content?: string; tags?: string; category?: string }) => {
    const updates: string[] = [];
    const values: any[] = [];
    const now = new Date().toISOString();

    if (fields.title !== undefined) { updates.push("title = ?"); values.push(fields.title); }
    if (fields.content !== undefined) { updates.push("content = ?"); values.push(fields.content); }
    if (fields.tags !== undefined) { updates.push("tags = ?"); values.push(fields.tags || null); }
    if (fields.category !== undefined) { updates.push("category = ?"); values.push(fields.category); }

    if (updates.length === 0) return;
    updates.push("updatedAt = ?");
    values.push(now);
    values.push(id);

    return db.prepare(`UPDATE knowledge_exchange SET ${updates.join(", ")} WHERE id = ?`).run(...values);
  },

  deleteKnowledge: (id: number) => {
    return db.prepare("DELETE FROM knowledge_exchange WHERE id = ?").run(id);
  },

  searchKnowledge: (query: string, limit = 10) => {
    const term = `%${query}%`;
    return db.prepare(`
      SELECT * FROM knowledge_exchange
      WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
      ORDER BY createdAt DESC
      LIMIT ?
    `).all(term, term, term, limit);
  },

  // ---- CV HISTORY ----
  getAllCVHistory: (limit = 50) => {
    return db.prepare(`SELECT * FROM cv_history ORDER BY createdAt DESC LIMIT ?`).all(limit);
  },

  getCVHistoryById: (id: number) => {
    return db.prepare("SELECT * FROM cv_history WHERE id = ?").get(id);
  },

  addCVHistory: (entry: {
    jobTitle: string;
    company: string;
    jobUrl?: string;
    atsScore?: number;
    matchedKeywords?: string[];
    missingKeywords?: string[];
    pdfPath?: string;
    status?: string;
    notes?: string;
  }) => {
    const stmt = db.prepare(`
      INSERT INTO cv_history (jobTitle, company, jobUrl, atsScore, matchedKeywords, missingKeywords, pdfPath, status, notes, createdAt)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    const result = stmt.run(
      entry.jobTitle,
      entry.company,
      entry.jobUrl || null,
      entry.atsScore || null,
      entry.matchedKeywords ? JSON.stringify(entry.matchedKeywords) : null,
      entry.missingKeywords ? JSON.stringify(entry.missingKeywords) : null,
      entry.pdfPath || null,
      entry.status || "Generated",
      entry.notes || null,
      new Date().toISOString()
    );
    return result.lastInsertRowid as number;
  },

  updateCVHistory: (id: number, fields: { pdfPath?: string; atsScore?: number; status?: string; notes?: string }) => {
    const updates: string[] = [];
    const values: any[] = [];

    if (fields.pdfPath !== undefined) { updates.push("pdfPath = ?"); values.push(fields.pdfPath); }
    if (fields.atsScore !== undefined) { updates.push("atsScore = ?"); values.push(fields.atsScore); }
    if (fields.status !== undefined) { updates.push("status = ?"); values.push(fields.status); }
    if (fields.notes !== undefined) { updates.push("notes = ?"); values.push(fields.notes); }

    if (updates.length === 0) return;
    values.push(id);
    return db.prepare(`UPDATE cv_history SET ${updates.join(", ")} WHERE id = ?`).run(...values);
  },

  deleteCVHistory: (id: number) => {
    return db.prepare("DELETE FROM cv_history WHERE id = ?").run(id);
  },
};

export default sqliteDb;
