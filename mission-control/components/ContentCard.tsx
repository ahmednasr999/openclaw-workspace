"use client";

import { useState } from "react";
import { Icon } from "./Icon";

interface ContentPost {
  id: number;
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
  updatedAt?: string;
}

interface ContentCardProps {
  post: ContentPost;
  onDelete: () => void;
  onEdit: () => void;
}

const PLATFORM_CLASS: Record<string, string> = {
  LinkedIn: "tag-linkedin",
  X: "tag-x",
};

const TYPE_LABELS: Record<string, { icon: string; label: string }> = {
  Post: { icon: "documentAgent", label: "Post" },
  Article: { icon: "📰", label: "Article" },
  Carousel: { icon: "🎠", label: "Carousel" },
  Video: { icon: "video", label: "Video" },
};

// Same AGENT_MAP pattern as TaskCard
const AGENT_MAP: Record<string, { initial: string; class: string }> = {
  "Ahmed": { initial: "A", class: "assignee-ahmed" },
  "OpenClaw": { initial: "targetAgent", class: "assignee-openclaw" },
  "NASR": { initial: "targetAgent", class: "assignee-openclaw" },
  "NASR (Coder)": { initial: "codeAgent", class: "assignee-openclaw" },
  "NASR (Writer)": { initial: "penAgent", class: "assignee-openclaw" },
  "NASR (Research)": { initial: "searchAgent", class: "assignee-openclaw" },
  "NASR (CV)": { initial: "documentAgent", class: "assignee-openclaw" },
  "QA Agent": { initial: "shieldAgent", class: "assignee-openclaw" },
  "Both": { initial: "B", class: "assignee-both" },
};

function getAssigneeInitial(assignee: string): string {
  return AGENT_MAP[assignee]?.initial || assignee.charAt(0).toUpperCase();
}

function getAssigneeBadgeClass(assignee: string): string {
  return AGENT_MAP[assignee]?.class || "assignee-openclaw";
}

export function ContentCard({ post, onDelete, onEdit }: ContentCardProps) {
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirmDelete) { onDelete(); }
    else { setConfirmDelete(true); setTimeout(() => setConfirmDelete(false), 3000); }
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  return (
    <div className="task-card" onClick={onEdit}>
      <div className="card-actions">
        <button onClick={(e) => { e.stopPropagation(); onEdit(); }} className="card-action-btn" title="Edit">
          <Icon name="edit" size={14} />
        </button>
        <button onClick={handleDelete} className={`card-action-btn ${confirmDelete ? "" : "danger"}`} title={confirmDelete ? "Confirm?" : "Delete"}>
          {confirmDelete ? "✕" : <Icon name="delete" size={14} />}
        </button>
      </div>

      {/* Tags */}
      <div className="flex items-center gap-2 mb-2">
        <span className={`tag ${PLATFORM_CLASS[post.platform] || "tag-x"}`}>{post.platform}</span>
        <span className="tag tag-task">{TYPE_LABELS[post.contentType]?.icon || "documentAgent"} {post.contentType}</span>
        <div className={`priority-dot priority-dot-${post.priority.toLowerCase()}`} title={post.priority} />
      </div>

      {/* Title */}
      <div className="task-card-title">{post.title}</div>

      {/* Hook preview */}
      {post.hook && (
        <div className="task-card-desc" style={{ WebkitLineClamp: 2 }}>
          {post.hook}
        </div>
      )}

      {/* Image indicator */}
      {post.imageUrl && (
        <div className="text-[10px] text-[var(--text-muted)] mb-1 flex items-center gap-1">
          <Icon name="image" size={12} /> Has image
        </div>
      )}

      {/* Footer */}
      <div className="card-footer">
        <div className="flex items-center gap-2">
          <div className={`assignee-badge ${getAssigneeBadgeClass(post.assignee)}`}>
            {getAssigneeInitial(post.assignee)}
          </div>
          <span className="text-[11px] text-[var(--text-muted)]">{post.assignee}</span>
        </div>
        {post.publishDate && (
          <span className="text-[10px] text-[var(--text-muted)] flex items-center gap-1">
            <Icon name="calendar" size={12} />{formatDate(post.publishDate)}
          </span>
        )}
      </div>
    </div>
  );
}
