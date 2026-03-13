"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { defaultEvents } from "@/lib/data";
import { CalendarCategory, CalendarEvent } from "@/lib/types";
import { categorySourceMap, createCalendarEvent, sortEvents } from "@/lib/calendar-helpers";

type ViewMode = "month" | "week" | "day";

const categoryMeta: Record<CalendarCategory, { color: string; label: string; source: string }> = {
  task: { color: "bg-blue-500", label: "Task", source: "Tasks" },
  content: { color: "bg-violet-500", label: "Content", source: "Content" },
  meeting: { color: "bg-emerald-500", label: "Meeting", source: "Meetings" },
  automation: { color: "bg-amber-500", label: "Automation", source: "Automations" },
};

function normalize(date: Date) {
  return date.toISOString().split("T")[0];
}

export function CalendarBoard() {
  const [view, setView] = useState<ViewMode>("month");
  const [events, setEvents] = useState<CalendarEvent[]>(defaultEvents);
  const [selectedDate, setSelectedDate] = useState(normalize(new Date("2026-03-04")));
  const [activeEvent, setActiveEvent] = useState<CalendarEvent | null>(null);

  useEffect(() => {
    async function loadEvents() {
      try {
        const response = await fetch("/api/calendar/events", { cache: "no-store" });
        if (!response.ok) return;
        const payload = (await response.json()) as { events: CalendarEvent[] };
        setEvents(sortEvents(payload.events));
      } catch {
        setEvents(defaultEvents);
      }
    }

    loadEvents();
  }, []);

  const monthDays = useMemo(() => {
    const year = 2026;
    const month = 2;
    const days = new Date(year, month + 1, 0).getDate();
    return Array.from({ length: days }, (_, i) => `${year}-03-${String(i + 1).padStart(2, "0")}`);
  }, []);

  const visibleEvents = useMemo(() => {
    if (view === "day") {
      return events.filter((event) => event.date === selectedDate);
    }

    if (view === "week") {
      const start = new Date(selectedDate);
      const end = new Date(selectedDate);
      end.setDate(end.getDate() + 6);
      return events.filter((event) => {
        const date = new Date(event.date);
        return date >= start && date <= end;
      });
    }

    return events;
  }, [events, selectedDate, view]);

  async function addEvent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const title = String(form.get("title") || "").trim();
    const date = String(form.get("date") || "");
    const time = String(form.get("time") || "09:00");
    const details = String(form.get("details") || "").trim();
    const category = String(form.get("category") || "task") as CalendarCategory;

    if (!title || !date || !details) return;

    const optimistic = createCalendarEvent({
      id: crypto.randomUUID(),
      title,
      date,
      time,
      details,
      category,
    });

    setEvents((current) => sortEvents([...current, optimistic]));
    setSelectedDate(date);
    event.currentTarget.reset();

    try {
      const response = await fetch("/api/calendar/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, date, time, details, category }),
      });

      if (!response.ok) {
        setEvents((current) => current.filter((item) => item.id !== optimistic.id));
        return;
      }

      const payload = (await response.json()) as { events: CalendarEvent[] };
      setEvents(sortEvents(payload.events));
    } catch {
      setEvents((current) => current.filter((item) => item.id !== optimistic.id));
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-2">
        {(["month", "week", "day"] as ViewMode[]).map((mode) => (
          <button
            key={mode}
            onClick={() => setView(mode)}
            className={`rounded-md border px-3 py-1.5 text-sm capitalize ${
              view === mode ? "border-zinc-500 bg-zinc-900 text-zinc-100" : "border-zinc-800 text-zinc-400"
            }`}
          >
            {mode}
          </button>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[2fr_1fr]">
        <section className="rounded-lg border border-zinc-800 bg-[#111111] p-4">
          <h3 className="mb-3 text-sm uppercase tracking-wide text-zinc-500">Calendar grid</h3>
          {view === "month" ? (
            <div className="grid grid-cols-7 gap-2">
              {monthDays.map((day) => {
                const dayEvents = events.filter((event) => event.date === day);
                return (
                  <button
                    key={day}
                    onClick={() => setSelectedDate(day)}
                    className={`min-h-24 rounded-md border p-2 text-left ${
                      selectedDate === day ? "border-zinc-500" : "border-zinc-800"
                    }`}
                  >
                    <p className="text-xs text-zinc-400">{day.slice(-2)}</p>
                    <div className="mt-1 space-y-1">
                      {dayEvents.slice(0, 3).map((item) => (
                        <div
                          key={item.id}
                          className="truncate rounded px-1 py-0.5 text-[10px] text-black"
                          style={{
                            backgroundColor:
                              item.category === "task"
                                ? "#60a5fa"
                                : item.category === "content"
                                  ? "#a78bfa"
                                  : item.category === "meeting"
                                    ? "#34d399"
                                    : "#fbbf24",
                          }}
                        >
                          {item.title}
                        </div>
                      ))}
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <ul className="space-y-2">
              {visibleEvents.map((item) => (
                <li
                  key={item.id}
                  className="flex items-center justify-between rounded-md border border-zinc-800 p-2 text-sm"
                >
                  <button className="text-left" onClick={() => setActiveEvent(item)}>
                    <p className="text-zinc-100">{item.title}</p>
                    <p className="text-xs text-zinc-400">{item.date} at {item.time}</p>
                  </button>
                  <span className={`h-2.5 w-2.5 rounded-full ${categoryMeta[item.category].color}`} />
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-lg border border-zinc-800 bg-[#111111] p-4">
          <h3 className="mb-3 text-sm uppercase tracking-wide text-zinc-500">Create event</h3>
          <form className="space-y-3" onSubmit={addEvent}>
            <input name="title" placeholder="Event title" required className="w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm" />
            <div className="grid grid-cols-2 gap-2">
              <input name="date" type="date" required className="rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm" />
              <input name="time" type="time" defaultValue="09:00" className="rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm" />
            </div>
            <select name="category" className="w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm">
              <option value="task">Tasks</option>
              <option value="content">Content</option>
              <option value="meeting">Meetings</option>
              <option value="automation">Automations</option>
            </select>
            <textarea name="details" required rows={3} placeholder="Event details" className="w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm" />
            <button type="submit" className="w-full rounded border border-zinc-600 bg-zinc-900 px-3 py-2 text-sm">
              Add event
            </button>
          </form>
          <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-zinc-400">
            {Object.entries(categoryMeta).map(([key, meta]) => (
              <div key={key} className="flex items-center gap-2 rounded border border-zinc-800 p-2">
                <span className={`h-2.5 w-2.5 rounded-full ${meta.color}`} />
                {meta.label}
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="rounded-lg border border-zinc-800 bg-[#111111] p-4">
        <h3 className="mb-3 text-sm uppercase tracking-wide text-zinc-500">Events list</h3>
        <ul className="space-y-2">
          {visibleEvents.map((item) => (
            <li key={item.id} className="rounded-md border border-zinc-800 p-2 text-sm">
              <button className="w-full text-left" onClick={() => setActiveEvent(item)}>
                <p className="font-medium text-zinc-100">{item.title}</p>
                <p className="text-zinc-400">{categorySourceMap[item.category]}, {item.date}, {item.time}</p>
              </button>
            </li>
          ))}
        </ul>
      </section>

      {activeEvent && (
        <div className="fixed inset-0 z-30 flex items-center justify-center bg-black/70 px-4">
          <div className="w-full max-w-lg rounded-lg border border-zinc-700 bg-[#121212] p-5">
            <div className="mb-3 flex items-center justify-between">
              <h4 className="text-lg font-semibold text-zinc-100">{activeEvent.title}</h4>
              <button onClick={() => setActiveEvent(null)} className="text-sm text-zinc-400">Close</button>
            </div>
            <p className="text-sm text-zinc-400">{activeEvent.date} at {activeEvent.time}</p>
            <p className="mt-3 text-sm text-zinc-300">{activeEvent.details}</p>
            <div className="mt-4 inline-flex items-center gap-2 rounded border border-zinc-700 px-2 py-1 text-xs text-zinc-300">
              <span className={`h-2.5 w-2.5 rounded-full ${categoryMeta[activeEvent.category].color}`} />
              {categoryMeta[activeEvent.category].label}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
