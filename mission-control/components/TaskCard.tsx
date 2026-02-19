"use client";

interface Task {
  _id: string;
  title: string;
  description?: string;
  assignee: string;
  priority: string;
  category: string;
  dueDate?: string;
}

interface TaskCardProps {
  task: Task;
  onDelete: () => void;
}

export function TaskCard({ task, onDelete }: TaskCardProps) {
  const priorityColors = {
    High: "priority-high",
    Medium: "priority-medium",
    Low: "priority-low",
  };

  const categoryIcons: Record<string, string> = {
    "Job Search": "🎯",
    Content: "📝",
    Networking: "🤝",
    Applications: "📋",
    Interviews: "🎤",
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 cursor-grab active:cursor-grabbing group relative">
      <div className="flex justify-between items-start mb-2">
        <span className="text-lg">{categoryIcons[task.category] || "📌"}</span>
        <div className="flex gap-2">
          <span className={`text-xs px-2 py-1 rounded ${priorityColors[task.priority as keyof typeof priorityColors] || "text-gray-400"}`}>
            {task.priority}
          </span>
        </div>
      </div>
      
      <h3 className="font-medium text-white mb-1">{task.title}</h3>
      
      {task.description && (
        <p className="text-sm text-gray-400 mb-3 line-clamp-2">{task.description}</p>
      )}
      
      <div className="flex justify-between items-center text-xs text-gray-500">
        <span>{task.assignee}</span>
        {task.dueDate && <span>📅 {task.dueDate}</span>}
      </div>
      
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300"
      >
        ✕
      </button>
    </div>
  );
}
