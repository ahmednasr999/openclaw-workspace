import { describe, expect, it } from "vitest";
import { createCalendarEvent, sortEvents } from "../lib/calendar-helpers";

describe("calendar helpers", () => {
  it("maps category to source when creating events", () => {
    const event = createCalendarEvent({
      id: "1",
      title: "Test",
      date: "2026-03-05",
      time: "10:00",
      details: "Details",
      category: "meeting",
    });

    expect(event.source).toBe("Meetings");
  });

  it("sorts events by date and time", () => {
    const sorted = sortEvents([
      createCalendarEvent({
        id: "2",
        title: "Late",
        date: "2026-03-05",
        time: "12:00",
        details: "B",
        category: "task",
      }),
      createCalendarEvent({
        id: "1",
        title: "Early",
        date: "2026-03-04",
        time: "09:00",
        details: "A",
        category: "task",
      }),
    ]);

    expect(sorted.map((item) => item.id)).toEqual(["1", "2"]);
  });
});
