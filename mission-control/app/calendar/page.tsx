"use client";

import { Calendar } from "@/components/Calendar";

export default function CalendarPage() {
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[rgba(255,255,255,0.06)]">
        <h1 className="text-xl font-bold text-white">Calendar</h1>
        <p className="text-xs text-gray-500 mt-1">Scheduled tasks and proactive work</p>
      </div>
      
      {/* Calendar */}
      <div className="flex-1 overflow-hidden">
        <Calendar />
      </div>
    </div>
  );
}
