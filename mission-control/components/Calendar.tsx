"use client";

import { useState, useEffect, useMemo, useCallback, useRef } from "react";
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
  id?: string;
  name: string;
  schedule: string;
  nextRun?: string;
  lastRun?: string;
  lastStatus?: string;
  enabled?: boolean;
}

// Pre-built Tailwind class maps to avoid dynamic class purging issues
const TYPE_STYLES = {
  task: {
    bg: "bg-blue-500",
    bgLight: "bg-blue-500/10",
    bgHover: "hover:bg-blue-500/20",
    text: "text-blue-400",
    border: "border-blue-500/30",
    dot: "bg-blue-500",
  },
  content: {
    bg: "bg-purple-500",
    bgLight: "bg-purple-500/10",
    bgHover: "hover:bg-purple-500/20",
    text: "text-purple-400",
    border: "border-purple-500/30",
    dot: "bg-purple-500",
  },
  cron: {
    bg: "bg-amber-500",
    bgLight: "bg-amber-500/10",
    bgHover: "hover:bg-amber-500/20",
    text: "text-amber-400",
    border: "border-amber-500/30",
    dot: "bg-amber-500",
  },
  default: {
    bg: "bg-gray-500",
    bgLight: "bg-gray-500/10",
    bgHover: "hover:bg-gray-500/20",
    text: "text-gray-400",
    border: "border-gray-500/30",
    dot: "bg-gray-500",
  },
} as const;

const STATUS_STYLES = {
  completed: "bg-green-500/20 text-green-400 border border-green-500/30",
  missed: "bg-red-500/20 text-red-400 border border-red-500/30",
  scheduled: "bg-blue-500/20 text-blue-400 border border-blue-500/30",
  default: "bg-gray-500/20 text-gray-400 border border-gray-500/30",
} as const;

// Cairo timezone offset helper - formats dates in Africa/Cairo
function toCairoDateStr(date: Date): string {
  return date.toLocaleDateString("en-CA", { timeZone: "Africa/Cairo" }); // YYYY-MM-DD
}

function nowCairo(): Date {
  // Return a Date object representing "now" - comparisons use Cairo strings
  return new Date();
}

function todayCairoStr(): string {
  return toCairoDateStr(new Date());
}

