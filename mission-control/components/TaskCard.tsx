"use client";

import { useState } from "react";

interface Task {
  id: number;
  title: string;
  description?: string;
  assignee: string;
  priority: string;
  category: string;
  status: string;
  dueDate?: string;
  createdAt: string;
  subtaskCount?: number;
  subtaskDone?: number;
}

interface TaskCardProps {
  task: Task;
  onDelete: () => void;
  onEdit: () => void;
}

export function TaskCard({ task, onDelete, onEdit }: TaskCardProps) {
  const [showConfirm, setShowConfirm] = useState(false);

  const priorityConfig: Record<string, { class: string; dot: string }> = {
    High: { class: "priority-high", dot: "bg-red-400" },
    Medium: { class: "priority-medium", dot: "bg-yellow-400" },
    Low: { class: "priority-low", dot: "bg-green-400" },
  };

  const categoryIcons: Record<string, string> = {
    "Job Search": "🎯",
    Content: "📝",
    Networking: "🤝",
    Applications: "📋",
    Interviews: "🎤",
    Task: "📌",
  };

  const priority = priorityConfig[task.priority] || { class: "text-gray-400", dot: "bg-gray-400" };
  const isCompleted = task.status === "Completed";

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return { text: `${Math.abs(diffDays)}d overdue`, color: "text-red-400" };
    if (diffDays === 0) return { text: "Today", color: "text-yellow-400" };
    if (diffDays === 1) return { text: "Tomorrow", color: "text-yellow-400" };
    if (diffDays <= 7) return { text: `${diffDays}d left`, color: "text-blue-400" };
    return { text: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }), color: "text-gray-500" };
  };

  const assigneeColor = task.assignee === "Ahmed" ? "text-blue-400" : 
                        task.assignee === "OpenClaw" ? "text-purple-400" : "text-indigo-400";

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (showConfirm) {
      onDelete();
    } else {
      setShowConfirm(true);
      setTimeout(() => setShowConfirm(false), 3000);
    }
  };

  return (
    <div 
      className={`task-card glass-strong rounded-lg p-3 cursor-grab active:cursor-grabbing group relative ${
        isCompleted ? "opacity-60" : ""
      }`}
      onClick={onEdit}
    >
      {/* Top row: category + priority + actions */}
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm">{categoryIcons[task.category] || "📌"}</span>
        <div className="flex items-center gap-1.5">
          <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${priority.class}`}>
            {task.priority}
          </span>
          {/* Always-visible action buttons for touch */}
          <button
            onClick={(e) => { e.stopPropagation(); onEdit(); }}
            className="w-7 h-7 rounded-md flex items-center justify-center text-xs hover:bg-white/10 text-gray-500 hover:text-white md:opacity-0 md:group-hover:opacity-100 transition-opacity"
            title="Edit"
          >
            ✏️
          </button>
          <button
            onClick={handleDelete}
            className={`w-7 h-7 rounded-md flex items-center justify-center text-xs transition-all md:opacity-0 md:group-hover:opacity-100 ${
              showConfirm 
                ? "bg-red-500/20 text-red-400 opacity-100" 
                : "hover:bg-red-500/20 text-gray-500 hover:text-red-400"
            }`}
            title={showConfirm ? "Click again to delete" : "Delete"}
          >
            {showConfirm ? "❌" : "🗑️"}
          </button>
        </div>
      </div>
      
      {/* Title */}
      <h3 className={`text-sm font-medium text-white mb-1 leading-snug ${
        isCompleted ? "line-through text-gray-400" : ""
      }`}>{task.title}</h3>
      
      {/* Description */}
      {task.description && (
        <p className="text-xs text-gray-500 mb-2 line-clamp-2 leading-relaxed">{task.description}</p>
      )}
      
      {/* Subtask progress */}
      {task.subtaskCount && task.subtaskCount > 0 ? (
        <div className="mb-2">
          <div className="flex justify-between text-[10px] text-gray-500 mb-1">
            <span>☑️ {task.subtaskDone}/{task.subtaskCount}</span>
            <span>{Math.round(((task.subtaskDone || 0) / task.subtaskCount) * 100)}%</span>
          </div>
          <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
            <div className="h-full bg-green-500 rounded-full transition-all" style={{ width: `${((task.subtaskDone || 0) / task.subtaskCount) * 100}%` }} />
          </div>
        </div>
      ) : null}

      {/* Footer: assignee + due date */}
      <div className="flex justify-between items-center mt-2 pt-2 border-t border-white/5">
        <span className={`text-[10px] font-medium ${assigneeColor}`}>
          {task.assignee === "Ahmed" ? "👤 Ahmed" : 
           task.assignee === "OpenClaw" ? "🤖 OpenClaw" : "👥 Both"}
        </span>
        {task.dueDate && (() => {
          const { text, color } = formatDate(task.dueDate);
          return <span className={`text-[10px] ${isCompleted ? "text-gray-600" : color}`}>📅 {text}</span>;
        })()}
      </div>
    </div>
  );
}
