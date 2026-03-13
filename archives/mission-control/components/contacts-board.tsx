"use client";

import { useMemo, useState } from "react";
import { contacts } from "@/lib/data";

const filters = ["All", "Executive", "Hiring", "Partner", "Team"] as const;

export function ContactsBoard() {
  const [filter, setFilter] = useState<(typeof filters)[number]>("All");

  const filtered = useMemo(() => {
    if (filter === "All") return contacts;
    return contacts.filter((c) => c.category === filter);
  }, [filter]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {filters.map((item) => (
          <button
            key={item}
            onClick={() => setFilter(item)}
            className={`rounded-md border px-3 py-1.5 text-xs ${
              filter === item
                ? "border-zinc-500 bg-zinc-900 text-zinc-100"
                : "border-zinc-800 text-zinc-400 hover:bg-zinc-900"
            }`}
          >
            {item}
          </button>
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {filtered.map((contact) => (
          <article key={contact.id} className="rounded-lg border border-zinc-800 bg-[#111111] p-4">
            <p className="text-sm uppercase tracking-wide text-zinc-500">{contact.category}</p>
            <h3 className="mt-1 text-lg font-semibold text-zinc-100">{contact.name}</h3>
            <p className="text-sm text-zinc-300">{contact.role}, {contact.company}</p>
            <p className="mt-2 text-sm text-zinc-400">{contact.email}</p>
            <p className="mt-3 text-sm text-zinc-300">{contact.notes}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
