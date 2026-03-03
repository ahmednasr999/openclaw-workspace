import { CalendarCategory, CalendarEvent } from "@/lib/types";

export const categorySourceMap: Record<CalendarCategory, CalendarEvent["source"]> = {
  task: "Tasks",
  content: "Content",
  meeting: "Meetings",
  automation: "Automations",
};

export function sortEvents(events: CalendarEvent[]) {
  return [...events].sort((a, b) => `${a.date}${a.time}`.localeCompare(`${b.date}${b.time}`));
}

export function createCalendarEvent(input: {
  id: string;
  title: string;
  date: string;
  time: string;
  details: string;
  category: CalendarCategory;
}): CalendarEvent {
  return {
    ...input,
    source: categorySourceMap[input.category],
  };
}
