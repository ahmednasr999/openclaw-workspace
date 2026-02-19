"use client";

import { useState } from "react";

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

const TYPE_LABELS: Record<string, string> = {
  Post: "📄",
  Article: "📰",
  Carousel: "🎠",
  Video: "🎬",
};

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
        <button onClick={(e) => { e.stopPropagation(); onEdit(); }} className="card-action-btn" title="Edit">✏️</button>
        <button onClick={handleDelete} className={`card-action-btn ${confirmDelete ? "" : "danger"}`} title={confirmDelete ? "Confirm?" : "Delete"}>
          {confirmDelete ? "❌" : "🗑"}
        </button>
      </div>

      {/* Tags */}
      <div className="flex items-center gap-2 mb-2">
        <span className={`tag ${PLATFORM_CLASS[post.platform] || "tag-x"}`}>{post.platform}</span>
        <span className="tag tag-task">{TYPE_LABELS[post.contentType] || "📄"} {post.contentType}</span>
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
        <div className="text-[10px] text-[var(--text-muted)] mb-1">🖼️ Has image</div>
      )}

      {/* Footer */}
      <div className="card-footer">
        <div className="flex items-center gap-2">
          <div className={`assignee-badge assignee-${post.assignee.toLowerCase()}`}>
            {post.assignee === "Ahmed" ? "A" : post.assignee === "OpenClaw" ? "O" : "B"}
          </div>
          <span className="text-[11px] text-[var(--text-muted)]">{post.assignee}</span>
        </div>
        {post.publishDate && (
          <span className="text-[10px] text-[var(--text-muted)]">📅 {formatDate(post.publishDate)}</span>
        )}
      </div>
    </div>
  );
}
