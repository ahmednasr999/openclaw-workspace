"use client";

import { useState } from "react";
import { Icon } from "./Icon";

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

const TAG_CLASSES: Record<string, string> = {
  "Job Search": "tag-job-search",
  Content: "tag-content",
  Networking: "tag-networking",
  Applications: "tag-applications",
  Interviews: "tag-interviews",
  Task: "tag-task",
};

export function TaskCard({ task, onDelete, onEdit }: TaskCardProps) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const isCompleted = task.status === "Completed";

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    if (diffDays < 0) return { text: `${Math.abs(diffDays)}d overdue`, color: "text-[var(--danger)]" };
    if (diffDays === 0) return { text: "Today", color: "text-[var(--warning)]" };
    if (diffDays === 1) return { text: "Tomorrow", color: "text-[var(--warning)]" };
    if (diffDays <= 7) return { text: `${diffDays}d`, color: "text-[#60a5fa]" };
    return { text: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }), color: "text-[var(--text-muted)]" };
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirmDelete) { onDelete(); } 
    else { setConfirmDelete(true); setTimeout(() => setConfirmDelete(false), 3000); }
  };

  return (
    <div
      className={`task-card ${isCompleted ? "completed" : ""}`}
      onClick={onEdit}
    >
      {/* Actions */}
      <div className="card-actions">
        <button onClick={(e) => { e.stopPropagation(); onEdit(); }} className="card-action-btn" title="Edit">
          <Icon name="edit" size={14} />
        </button>
        <button onClick={handleDelete} className={`card-action-btn ${confirmDelete ? "" : "danger"}`} title={confirmDelete ? "Confirm?" : "Delete"}>
          {confirmDelete ? "✕" : <Icon name="delete" size={14} />}
        </button>
      </div>

      {/* Tag + Priority */}
      <div className="flex items-center gap-2 mb-2">
        <span className={`tag ${TAG_CLASSES[task.category] || "tag-task"}`}>{task.category}</span>
        <div className={`priority-dot priority-dot-${task.priority.toLowerCase()}`} title={task.priority} />
      </div>

      {/* Title */}
      <div className={`task-card-title ${isCompleted ? "done" : ""}`}>{task.title}</div>

      {/* Description */}
      {task.description && <div className="task-card-desc">{task.description}</div>}

      {/* Subtask progress */}
      {task.subtaskCount && task.subtaskCount > 0 ? (
        <div className="subtask-bar">
          <div
            className="subtask-bar-fill"
            style={{ width: `${((task.subtaskDone || 0) / task.subtaskCount) * 100}%` }}
          />
        </div>
      ) : null}

      {/* Footer */}
      <div className="card-footer">
        <div className="flex items-center gap-2">
          <div className={`assignee-badge assignee-${task.assignee.toLowerCase()}`}>
            {task.assignee === "Ahmed" ? "A" : task.assignee === "OpenClaw" ? "O" : "B"}
          </div>
          <span className="text-[11px] text-[var(--text-muted)]">{task.assignee}</span>
        </div>
        <div className="flex items-center gap-2">
          {task.subtaskCount && task.subtaskCount > 0 ? (
            <span className="text-[10px] text-[var(--text-muted)]">
              ☑ {task.subtaskDone}/{task.subtaskCount}
            </span>
          ) : null}
          {task.dueDate && (() => {
            const { text, color } = formatDate(task.dueDate);
            return <span className={`text-[10px] ${isCompleted ? "text-[var(--text-muted)]" : color}`}>{text}</span>;
          })()}
        </div>
      </div>
    </div>
  );
}
