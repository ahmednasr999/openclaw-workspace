"use client";

import { useState, useRef, useCallback } from "react";
import { TaskCard } from "./TaskCard";

const COLUMNS = [
  { id: "Inbox", title: "Inbox", icon: "📥", color: "column-inbox" },
  { id: "My Tasks", title: "My Tasks", icon: "📝", color: "column-my-tasks" },
  { id: "OpenClaw Tasks", title: "OpenClaw", icon: "🤖", color: "column-openclaw" },
  { id: "In Progress", title: "In Progress", icon: "🔄", color: "column-progress" },
  { id: "Review", title: "Review", icon: "👀", color: "column-review" },
  { id: "Completed", title: "Completed", icon: "✅", color: "column-completed" },
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
}

interface TaskBoardProps {
  tasks: Task[];
  onRefresh: () => void;
  onEditTask: (task: Task) => void;
}

export function TaskBoard({ tasks, onRefresh, onEditTask }: TaskBoardProps) {
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null);
  const [draggingId, setDraggingId] = useState<number | null>(null);
  
  // Touch drag state
  const touchState = useRef<{
    taskId: number | null;
    startX: number;
    startY: number;
    isDragging: boolean;
    ghost: HTMLDivElement | null;
  }>({ taskId: null, startX: 0, startY: 0, isDragging: false, ghost: null });

  const sortTasks = (taskList: Task[]) => {
    return [...taskList].sort((a, b) => {
      return (PRIORITY_ORDER[a.priority] ?? 99) - (PRIORITY_ORDER[b.priority] ?? 99);
    });
  };

  // Desktop drag
  const handleDragStart = (e: React.DragEvent, taskId: number) => {
    e.dataTransfer.setData("taskId", taskId.toString());
    setDraggingId(taskId);
  };

  const handleDragEnd = () => {
    setDraggingId(null);
    setDragOverColumn(null);
  };

  const handleDrop = async (e: React.DragEvent, status: string) => {
    e.preventDefault();
    setDragOverColumn(null);
    setDraggingId(null);
    const taskId = parseInt(e.dataTransfer.getData("taskId"));
    if (!taskId) return;
    await moveTask(taskId, status);
  };

  const handleDragOver = (e: React.DragEvent, columnId: string) => {
    e.preventDefault();
    setDragOverColumn(columnId);
  };

  // Touch drag for mobile
  const handleTouchStart = useCallback((e: React.TouchEvent, taskId: number) => {
    const touch = e.touches[0];
    touchState.current = {
      taskId,
      startX: touch.clientX,
      startY: touch.clientY,
      isDragging: false,
      ghost: null,
    };
  }, []);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    const ts = touchState.current;
    if (!ts.taskId) return;
    
    const touch = e.touches[0];
    const dx = Math.abs(touch.clientX - ts.startX);
    const dy = Math.abs(touch.clientY - ts.startY);
    
    if (!ts.isDragging && dx > 10) {
      ts.isDragging = true;
      // Create ghost element
      const ghost = document.createElement("div");
      ghost.className = "fixed z-[100] px-3 py-2 rounded-lg glass-strong text-white text-xs font-medium pointer-events-none";
      ghost.textContent = tasks.find(t => t.id === ts.taskId)?.title || "";
      document.body.appendChild(ghost);
      ts.ghost = ghost;
    }
    
    if (ts.isDragging && ts.ghost) {
      e.preventDefault();
      ts.ghost.style.left = `${touch.clientX - 50}px`;
      ts.ghost.style.top = `${touch.clientY - 20}px`;
      
      // Find column under touch
      const elements = document.elementsFromPoint(touch.clientX, touch.clientY);
      const col = elements.find(el => el.getAttribute("data-column"));
      const colId = col?.getAttribute("data-column") || null;
      setDragOverColumn(colId);
    }
  }, [tasks]);

  const handleTouchEnd = useCallback(async () => {
    const ts = touchState.current;
    if (ts.ghost) {
      document.body.removeChild(ts.ghost);
    }
    if (ts.isDragging && ts.taskId && dragOverColumn) {
      await moveTask(ts.taskId, dragOverColumn);
    }
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
    <div className="board-grid grid grid-cols-6 gap-4 overflow-x-auto pb-4">
      {COLUMNS.map((column) => {
        const columnTasks = sortTasks(tasks.filter((task) => task.status === column.id));
        const isDropTarget = dragOverColumn === column.id;

        return (
          <div
            key={column.id}
            data-column={column.id}
            onDrop={(e) => handleDrop(e, column.id)}
            onDragOver={(e) => handleDragOver(e, column.id)}
            onDragLeave={() => setDragOverColumn(null)}
            className={`${column.color} rounded-xl p-3 min-h-[500px] min-w-[220px] transition-all duration-200 ${
              isDropTarget ? "column-drop-active scale-[1.01]" : ""
            }`}
          >
            {/* Column Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="text-lg">{column.icon}</span>
                <h2 className="text-sm font-semibold text-white">{column.title}</h2>
              </div>
              <span className="column-badge">{columnTasks.length}</span>
            </div>
            
            {/* Tasks */}
            <div className="space-y-2">
              {columnTasks.map((task) => (
                <div
                  key={task.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, task.id)}
                  onDragEnd={handleDragEnd}
                  onTouchStart={(e) => handleTouchStart(e, task.id)}
                  onTouchMove={(e) => handleTouchMove(e)}
                  onTouchEnd={() => handleTouchEnd()}
                  className={draggingId === task.id ? "opacity-40" : ""}
                >
                  <TaskCard 
                    task={task} 
                    onDelete={() => handleDelete(task.id)}
                    onEdit={() => onEditTask(task)}
                  />
                </div>
              ))}
              {columnTasks.length === 0 && (
                <div className={`text-center py-8 text-gray-600 text-xs rounded-lg border border-dashed transition-all ${
                  isDropTarget ? "border-indigo-500 bg-indigo-500/5 text-indigo-400" : "border-gray-800"
                }`}>
                  {isDropTarget ? "Drop here" : 
                   column.id === "Inbox" ? "All clear ✨" : "No tasks"}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
