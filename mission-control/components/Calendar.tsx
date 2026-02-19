"use client";

import { useState, useEffect, useMemo } from "react";
import { Icon } from "./Icon";

interface ScheduledTask {
  id: number;
  taskId?: number;
  title: string;
  scheduledDate: string;
  scheduledTime?: string;
  type: string;
  status: string;
  notes?: string;
}

interface CronJob {
  name: string;
  schedule: string;
  nextRun?: string;
  lastRun?: string;
  lastStatus?: string;
}

export function Calendar() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<"month" | "week" | "day">("month");
  const [scheduledTasks, setScheduledTasks] = useState<ScheduledTask[]>([]);
  const [cronJobs, setCronJobs] = useState<CronJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState<ScheduledTask | null>(null);
  const [showCronPanel, setShowCronPanel] = useState(false);

  useEffect(() => {
    fetchData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [currentDate, view]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth();
      const startDate = new Date(year, month, 1).toISOString().split("T")[0];
      const endDate = new Date(year, month + 1, 0).toISOString().split("T")[0];
      
      const [tasksRes, cronRes] = await Promise.all([
        fetch(`/api/scheduled?startDate=${startDate}&endDate=${endDate}`),
        fetch("/api/cron-jobs")
      ]);
      
      const tasksData = await tasksRes.json();
      const cronData = await cronRes.json();
      
      setScheduledTasks(tasksData);
      setCronJobs(cronData);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  };

  const daysInMonth = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const days: (Date | null)[] = [];
    for (let i = 0; i < firstDay.getDay(); i++) days.push(null);
    for (let i = 1; i <= lastDay.getDate(); i++) days.push(new Date(year, month, i));
    return days;
  }, [currentDate]);

  const weekDays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  const getTasksForDate = (date: Date) => {
    const dateStr = date.toISOString().split("T")[0];
    return scheduledTasks.filter(t => t.scheduledDate === dateStr);
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" });
  };

  const navigate = (direction: "prev" | "next") => {
    const newDate = new Date(currentDate);
    if (view === "month") {
      newDate.setMonth(newDate.getMonth() + (direction === "next" ? 1 : -1));
    } else if (view === "week") {
      newDate.setDate(newDate.getDate() + (direction === "next" ? 7 : -7));
    } else {
      newDate.setDate(newDate.getDate() + (direction === "next" ? 1 : -1));
    }
    setCurrentDate(newDate);
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "task": return { bg: "bg-blue-500", text: "text-blue-400", border: "border-blue-500/30" };
      case "content": return { bg: "bg-purple-500", text: "text-purple-400", border: "border-purple-500/30" };
      case "cron": return { bg: "bg-amber-500", text: "text-amber-400", border: "border-amber-500/30" };
      default: return { bg: "bg-gray-500", text: "text-gray-400", border: "border-gray-500/30" };
    }
  };

  // Weekly summary
  const weeklyStats = useMemo(() => {
    const now = new Date();
    const weekStart = new Date(now);
    weekStart.setDate(now.getDate() - now.getDay());
    weekStart.setHours(0, 0, 0, 0);
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 7);
    
    const weekTasks = scheduledTasks.filter(t => {
      const d = new Date(t.scheduledDate);
      return d >= weekStart && d < weekEnd;
    });
    
    return {
      total: weekTasks.length,
      completed: weekTasks.filter(t => t.status === "completed").length,
      scheduled: weekTasks.filter(t => t.status === "scheduled").length,
      missed: weekTasks.filter(t => t.status === "missed").length,
    };
  }, [scheduledTasks]);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-[rgba(255,255,255,0.06)]">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-white">{formatDate(currentDate)}</h2>
          <div className="flex gap-1">
            <button onClick={() => navigate("prev")} className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-all">
              <Icon name="arrowLeft" size={18} />
            </button>
            <button onClick={() => navigate("next")} className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-all">
              <Icon name="arrowRight" size={18} />
            </button>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setShowCronPanel(!showCronPanel)}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all border ${
              showCronPanel ? "bg-[rgba(245,158,11,0.15)] border-amber-500/30 text-amber-400" : "text-gray-400 hover:text-white border-[rgba(255,255,255,0.08)]"
            }`}
          >
            <Icon name="clock" size={14} className="inline mr-1" />
            Cron Jobs
          </button>
          <div className="flex gap-1 bg-[rgba(255,255,255,0.03)] rounded-lg p-1 border border-[rgba(255,255,255,0.08)]">
            {(["month", "week", "day"] as const).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
                  view === v ? "bg-[rgba(124,92,252,0.15)] text-[#a78bfa]" : "text-gray-500 hover:text-white"
                }`}
              >
                {v.charAt(0).toUpperCase() + v.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Weekly Summary */}
      <div className="flex items-center gap-4 px-6 py-3 border-b border-[rgba(255,255,255,0.04)] bg-[rgba(255,255,255,0.02)]">
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">This Week</span>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-gray-500" />
            <span className="text-xs text-gray-400">Total: {weeklyStats.total}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-xs text-green-400">Done: {weeklyStats.completed}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-blue-500" />
            <span className="text-xs text-blue-400">Scheduled: {weeklyStats.scheduled}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-xs text-red-400">Missed: {weeklyStats.missed}</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Calendar */}
        <div className="flex-1 overflow-auto p-6">
          {view === "month" ? (
            <div className="grid grid-cols-7 gap-1">
              {weekDays.map((day) => (
                <div key={day} className="text-center text-xs font-medium text-gray-500 py-3">{day}</div>
              ))}
              {daysInMonth.map((date, i) => {
                const tasks = date ? getTasksForDate(date) : [];
                const isToday = date && new Date().toDateString() === date.toDateString();
                return (
                  <div
                    key={i}
                    className={`min-h-[100px] p-2 rounded-lg border ${
                      date 
                        ? `bg-[rgba(255,255,255,0.02)] ${isToday ? "border-indigo-500/50" : "border-[rgba(255,255,255,0.04)]"}` 
                        : "bg-transparent border-transparent"
                    }`}
                  >
                    {date && (
                      <>
                        <div className={`text-xs mb-2 ${isToday ? "text-indigo-400 font-semibold" : "text-gray-500"}`}>
                          {date.getDate()}
                        </div>
                        <div className="space-y-1">
                          {tasks.slice(0, 4).map((task) => {
                            const colors = getTypeColor(task.type);
                            return (
                              <button
                                key={task.id}
                                onClick={() => setSelectedTask(task)}
                                className={`w-full flex items-center gap-1.5 px-2 py-1 rounded text-left text-[10px] border ${colors.border} ${colors.bg}/10 hover:${colors.bg}/20 transition-all`}
                              >
                                <div className={`w-1.5 h-1.5 rounded-full ${colors.bg}`} />
                                <span className={`${colors.text} truncate flex-1`}>{task.title}</span>
                              </button>
                            );
                          })}
                          {tasks.length > 4 && (
                            <div className="text-[10px] text-gray-600 px-2">+{tasks.length - 4} more</div>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          ) : view === "week" ? (
            <div className="flex gap-2 h-full">
              {/* Time column */}
              <div className="w-16 flex-shrink-0">
                {Array.from({ length: 24 }, (_, hour) => (
                  <div key={hour} className="h-12 text-[10px] text-gray-600 text-right pr-2 -mt-2">{hour === 0 ? "12 AM" : hour < 12 ? `${hour} AM` : hour === 12 ? "12 PM" : `${hour - 12} PM`}</div>
                ))}
              </div>
              {/* Days columns */}
              <div className="flex-1 grid grid-cols-7 gap-1">
                {Array.from({ length: 7 }, (_, dayOffset) => {
                  const dayDate = new Date(currentDate);
                  dayDate.setDate(currentDate.getDate() - currentDate.getDay() + dayOffset);
                  const dateStr = dayDate.toISOString().split("T")[0];
                  const dayTasks = scheduledTasks.filter(t => t.scheduledDate === dateStr);
                  const isToday = new Date().toDateString() === dayDate.toDateString();
                  return (
                    <div key={dayOffset} className={`h-full rounded-lg ${isToday ? "bg-indigo-500/5 border-indigo-500/20" : "bg-[rgba(255,255,255,0.02)]"} border border-[rgba(255,255,255,0.04)]`}>
                      <div className={`text-xs text-center py-2 border-b border-[rgba(255,255,255,0.04)] ${isToday ? "text-indigo-400 font-semibold" : "text-gray-500"}`}>
                        {weekDays[dayOffset]} {dayDate.getDate()}
                      </div>
                      <div className="p-1 space-y-1">
                        {dayTasks.map((task) => {
                          const colors = getTypeColor(task.type);
                          return (
                            <button
                              key={task.id}
                              onClick={() => setSelectedTask(task)}
                              className={`w-full px-2 py-1 rounded text-[10px] text-left ${colors.bg}/10 border ${colors.border} ${colors.text} truncate hover:${colors.bg}/20 transition-all`}
                            >
                              {task.scheduledTime && <span className="opacity-60 mr-1">{task.scheduledTime}</span>}
                              {task.title}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="space-y-0">
              {Array.from({ length: 24 }, (_, hour) => {
                const hourStr = `${hour.toString().padStart(2, "0")}:00`;
                const hourTasks = scheduledTasks.filter(t => t.scheduledTime?.startsWith(hourStr));
                return (
                  <div key={hour} className="flex border-b border-[rgba(255,255,255,0.04)] h-12">
                    <div className="w-20 text-xs text-gray-500 py-3">{hour === 0 ? "12:00 AM" : hour < 12 ? `${hour}:00 AM` : hour === 12 ? "12:00 PM" : `${hour - 12}:00 PM`}</div>
                    <div className="flex-1 relative">
                      {hourTasks.map((task) => {
                        const colors = getTypeColor(task.type);
                        return (
                          <button
                            key={task.id}
                            onClick={() => setSelectedTask(task)}
                            className={`absolute left-0 right-0 mx-1 px-3 py-1.5 rounded text-xs ${colors.bg}/10 border ${colors.border} ${colors.text} truncate hover:${colors.bg}/20 transition-all`}
                          >
                            {task.title}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Cron Jobs Panel */}
        {showCronPanel && (
          <div className="w-80 border-l border-[rgba(255,255,255,0.06)] bg-[rgba(255,255,255,0.02)] overflow-auto">
            <div className="p-4 border-b border-[rgba(255,255,255,0.06)]">
              <h3 className="text-sm font-semibold text-white">Cron Jobs</h3>
              <p className="text-[10px] text-gray-500 mt-1">Automated scheduled tasks</p>
            </div>
            <div className="p-4 space-y-3">
              {cronJobs.length === 0 ? (
                <div className="text-xs text-gray-600 text-center py-4">No cron jobs configured</div>
              ) : (
                cronJobs.map((job, i) => (
                  <div key={i} className="p-3 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)]">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-white">{job.name}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        job.lastStatus === "success" ? "bg-green-500/20 text-green-400" : 
                        job.lastStatus === "failed" ? "bg-red-500/20 text-red-400" : "bg-gray-500/20 text-gray-400"
                      }`}>
                        {job.lastStatus || "pending"}
                      </span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-[10px] text-gray-500">
                        <Icon name="clock" size={10} />
                        <span>Schedule: {job.schedule}</span>
                      </div>
                      <div className="flex items-center gap-2 text-[10px] text-gray-500">
                        <Icon name="arrowRight" size={10} />
                        <span>Next: {job.nextRun || "unknown"}</span>
                      </div>
                      <div className="flex items-center gap-2 text-[10px] text-gray-500">
                        <Icon name="check" size={10} />
                        <span>Last: {job.lastRun || "never"}</span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* Task Detail Modal */}
      {selectedTask && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedTask(null)}>
          <div className="bg-[#12121a] border border-[rgba(255,255,255,0.1)] rounded-xl w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded ${getTypeColor(selectedTask.type).bg}/20 ${getTypeColor(selectedTask.type).text} border ${getTypeColor(selectedTask.type).border}`}>
                    {selectedTask.type}
                  </span>
                  <span className={`text-[10px] px-2 py-0.5 rounded ${
                    selectedTask.status === "completed" ? "bg-green-500/20 text-green-400 border border-green-500/30" :
                    selectedTask.status === "missed" ? "bg-red-500/20 text-red-400 border border-red-500/30" :
                    "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                  }`}>
                    {selectedTask.status}
                  </span>
                </div>
                <h3 className="text-base font-semibold text-white">{selectedTask.title}</h3>
              </div>
              <button onClick={() => setSelectedTask(null)} className="text-gray-500 hover:text-white">
                <Icon name="close" size={18} />
              </button>
            </div>
            <div className="space-y-3 text-sm">
              <div className="flex items-center gap-2 text-gray-400">
                <Icon name="calendar" size={14} />
                <span>{new Date(selectedTask.scheduledDate).toLocaleDateString()}</span>
                {selectedTask.scheduledTime && <span>at {selectedTask.scheduledTime}</span>}
              </div>
              {selectedTask.notes && (
                <p className="text-gray-500 text-xs">{selectedTask.notes}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-4 px-6 py-3 border-t border-[rgba(255,255,255,0.06)]">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-blue-500" />
          <span className="text-xs text-gray-500">Task</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-purple-500" />
          <span className="text-xs text-gray-500">Content</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-amber-500" />
          <span className="text-xs text-gray-500">Cron</span>
        </div>
        <div className="flex-1" />
        <span className="text-xs text-gray-600">{loading ? "Updating..." : "Live"}</span>
      </div>
    </div>
  );
}
