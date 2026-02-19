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

const CATEGORY_CLASS: Record<string, string> = {
  "Job Search": "tag-linkedin",
  "Content": "tag-x",
  "Networking": "tag-job-search",
  "Applications": "tag-applications",
  "Interviews": "tag-interviews",
  "Task": "tag-task",
};

const STATUS_ICONS: Record<string, string> = {
  "Inbox": "inbox",
  "My Tasks": "myTasks",
  "OpenClaw Tasks": "openClaw",
  "In Progress": "inProgress",
  "QA": "check",
  "Review": "review",
  "Completed": "published",
};

const AGENT_MAP: Record<string, { initial: string; class: string }> = {
  "Ahmed": { initial: "A", class: "assignee-ahmed" },
  "OpenClaw": { initial: "O", class: "assignee-openclaw" },
  "NASR": { initial: "N", class: "assignee-openclaw" },
  "NASR (Coder)": { initial: "{ }", class: "assignee-openclaw" },
  "NASR (Writer)": { initial: "✎", class: "assignee-openclaw" },
  "NASR (Research)": { initial: "🔍", class: "assignee-openclaw" },
  "NASR (CV)": { initial: "📄", class: "assignee-openclaw" },
  "QA Agent": { initial: "✓", class: "assignee-openclaw" },
  "Both": { initial: "B", class: "assignee-both" },
};

function getAgentInitial(assignee: string): string {
  return AGENT_MAP[assignee]?.initial || assignee.charAt(0).toUpperCase();
}

function getAgentBadgeClass(assignee: string): string {
  return AGENT_MAP[assignee]?.class || "assignee-openclaw";
}

export function TaskCard({ task, onDelete, onEdit }: TaskCardProps) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const isCompleted = task.status === "Completed";

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    if (diffDays < 0) return { text: `${Math.abs(diffDays)}d overdue`, color: "text-red-400" };
    if (diffDays === 0) return { text: "Today", color: "text-amber-400" };
    if (diffDays === 1) return { text: "Tomorrow", color: "text-amber-400" };
    if (diffDays <= 7) return { text: `${diffDays}d`, color: "text-blue-400" };
    return { text: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }), color: "text-gray-500" };
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirmDelete) { onDelete(); } 
    else { setConfirmDelete(true); setTimeout(() => setConfirmDelete(false), 3000); }
  };

  const dateInfo = task.dueDate ? formatDate(task.dueDate) : null;

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

      {/* Category Tag + Priority */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-[10px] text-gray-600 font-mono">#{task.id}</span>
        <span className={`tag ${CATEGORY_CLASS[task.category] || "tag-task"}`}>
          {task.category}
        </span>
        <span className={`priority-dot priority-dot-${task.priority.toLowerCase()}`} title={task.priority} />
      </div>

      {/* Title */}
      <div className={`task-card-title ${isCompleted ? "done" : ""}`}>{task.title}</div>

      {/* Description/Preview */}
      {task.description && (
        <div className="task-card-desc">{task.description}</div>
      )}

      {/* Subtask Progress */}
      {task.subtaskCount && task.subtaskCount > 0 ? (
        <div className="mt-2">
          <div className="flex justify-between text-[10px] text-gray-500 mb-1">
            <span>Progress</span>
            <span>{task.subtaskDone}/{task.subtaskCount}</span>
          </div>
          <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-300"
              style={{ width: `${((task.subtaskDone || 0) / task.subtaskCount) * 100}%` }}
            />
          </div>
        </div>
      ) : null}

      {/* Footer */}
      <div className="card-footer">
        <div className="flex items-center gap-2">
          <div className={`assignee-badge ${getAgentBadgeClass(task.assignee)}`}>
            {getAgentInitial(task.assignee)}
          </div>
          <span className="text-[11px] text-gray-500">{task.assignee}</span>
        </div>
        <div className="flex items-center gap-2">
          {task.subtaskCount && task.subtaskCount > 0 && (
            <span className="text-[10px] text-gray-500 flex items-center gap-1">
              <Icon name="check" size={10} />{task.subtaskDone}/{task.subtaskCount}
            </span>
          )}
          {dateInfo && (
            <span className={`text-[10px] ${isCompleted ? "text-gray-600" : dateInfo.color}`}>
              {dateInfo.text}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