export function Calendar() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<"month" | "week" | "day">("month");
  const [scheduledTasks, setScheduledTasks] = useState<ScheduledTask[]>([]);
  const [cronJobs, setCronJobs] = useState<CronJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState<ScheduledTask | null>(null);
  const [showCronPanel, setShowCronPanel] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createDate, setCreateDate] = useState("");
  const [editingTask, setEditingTask] = useState<ScheduledTask | null>(null);
  const weekTimeRef = useRef<HTMLDivElement>(null);
  const weekDaysRef = useRef<HTMLDivElement>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth();
      const startDate = new Date(year, month, 1).toISOString().split("T")[0];
      const endDate = new Date(year, month + 1, 0).toISOString().split("T")[0];

      const [tasksRes, cronRes] = await Promise.all([
        fetch(`/api/scheduled?startDate=${startDate}&endDate=${endDate}`),
        fetch("/api/cron-jobs"),
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
  }, [currentDate]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData, view]);

  // Sync scroll between time column and day columns in week view
  useEffect(() => {
    const timeEl = weekTimeRef.current;
    const daysEl = weekDaysRef.current;
    if (!timeEl || !daysEl) return;

    const syncScroll = (source: HTMLElement, target: HTMLElement) => () => {
      target.scrollTop = source.scrollTop;
    };

    const onTimeScroll = syncScroll(timeEl, daysEl);
    const onDaysScroll = syncScroll(daysEl, timeEl);

    timeEl.addEventListener("scroll", onTimeScroll);
    daysEl.addEventListener("scroll", onDaysScroll);
    return () => {
      timeEl.removeEventListener("scroll", onTimeScroll);
      daysEl.removeEventListener("scroll", onDaysScroll);
    };
  }, [view]);

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
    const dateStr = toCairoDateStr(date);
    return scheduledTasks.filter((t) => t.scheduledDate === dateStr);
  };

  const getTypeStyles = (type: string) => {
    return TYPE_STYLES[type as keyof typeof TYPE_STYLES] || TYPE_STYLES.default;
  };

  const getStatusStyle = (status: string) => {
    return STATUS_STYLES[status as keyof typeof STATUS_STYLES] || STATUS_STYLES.default;
  };

  // Smart header text based on view
  const headerText = useMemo(() => {
    if (view === "month") {
      return currentDate.toLocaleDateString("en-US", { year: "numeric", month: "long", timeZone: "Africa/Cairo" });
    } else if (view === "week") {
      const weekStart = new Date(currentDate);
      weekStart.setDate(currentDate.getDate() - currentDate.getDay());
      const weekEnd = new Date(weekStart);
      weekEnd.setDate(weekStart.getDate() + 6);
      const startStr = weekStart.toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "Africa/Cairo" });
      const endStr = weekEnd.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "Africa/Cairo" });
      return `Week of ${startStr} - ${endStr}`;
    } else {
      return currentDate.toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric", timeZone: "Africa/Cairo" });
    }
  }, [currentDate, view]);

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

  const goToToday = () => setCurrentDate(new Date());

  // Weekly summary
  const weeklyStats = useMemo(() => {
    const now = new Date();
    const weekStart = new Date(now);
    weekStart.setDate(now.getDate() - now.getDay());
    weekStart.setHours(0, 0, 0, 0);
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 7);

    const weekTasks = scheduledTasks.filter((t) => {
      const d = new Date(t.scheduledDate + "T00:00:00");
      return d >= weekStart && d < weekEnd;
    });

    return {
      total: weekTasks.length,
      completed: weekTasks.filter((t) => t.status === "completed").length,
      scheduled: weekTasks.filter((t) => t.status === "scheduled").length,
      missed: weekTasks.filter((t) => t.status === "missed").length,
    };
  }, [scheduledTasks]);

  // Get tasks for a specific hour range in day view
  const getTasksForHour = (hour: number) => {
    const dateStr = toCairoDateStr(currentDate);
    return scheduledTasks.filter((t) => {
      if (t.scheduledDate !== dateStr) return false;
      if (!t.scheduledTime) return hour === 0; // Unscheduled tasks show at midnight
      const taskHour = parseInt(t.scheduledTime.split(":")[0], 10);
      return taskHour === hour;
    });
  };

  // CRUD operations
  const handleCreateTask = async (data: {
    title: string;
    scheduledDate: string;
    scheduledTime?: string;
    type: string;
    notes?: string;
  }) => {
    try {
      await fetch("/api/scheduled", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...data, status: "scheduled" }),
      });
      setShowCreateForm(false);
      setCreateDate("");
      fetchData();
    } catch (error) {
      console.error("Failed to create task:", error);
    }
  };

  const handleUpdateTask = async (id: number, fields: Record<string, any>) => {
    try {
      await fetch(`/api/scheduled?id=${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(fields),
      });
      setSelectedTask(null);
      setEditingTask(null);
      fetchData();
    } catch (error) {
      console.error("Failed to update task:", error);
    }
  };

  const handleDeleteTask = async (id: number) => {
    try {
      await fetch(`/api/scheduled?id=${id}`, { method: "DELETE" });
      setSelectedTask(null);
      fetchData();
    } catch (error) {
      console.error("Failed to delete task:", error);
    }
  };

  const handleDateCellClick = (date: Date) => {
    setCreateDate(toCairoDateStr(date));
    setShowCreateForm(true);
  };

  const todayStr = todayCairoStr();

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-[rgba(255,255,255,0.06)]">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-white">{headerText}</h2>
          <div className="flex gap-1">
            <button onClick={() => navigate("prev")} className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-all">
              <Icon name="arrowLeft" size={18} />
            </button>
            <button onClick={goToToday} className="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-400 hover:text-white hover:bg-white/5 transition-all border border-[rgba(255,255,255,0.08)]">
              Today
            </button>
            <button onClick={() => navigate("next")} className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-all">
              <Icon name="arrowRight" size={18} />
            </button>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => { setCreateDate(toCairoDateStr(currentDate)); setShowCreateForm(true); }}
            className="px-4 py-2 rounded-lg text-xs font-medium bg-[rgba(124,92,252,0.15)] border border-indigo-500/30 text-indigo-400 hover:bg-[rgba(124,92,252,0.25)] transition-all"
          >
            <Icon name="plus" size={14} className="inline mr-1" />
            Add Task
          </button>
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
                const isToday = date ? toCairoDateStr(date) === todayStr : false;
                return (
                  <div
                    key={i}
                    className={`min-h-[100px] p-2 rounded-lg border group ${
                      date
                        ? `bg-[rgba(255,255,255,0.02)] ${isToday ? "border-indigo-500/50" : "border-[rgba(255,255,255,0.04)]"} cursor-pointer`
                        : "bg-transparent border-transparent"
                    }`}
                    onDoubleClick={() => date && handleDateCellClick(date)}
                  >
                    {date && (
                      <>
                        <div className="flex items-center justify-between mb-2">
                          <span className={`text-xs ${isToday ? "text-indigo-400 font-semibold" : "text-gray-500"}`}>
                            {date.getDate()}
                          </span>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleDateCellClick(date); }}
                            className="opacity-0 group-hover:opacity-100 w-5 h-5 flex items-center justify-center rounded hover:bg-white/10 text-gray-500 hover:text-white transition-all"
                            title="Add task"
                          >
                            <Icon name="plus" size={12} />
                          </button>
                        </div>
                        <div className="space-y-1">
                          {tasks.slice(0, 4).map((task) => {
                            const styles = getTypeStyles(task.type);
                            return (
                              <button
                                key={task.id}
                                onClick={(e) => { e.stopPropagation(); setSelectedTask(task); }}
                                className={`w-full flex items-center gap-1.5 px-2 py-1 rounded text-left text-[10px] border ${styles.border} ${styles.bgLight} ${styles.bgHover} transition-all`}
                              >
                                <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${styles.dot}`} />
                                <span className={`${styles.text} truncate flex-1`}>{task.title}</span>
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
            <div className="flex h-full">
              {/* Time column */}
              <div ref={weekTimeRef} className="w-16 flex-shrink-0 overflow-hidden">
                {Array.from({ length: 24 }, (_, hour) => (
                  <div key={hour} className="h-12 text-[10px] text-gray-600 text-right pr-2 -mt-2">
                    {hour === 0 ? "12 AM" : hour < 12 ? `${hour} AM` : hour === 12 ? "12 PM" : `${hour - 12} PM`}
                  </div>
                ))}
              </div>
              {/* Days columns - synced scroll */}
              <div ref={weekDaysRef} className="flex-1 grid grid-cols-7 gap-1 overflow-auto">
                {Array.from({ length: 7 }, (_, dayOffset) => {
                  const dayDate = new Date(currentDate);
                  dayDate.setDate(currentDate.getDate() - currentDate.getDay() + dayOffset);
                  const dateStr = toCairoDateStr(dayDate);
                  const dayTasks = scheduledTasks.filter((t) => t.scheduledDate === dateStr);
                  const isToday = dateStr === todayStr;
                  return (
                    <div
                      key={dayOffset}
                      className={`rounded-lg ${isToday ? "bg-indigo-500/5 border-indigo-500/20" : "bg-[rgba(255,255,255,0.02)]"} border border-[rgba(255,255,255,0.04)]`}
                    >
                      <div className={`text-xs text-center py-2 border-b border-[rgba(255,255,255,0.04)] flex items-center justify-center gap-1 ${isToday ? "text-indigo-400 font-semibold" : "text-gray-500"}`}>
                        {weekDays[dayOffset]} {dayDate.getDate()}
                        <button
                          onClick={() => handleDateCellClick(dayDate)}
                          className="opacity-0 hover:opacity-100 w-4 h-4 flex items-center justify-center rounded hover:bg-white/10 text-gray-500 hover:text-white transition-all"
                        >
                          <Icon name="plus" size={10} />
                        </button>
                      </div>
                      <div className="p-1 space-y-1">
                        {dayTasks.map((task) => {
                          const styles = getTypeStyles(task.type);
                          return (
                            <button
                              key={task.id}
                              onClick={() => setSelectedTask(task)}
                              className={`w-full px-2 py-1 rounded text-[10px] text-left ${styles.bgLight} border ${styles.border} ${styles.text} truncate ${styles.bgHover} transition-all`}
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
            /* Day view */
            <div className="space-y-0">
              {Array.from({ length: 24 }, (_, hour) => {
                const hourTasks = getTasksForHour(hour);
                return (
                  <div
                    key={hour}
                    className="flex border-b border-[rgba(255,255,255,0.04)] min-h-[48px] group cursor-pointer"
                    onDoubleClick={() => {
                      setCreateDate(toCairoDateStr(currentDate));
                      setShowCreateForm(true);
                    }}
                  >
                    <div className="w-20 text-xs text-gray-500 py-3 flex-shrink-0">
                      {hour === 0 ? "12:00 AM" : hour < 12 ? `${hour}:00 AM` : hour === 12 ? "12:00 PM" : `${hour - 12}:00 PM`}
                    </div>
                    <div className="flex-1 relative py-1 space-y-1">
                      {hourTasks.map((task) => {
                        const styles = getTypeStyles(task.type);
                        return (
                          <button
                            key={task.id}
                            onClick={() => setSelectedTask(task)}
                            className={`w-full px-3 py-1.5 rounded text-xs text-left ${styles.bgLight} border ${styles.border} ${styles.text} truncate ${styles.bgHover} transition-all`}
                          >
                            {task.scheduledTime && <span className="opacity-60 mr-1">{task.scheduledTime}</span>}
                            {task.title}
                          </button>
                        );
                      })}
                      <button
                        onClick={() => {
                          setCreateDate(toCairoDateStr(currentDate));
                          setShowCreateForm(true);
                        }}
                        className="opacity-0 group-hover:opacity-100 absolute top-1 right-1 w-5 h-5 flex items-center justify-center rounded hover:bg-white/10 text-gray-500 hover:text-white transition-all"
                      >
                        <Icon name="plus" size={12} />
                      </button>
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
              <p className="text-[10px] text-gray-500 mt-1">Live from OpenClaw scheduler</p>
            </div>
            <div className="p-4 space-y-3">
              {cronJobs.length === 0 ? (
                <div className="text-xs text-gray-600 text-center py-4">No cron jobs configured</div>
              ) : (
                cronJobs.map((job, i) => (
                  <div key={job.id || i} className="p-3 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)]">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-white">{job.name}</span>
                      <div className="flex items-center gap-2">
                        {job.enabled === false && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-500/20 text-gray-500">disabled</span>
                        )}
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                          job.lastStatus === "success" ? "bg-green-500/20 text-green-400" :
                          job.lastStatus === "failed" ? "bg-red-500/20 text-red-400" : "bg-gray-500/20 text-gray-400"
                        }`}>
                          {job.lastStatus || "pending"}
                        </span>
                      </div>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-[10px] text-gray-500">
                        <Icon name="clock" size={10} />
                        <span>Schedule: {job.schedule}</span>
                      </div>
                      {job.nextRun && (
                        <div className="flex items-center gap-2 text-[10px] text-gray-500">
                          <Icon name="arrowRight" size={10} />
                          <span>Next: {new Date(job.nextRun).toLocaleString("en-US", { timeZone: "Africa/Cairo", dateStyle: "short", timeStyle: "short" })}</span>
                        </div>
                      )}
                      {job.lastRun && (
                        <div className="flex items-center gap-2 text-[10px] text-gray-500">
                          <Icon name="check" size={10} />
                          <span>Last: {new Date(job.lastRun).toLocaleString("en-US", { timeZone: "Africa/Cairo", dateStyle: "short", timeStyle: "short" })}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* Task Detail Modal - with edit/delete/complete */}
      {selectedTask && !editingTask && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedTask(null)}>
          <div className="bg-[#12121a] border border-[rgba(255,255,255,0.1)] rounded-xl w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded ${getTypeStyles(selectedTask.type).bgLight} ${getTypeStyles(selectedTask.type).text} border ${getTypeStyles(selectedTask.type).border}`}>
                    {selectedTask.type}
                  </span>
                  <span className={`text-[10px] px-2 py-0.5 rounded ${getStatusStyle(selectedTask.status)}`}>
                    {selectedTask.status}
                  </span>
                </div>
                <h3 className="text-base font-semibold text-white">{selectedTask.title}</h3>
              </div>
              <button onClick={() => setSelectedTask(null)} className="text-gray-500 hover:text-white">
                <Icon name="close" size={18} />
              </button>
            </div>
            <div className="space-y-3 text-sm mb-6">
              <div className="flex items-center gap-2 text-gray-400">
                <Icon name="calendar" size={14} />
                <span>{new Date(selectedTask.scheduledDate + "T00:00:00").toLocaleDateString("en-US", { timeZone: "Africa/Cairo" })}</span>
                {selectedTask.scheduledTime && <span>at {selectedTask.scheduledTime}</span>}
              </div>
              {selectedTask.notes && (
                <p className="text-gray-500 text-xs">{selectedTask.notes}</p>
              )}
            </div>
            {/* Action buttons */}
            <div className="flex items-center gap-2 pt-4 border-t border-[rgba(255,255,255,0.06)]">
              {selectedTask.status !== "completed" && (
                <button
                  onClick={() => handleUpdateTask(selectedTask.id, { status: "completed" })}
                  className="flex-1 px-3 py-2 rounded-lg text-xs font-medium bg-green-500/10 border border-green-500/30 text-green-400 hover:bg-green-500/20 transition-all"
                >
                  <Icon name="check" size={12} className="inline mr-1" />
                  Complete
                </button>
              )}
              <button
                onClick={() => setEditingTask(selectedTask)}
                className="flex-1 px-3 py-2 rounded-lg text-xs font-medium bg-white/5 border border-[rgba(255,255,255,0.08)] text-gray-400 hover:text-white hover:bg-white/10 transition-all"
              >
                <Icon name="edit" size={12} className="inline mr-1" />
                Edit
              </button>
              <button
                onClick={() => {
                  if (confirm("Delete this scheduled task?")) {
                    handleDeleteTask(selectedTask.id);
                  }
                }}
                className="px-3 py-2 rounded-lg text-xs font-medium bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 transition-all"
              >
                <Icon name="delete" size={12} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Task Modal */}
      {editingTask && (
        <TaskFormModal
          title="Edit Task"
          initial={{
            title: editingTask.title,
            scheduledDate: editingTask.scheduledDate,
            scheduledTime: editingTask.scheduledTime || "",
            type: editingTask.type,
            notes: editingTask.notes || "",
            status: editingTask.status,
          }}
          showStatus
          onSubmit={(data) => handleUpdateTask(editingTask.id, data)}
          onClose={() => { setEditingTask(null); setSelectedTask(null); }}
        />
      )}

      {/* Create Task Modal */}
      {showCreateForm && (
        <TaskFormModal
          title="New Scheduled Task"
          initial={{
            title: "",
            scheduledDate: createDate,
            scheduledTime: "",
            type: "task",
            notes: "",
          }}
          onSubmit={handleCreateTask}
          onClose={() => { setShowCreateForm(false); setCreateDate(""); }}
        />
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
        <span className="text-[10px] text-gray-600">Double-click a cell to add task</span>
        <span className="text-xs text-gray-600">{loading ? "Updating..." : "Live"}</span>
      </div>
    </div>
  );
}

// Reusable form modal for create and edit
function TaskFormModal({
  title,
  initial,
  showStatus,
  onSubmit,
  onClose,
}: {
  title: string;
  initial: {
    title: string;
    scheduledDate: string;
    scheduledTime: string;
    type: string;
    notes: string;
    status?: string;
  };
  showStatus?: boolean;
  onSubmit: (data: any) => void;
  onClose: () => void;
}) {
  const [form, setForm] = useState(initial);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim() || !form.scheduledDate) return;
    onSubmit({
      title: form.title.trim(),
      scheduledDate: form.scheduledDate,
      scheduledTime: form.scheduledTime || undefined,
      type: form.type,
      notes: form.notes || undefined,
      ...(showStatus && form.status ? { status: form.status } : {}),
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-[#12121a] border border-[rgba(255,255,255,0.1)] rounded-xl w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-white">{title}</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-white">
            <Icon name="close" size={18} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs text-gray-500 block mb-1">Title</label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full px-3 py-2 rounded-lg bg-white/5 border border-[rgba(255,255,255,0.08)] text-white text-sm focus:outline-none focus:border-indigo-500/50"
              placeholder="Task title..."
              autoFocus
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Date</label>
              <input
                type="date"
                value={form.scheduledDate}
                onChange={(e) => setForm({ ...form, scheduledDate: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-[rgba(255,255,255,0.08)] text-white text-sm focus:outline-none focus:border-indigo-500/50 [color-scheme:dark]"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Time (optional)</label>
              <input
                type="time"
                value={form.scheduledTime}
                onChange={(e) => setForm({ ...form, scheduledTime: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-[rgba(255,255,255,0.08)] text-white text-sm focus:outline-none focus:border-indigo-500/50 [color-scheme:dark]"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Type</label>
              <select
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-[rgba(255,255,255,0.08)] text-white text-sm focus:outline-none focus:border-indigo-500/50 [color-scheme:dark]"
              >
                <option value="task">Task</option>
                <option value="content">Content</option>
                <option value="cron">Cron</option>
              </select>
            </div>
            {showStatus && (
              <div>
                <label className="text-xs text-gray-500 block mb-1">Status</label>
                <select
                  value={form.status || "scheduled"}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-white/5 border border-[rgba(255,255,255,0.08)] text-white text-sm focus:outline-none focus:border-indigo-500/50 [color-scheme:dark]"
                >
                  <option value="scheduled">Scheduled</option>
                  <option value="completed">Completed</option>
                  <option value="missed">Missed</option>
                </select>
              </div>
            )}
          </div>
          <div>
            <label className="text-xs text-gray-500 block mb-1">Notes (optional)</label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              className="w-full px-3 py-2 rounded-lg bg-white/5 border border-[rgba(255,255,255,0.08)] text-white text-sm focus:outline-none focus:border-indigo-500/50 resize-none"
              rows={3}
              placeholder="Additional notes..."
            />
          </div>
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 px-3 py-2 rounded-lg text-xs font-medium border border-[rgba(255,255,255,0.08)] text-gray-400 hover:text-white hover:bg-white/5 transition-all">
              Cancel
            </button>
            <button type="submit" className="flex-1 px-3 py-2 rounded-lg text-xs font-medium bg-[rgba(124,92,252,0.15)] border border-indigo-500/30 text-indigo-400 hover:bg-[rgba(124,92,252,0.25)] transition-all">
              {showStatus ? "Save Changes" : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
