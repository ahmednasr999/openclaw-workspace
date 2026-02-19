"use client";

import { useState } from "react";
import { TaskBoard } from "@/components/TaskBoard";
import { Dashboard } from "@/components/Dashboard";
import { TaskForm } from "@/components/TaskForm";

export default function Home() {
  const [view, setView] = useState<"board" | "dashboard">("board");
  const [showForm, setShowForm] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleTaskAdded = () => {
    setRefreshKey((prev) => prev + 1);
  };

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <main className="min-h-screen bg-black text-white p-6">
      {/* Header */}
      <header className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Mission Control
          </h1>
          <p className="text-gray-400 mt-1">
            Task board for Ahmed & OpenClaw (SQLite)
          </p>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            title="Refresh"
          >
            🔄
          </button>
          <button
            onClick={() => setView("dashboard")}
            className={`px-4 py-2 rounded-lg transition-colors ${
              view === "dashboard" ? "bg-blue-600" : "bg-gray-800 hover:bg-gray-700"
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setView("board")}
            className={`px-4 py-2 rounded-lg transition-colors ${
              view === "board" ? "bg-blue-600" : "bg-gray-800 hover:bg-gray-700"
            }`}
          >
            Task Board
          </button>
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
          >
            + Add Task
          </button>
        </div>
      </header>

      {/* Main Content */}
      {view === "board" ? (
        <TaskBoard key={refreshKey} />
      ) : (
        <Dashboard key={refreshKey} />
      )}

      {/* Task Form Modal */}
      {showForm && (
        <TaskForm onClose={() => setShowForm(false)} onTaskAdded={handleTaskAdded} />
      )}
    </main>
  );
}
