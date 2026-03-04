import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { defaultEvents } from "@/lib/data";
import { sortEvents } from "@/lib/calendar-helpers";
import { CalendarEvent } from "@/lib/types";

const dataDir = path.join(process.cwd(), "data");
const filePath = path.join(dataDir, "calendar-events.json");

async function ensureStoreFile() {
  await mkdir(dataDir, { recursive: true });

  try {
    await readFile(filePath, "utf8");
  } catch {
    await writeFile(filePath, JSON.stringify(defaultEvents, null, 2), "utf8");
  }
}

export async function loadCalendarEvents() {
  await ensureStoreFile();
  const raw = await readFile(filePath, "utf8");
  const parsed = JSON.parse(raw) as CalendarEvent[];
  return sortEvents(parsed);
}

export async function saveCalendarEvent(event: CalendarEvent) {
  const events = await loadCalendarEvents();
  const next = sortEvents([...events, event]);
  await writeFile(filePath, JSON.stringify(next, null, 2), "utf8");
  return next;
}
