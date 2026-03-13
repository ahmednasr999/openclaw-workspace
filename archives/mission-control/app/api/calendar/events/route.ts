import { NextResponse } from "next/server";
import { createCalendarEvent } from "@/lib/calendar-helpers";
import { loadCalendarEvents, saveCalendarEvent } from "@/lib/calendar-store";
import { CalendarCategory } from "@/lib/types";

export const runtime = "nodejs";

const allowedCategories: CalendarCategory[] = ["task", "content", "meeting", "automation"];

export async function GET() {
  const events = await loadCalendarEvents();
  return NextResponse.json({ events });
}

export async function POST(request: Request) {
  const body = (await request.json()) as {
    title?: string;
    date?: string;
    time?: string;
    details?: string;
    category?: CalendarCategory;
  };

  const title = body.title?.trim() || "";
  const date = body.date || "";
  const time = body.time || "09:00";
  const details = body.details?.trim() || "";
  const category = body.category;

  if (!title || !date || !details || !category || !allowedCategories.includes(category)) {
    return NextResponse.json({ error: "Invalid payload" }, { status: 400 });
  }

  const event = createCalendarEvent({
    id: crypto.randomUUID(),
    title,
    date,
    time,
    details,
    category,
  });

  const events = await saveCalendarEvent(event);
  return NextResponse.json({ event, events }, { status: 201 });
}
