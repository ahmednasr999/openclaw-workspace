"use client";

interface Task {
  id: number;
  title: string;
  description?: string;
  assignee: string;
  priority: string;
  category: string;
  dueDate?: string;
  createdAt: string;
}

interface TaskCardProps {
  task: Task;
  onDelete: () => void;
  onEdit: () => void;
}

export function TaskCard({ task, onDelete, onEdit }: TaskCardProps) {
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

  // Format date
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

  return (
    <div 
      className="task-card glass-strong rounded-lg p-3 cursor-grab active:cursor-grabbing group relative"
      onClick={onEdit}
    >
      {/* Top row: category + priority */}
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm">{categoryIcons[task.category] || "📌"}</span>
        <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${priority.class}`}>
          {task.priority}
        </span>
      </div>
      
      {/* Title */}
      <h3 className="text-sm font-medium text-white mb-1 leading-snug">{task.title}</h3>
      
      {/* Description */}
      {task.description && (
        <p className="text-xs text-gray-500 mb-2 line-clamp-2 leading-relaxed">{task.description}</p>
      )}
      
      {/* Footer: assignee + due date */}
      <div className="flex justify-between items-center mt-2 pt-2 border-t border-white/5">
        <span className={`text-[10px] font-medium ${assigneeColor}`}>
          {task.assignee === "Ahmed" ? "👤 Ahmed" : 
           task.assignee === "OpenClaw" ? "🤖 OpenClaw" : "👥 Both"}
        </span>
        {task.dueDate && (() => {
          const { text, color } = formatDate(task.dueDate);
          return <span className={`text-[10px] ${color}`}>📅 {text}</span>;
        })()}
      </div>
      
      {/* Actions overlay */}
      <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
        <button
          onClick={(e) => { e.stopPropagation(); onEdit(); }}
          className="w-6 h-6 rounded flex items-center justify-center text-xs hover:bg-white/10 text-gray-400 hover:text-white"
          title="Edit"
        >
          ✏️
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
          className="w-6 h-6 rounded flex items-center justify-center text-xs hover:bg-red-500/20 text-gray-400 hover:text-red-400"
          title="Delete"
        >
          🗑️
        </button>
      </div>
    </div>
  );
}
