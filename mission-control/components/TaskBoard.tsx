"use client";

import { useState, useRef, useCallback } from "react";
import { TaskCard } from "./TaskCard";
import { Icon } from "./Icon";

const COLUMNS = [
  { id: "Inbox", title: "Inbox", icon: "inbox" },
  { id: "My Tasks", title: "My Tasks", icon: "myTasks" },
  { id: "OpenClaw Tasks", title: "OpenClaw", icon: "openClaw" },
  { id: "In Progress", title: "In Progress", icon: "inProgress" },
  { id: "QA", title: "QA", icon: "check" },
  { id: "Review", title: "Review", icon: "review" },
  { id: "Completed", title: "Completed", icon: "published" },
];

const PRIORITY_ORDER: Record<string, number> = { High: 0, Medium: 1, Low: 2 };

interface Task {
  id: number;
  title: string;
  description?: string;
  assignee: string;
  priority: string;
  category: string;
  status: string;
  dueDate?: string;
  completedDate?: string;
  createdAt: string;
  subtaskCount?: number;
  subtaskDone?: number;
}

interface TaskBoardProps {
  tasks: Task[];
  onRefresh: () => void;
  onEditTask: (task: Task) => void;
}

export function TaskBoard({ tasks, onRefresh, onEditTask }: TaskBoardProps) {
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null);
  const [draggingId, setDraggingId] = useState<number | null>(null);
  
  const touchState = useRef<{
    taskId: number | null;
    startX: number;
    startY: number;
    isDragging: boolean;
    ghost: HTMLDivElement | null;
  }>({ taskId: null, startX: 0, startY: 0, isDragging: false, ghost: null });

  const sortTasks = (taskList: Task[]) => {
    return [...taskList].sort((a, b) => 
      (PRIORITY_ORDER[a.priority] ?? 99) - (PRIORITY_ORDER[b.priority] ?? 99)
    );
  };

  const handleDragStart = (e: React.DragEvent, taskId: number) => {
    e.dataTransfer.setData("taskId", taskId.toString());
    setDraggingId(taskId);
  };

  const handleDrop = async (e: React.DragEvent, status: string) => {
    e.preventDefault();
    setDragOverColumn(null);
    setDraggingId(null);
    const taskId = parseInt(e.dataTransfer.getData("taskId"));
    if (taskId) await moveTask(taskId, status);
  };

  const handleTouchStart = useCallback((e: React.TouchEvent, taskId: number) => {
    const touch = e.touches[0];
    touchState.current = { taskId, startX: touch.clientX, startY: touch.clientY, isDragging: false, ghost: null };
  }, []);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    const ts = touchState.current;
    if (!ts.taskId) return;
    const touch = e.touches[0];
    if (!ts.isDragging && Math.abs(touch.clientX - ts.startX) > 10) {
      ts.isDragging = true;
      const ghost = document.createElement("div");
      ghost.className = "fixed z-[100] px-3 py-2 rounded-lg text-white text-xs font-medium pointer-events-none";
      ghost.style.background = "var(--bg-card)";
      ghost.style.border = "1px solid var(--accent)";
      ghost.textContent = tasks.find(t => t.id === ts.taskId)?.title || "";
      document.body.appendChild(ghost);
      ts.ghost = ghost;
    }
    if (ts.isDragging && ts.ghost) {
      e.preventDefault();
      ts.ghost.style.left = `${touch.clientX - 50}px`;
      ts.ghost.style.top = `${touch.clientY - 20}px`;
      const elements = document.elementsFromPoint(touch.clientX, touch.clientY);
      const col = elements.find(el => el.getAttribute("data-column"));
      setDragOverColumn(col?.getAttribute("data-column") || null);
    }
  }, [tasks]);

  const handleTouchEnd = useCallback(async () => {
    const ts = touchState.current;
    if (ts.ghost) document.body.removeChild(ts.ghost);
    if (ts.isDragging && ts.taskId && dragOverColumn) await moveTask(ts.taskId, dragOverColumn);
    touchState.current = { taskId: null, startX: 0, startY: 0, isDragging: false, ghost: null };
    setDragOverColumn(null);
  }, [dragOverColumn]);

  const moveTask = async (taskId: number, status: string) => {
    const completedDate = status === "Completed" ? new Date().toISOString() : undefined;
    try {
      await fetch("/api/tasks", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: taskId, status, completedDate }),
      });
      onRefresh();
    } catch (error) {
      console.error("Error updating task:", error);
    }
  };

  const handleDelete = async (taskId: number) => {
    try {
      await fetch(`/api/tasks?id=${taskId}`, { method: "DELETE" });
      onRefresh();
    } catch (error) {
      console.error("Error deleting task:", error);
    }
  };

  return (
    <div className="board-grid" style={{ gridTemplateColumns: `repeat(${COLUMNS.length}, minmax(260px, 1fr))` }}>
      {COLUMNS.map((column) => {
        const columnTasks = sortTasks(tasks.filter((task) => task.status === column.id));
        const isDropTarget = dragOverColumn === column.id;

        return (
          <div
            key={column.id}
            data-column={column.id}
            onDrop={(e) => handleDrop(e, column.id)}
            onDragOver={(e) => { e.preventDefault(); setDragOverColumn(column.id); }}
            onDragLeave={() => setDragOverColumn(null)}
            className={`column ${isDropTarget ? "column-drop-active" : ""}`}
          >
            <div className="column-header">
              <div className="column-title">
                <Icon name={column.icon} className="text-gray-400" size={16} />
                <span className="column-name">{column.title}</span>
              </div>
              <span className="column-count">{columnTasks.length}</span>
            </div>

            <div className="column-body">
              {columnTasks.map((task) => (
                <div
                  key={task.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, task.id)}
                  onDragEnd={() => { setDraggingId(null); setDragOverColumn(null); }}
                  onTouchStart={(e) => handleTouchStart(e, task.id)}
                  onTouchMove={(e) => handleTouchMove(e)}
                  onTouchEnd={() => handleTouchEnd()}
                  className={draggingId === task.id ? "opacity-30" : ""}
                >
                  <TaskCard
                    task={task}
                    onDelete={() => handleDelete(task.id)}
                    onEdit={() => onEditTask(task)}
                  />
                </div>
              ))}
              {columnTasks.length === 0 && (
                <div className="column-empty">
                  {isDropTarget ? "Drop here" : column.id === "Inbox" ? "All clear ✨" : "No tasks"}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
