"use client";

import { useState, useEffect } from "react";
import { TaskCard } from "./TaskCard";

const COLUMNS = [
  { id: "Inbox", title: "📥 Inbox", color: "column-inbox" },
  { id: "My Tasks", title: "📝 My Tasks", color: "column-my-tasks" },
  { id: "OpenClaw Tasks", title: "🤖 OpenClaw Tasks", color: "column-openclaw" },
  { id: "In Progress", title: "🔄 In Progress", color: "column-progress" },
  { id: "Completed", title: "✅ Completed", color: "column-completed" },
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

export function TaskBoard() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Load tasks from API
  const loadTasks = async () => {
    try {
      const res = await fetch("/api/tasks");
      const data = await res.json();
      setTasks(data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Error loading tasks:", error);
    }
  };

  useEffect(() => {
    loadTasks();
    setLoaded(true);
    
    // Poll for changes every 10 seconds (less frequent, as backup)
    const interval = setInterval(loadTasks, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleDragStart = (e: React.DragEvent, taskId: number) => {
    e.dataTransfer.setData("taskId", taskId.toString());
  };

  const handleDrop = async (e: React.DragEvent, status: string) => {
    e.preventDefault();
    const taskId = parseInt(e.dataTransfer.getData("taskId"));
    
    if (taskId) {
      const completedDate = status === "Completed" ? new Date().toISOString() : undefined;
      
      // Update local state immediately
      setTasks((prev) =>
        prev.map((task) =>
          task.id === taskId
            ? { ...task, status, completedDate }
            : task
        )
      );

      // Update API
      try {
        await fetch("/api/tasks", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: taskId, status, completedDate }),
        });
      } catch (error) {
        console.error("Error updating task:", error);
        loadTasks();
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDelete = async (taskId: number) => {
    // Update local state immediately
    setTasks((prev) => prev.filter((task) => task.id !== taskId));

    // Update API
    try {
      await fetch(`/api/tasks?id=${taskId}`, { method: "DELETE" });
    } catch (error) {
      console.error("Error deleting task:", error);
      loadTasks();
    }
  };

  if (!loaded) {
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
                  key={task.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, task.id)}
                >
                  <TaskCard task={task} onDelete={() => handleDelete(task.id)} />
                </div>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}
