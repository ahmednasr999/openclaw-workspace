"use client";

import { useState } from "react";
import { TaskCard } from "./TaskCard";

const COLUMNS = [
  { id: "Inbox", title: "Inbox", icon: "📥", color: "column-inbox" },
  { id: "My Tasks", title: "My Tasks", icon: "📝", color: "column-my-tasks" },
  { id: "OpenClaw Tasks", title: "OpenClaw", icon: "🤖", color: "column-openclaw" },
  { id: "In Progress", title: "In Progress", icon: "🔄", color: "column-progress" },
  { id: "Completed", title: "Completed", icon: "✅", color: "column-completed" },
];

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

  const handleDragOver = (e: React.DragEvent, columnId: string) => {
    e.preventDefault();
    setDragOverColumn(columnId);
  };

  const handleDragLeave = () => {
    setDragOverColumn(null);
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
    <div className="board-grid grid grid-cols-5 gap-4">
      {COLUMNS.map((column) => {
        const columnTasks = tasks.filter((task) => task.status === column.id);
        const isDropTarget = dragOverColumn === column.id;

        return (
          <div
            key={column.id}
            onDrop={(e) => handleDrop(e, column.id)}
            onDragOver={(e) => handleDragOver(e, column.id)}
            onDragLeave={handleDragLeave}
            className={`${column.color} rounded-xl p-3 min-h-[500px] transition-all duration-200 ${
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
                <div className={`text-center py-8 text-gray-600 text-xs rounded-lg border border-dashed ${
                  isDropTarget ? "border-indigo-500 bg-indigo-500/5" : "border-gray-800"
                }`}>
                  {isDropTarget ? "Drop here" : "No tasks"}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
