import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { TaskItem, TaskStatus } from "@/lib/parity";

const dataDir = path.join(process.cwd(), "data");
const filePath = path.join(dataDir, "tasks.json");

// Empty array: live tasks come from active-tasks.md via lib/sync
const emptyTasks: TaskItem[] = [];

async function ensureTasksFile() {
  await mkdir(dataDir, { recursive: true });

  try {
    await readFile(filePath, "utf8");
  } catch {
    // Create empty file (not seeded with fake data)
    await writeFile(filePath, JSON.stringify(emptyTasks, null, 2), "utf8");
  }
}

export async function loadTasks(): Promise<TaskItem[]> {
  await ensureTasksFile();
  const raw = await readFile(filePath, "utf8");
  return JSON.parse(raw) as TaskItem[];
}

async function saveTasks(tasks: TaskItem[]) {
  await writeFile(filePath, JSON.stringify(tasks, null, 2), "utf8");
}

export interface NewTaskInput {
  title: string;
  assignee: string;
  priority: TaskItem["priority"];
  dueDate: string;
  status?: TaskStatus;
}

export async function createTask(input: NewTaskInput): Promise<TaskItem> {
  const tasks = await loadTasks();
  const task: TaskItem = {
    id: `t-${Date.now()}`,
    title: input.title,
    assignee: input.assignee,
    priority: input.priority,
    dueDate: input.dueDate,
    status: input.status || "backlog",
  };

  tasks.unshift(task);
  await saveTasks(tasks);
  return task;
}

export async function updateTaskStatus(taskId: string, status: TaskStatus): Promise<TaskItem | null> {
  const tasks = await loadTasks();
  const index = tasks.findIndex((task) => task.id === taskId);

  if (index < 0) {
    return null;
  }

  tasks[index] = { ...tasks[index], status };
  await saveTasks(tasks);
  return tasks[index];
}
