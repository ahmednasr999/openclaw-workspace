"use client";

import { useState, useRef, useCallback } from "react";
import { ContentCard } from "./ContentCard";
import { Icon } from "./Icon";

const COLUMNS = [
  { id: "Ideas", title: "Ideas", icon: "ideas" },
  { id: "Outline", title: "Outline", icon: "outline" },
  { id: "Draft", title: "Draft", icon: "draft" },
  { id: "Design", title: "Design", icon: "design" },
  { id: "Review", title: "Review", icon: "review" },
  { id: "Published", title: "Published", icon: "published" },
];

const PRIORITY_ORDER: Record<string, number> = { High: 0, Medium: 1, Low: 2 };

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

interface ContentBoardProps {
  posts: ContentPost[];
  onRefresh: () => void;
  onEditPost: (post: ContentPost) => void;
}

export function ContentBoard({ posts, onRefresh, onEditPost }: ContentBoardProps) {
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null);
  const [draggingId, setDraggingId] = useState<number | null>(null);

  const touchState = useRef<{
    postId: number | null;
    startX: number;
    startY: number;
    isDragging: boolean;
    ghost: HTMLDivElement | null;
  }>({ postId: null, startX: 0, startY: 0, isDragging: false, ghost: null });

  const sortPosts = (list: ContentPost[]) =>
    [...list].sort((a, b) => (PRIORITY_ORDER[a.priority] ?? 99) - (PRIORITY_ORDER[b.priority] ?? 99));

  const handleDragStart = (e: React.DragEvent, id: number) => {
    e.dataTransfer.setData("postId", id.toString());
    setDraggingId(id);
  };

  const handleDrop = async (e: React.DragEvent, status: string) => {
    e.preventDefault();
    setDragOverColumn(null);
    setDraggingId(null);
    const postId = parseInt(e.dataTransfer.getData("postId"));
    if (postId) await movePost(postId, status);
  };

  const handleTouchStart = useCallback((e: React.TouchEvent, postId: number) => {
    const touch = e.touches[0];
    touchState.current = { postId, startX: touch.clientX, startY: touch.clientY, isDragging: false, ghost: null };
  }, []);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    const ts = touchState.current;
    if (!ts.postId) return;
    const touch = e.touches[0];
    if (!ts.isDragging && Math.abs(touch.clientX - ts.startX) > 10) {
      ts.isDragging = true;
      const ghost = document.createElement("div");
      ghost.className = "fixed z-[100] px-3 py-2 rounded-lg text-white text-xs font-medium pointer-events-none";
      ghost.style.background = "var(--bg-card)";
      ghost.style.border = "1px solid var(--accent)";
      ghost.textContent = posts.find((p) => p.id === ts.postId)?.title || "";
      document.body.appendChild(ghost);
      ts.ghost = ghost;
    }
    if (ts.isDragging && ts.ghost) {
      e.preventDefault();
      ts.ghost.style.left = `${touch.clientX - 50}px`;
      ts.ghost.style.top = `${touch.clientY - 20}px`;
      const elements = document.elementsFromPoint(touch.clientX, touch.clientY);
      const col = elements.find((el) => el.getAttribute("data-column"));
      setDragOverColumn(col?.getAttribute("data-column") || null);
    }
  }, [posts]);

  const handleTouchEnd = useCallback(async () => {
    const ts = touchState.current;
    if (ts.ghost) document.body.removeChild(ts.ghost);
    if (ts.isDragging && ts.postId && dragOverColumn) await movePost(ts.postId, dragOverColumn);
    touchState.current = { postId: null, startX: 0, startY: 0, isDragging: false, ghost: null };
    setDragOverColumn(null);
  }, [dragOverColumn]);

  const movePost = async (postId: number, status: string) => {
    try {
      await fetch("/api/content", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: postId, status }),
      });
      onRefresh();
    } catch (error) {
      console.error("Error updating post:", error);
    }
  };

  const handleDelete = async (id: number) => {
    await fetch(`/api/content?id=${id}`, { method: "DELETE" });
    onRefresh();
  };

  return (
    <div className="board-grid" style={{ gridTemplateColumns: `repeat(${COLUMNS.length}, minmax(260px, 1fr))` }}>
      {COLUMNS.map((column) => {
        const columnPosts = sortPosts(posts.filter((p) => p.status === column.id));
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
              <span className="column-count">{columnPosts.length}</span>
            </div>

            <div className="column-body">
              {columnPosts.map((post) => (
                <div
                  key={post.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, post.id)}
                  onDragEnd={() => { setDraggingId(null); setDragOverColumn(null); }}
                  onTouchStart={(e) => handleTouchStart(e, post.id)}
                  onTouchMove={(e) => handleTouchMove(e)}
                  onTouchEnd={() => handleTouchEnd()}
                  className={draggingId === post.id ? "opacity-30" : ""}
                >
                  <ContentCard
                    post={post}
                    onDelete={() => handleDelete(post.id)}
                    onEdit={() => onEditPost(post)}
                  />
                </div>
              ))}
              {columnPosts.length === 0 && (
                <div className="column-empty">
                  {isDropTarget ? "Drop here" : "No posts"}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
