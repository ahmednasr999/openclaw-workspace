"use client";

import { useState, useEffect } from "react";
import { TaskCard } from "./TaskCard";
import { useQuery, useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";

const COLUMNS = [
  { id: "Inbox", title: "📥 Inbox", color: "column-inbox" },
  { id: "My Tasks", title: "📝 My Tasks", color: "column-my-tasks" },
  { id: "OpenClaw Tasks", title: "🤖 OpenClaw Tasks", color: "column-openclaw" },
  { id: "In Progress", title: "🔄 In Progress", color: "column-progress" },
  { id: "Completed", title: "✅ Completed", color: "column-completed" },
];

export function TaskBoard() {
  const tasks = useQuery(api.tasks.getTasks);
  const updateStatus = useMutation(api.tasks.updateTaskStatus);
  const deleteTask = useMutation(api.tasks.deleteTask);

  const handleDragStart = (e: React.DragEvent, taskId: string) => {
    e.dataTransfer.setData("taskId", taskId);
  };

  const handleDrop = (e: React.DragEvent, status: string) => {
    e.preventDefault();
    const taskId = e.dataTransfer.getData("taskId");
    if (taskId) {
      updateStatus({
        id: taskId as any,
        status,
        completedDate: status === "Completed" ? new Date().toISOString() : undefined,
      });
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDelete = (taskId: string) => {
    deleteTask({ id: taskId as any });
  };

  if (tasks === undefined) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading tasks...</div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-5 gap-4">
      {COLUMNS.map((column) => (
        <div
          key={column.id}
          onDrop={(e) => handleDrop(e, column.id)}
          onDragOver={handleDragOver}
          className={`${column.color} rounded-xl p-4 min-h-[500px]`}
        >
          <h2 className="text-lg font-semibold mb-4 text-white">{column.title}</h2>
          
          <div className="space-y-3">
            {tasks
              .filter((task) => task.status === column.id)
              .map((task) => (
                <div
                  key={task._id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, task._id)}
                >
                  <TaskCard task={task} onDelete={() => handleDelete(task._id)} />
                </div>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}
