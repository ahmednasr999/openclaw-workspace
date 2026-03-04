"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { navGroups } from "@/lib/data";

interface CommandResult {
  id: string;
  title: string;
  subtitle?: string;
  section: string;
  href?: string;
  shortcut?: string;
}

interface ResultGroup {
  label: string;
  items: CommandResult[];
}

const SECTION_ORDER = ["Tasks", "Pipeline", "Memory", "Pages"];

function buildNavResults(): CommandResult[] {
  const out: CommandResult[] = [];
  navGroups.forEach((group) => {
    group.items.forEach((item) => {
      out.push({
        id: `nav-${item.href}`,
        title: item.label,
        subtitle: group.label,
        section: "Pages",
        href: item.href,
        shortcut: item.short,
      });
    });
  });
  return out;
}

async function fetchCommandData(): Promise<CommandResult[]> {
  const [tasksRes, pipelineRes, memoryRes] = await Promise.all([
    fetch("/api/modules?module=tasks", { cache: "no-store" }).catch(() => null),
    fetch("/api/job-radar", { cache: "no-store" }).catch(() => null),
    fetch("/api/modules?module=memory", { cache: "no-store" }).catch(() => null),
  ]);

  const out: CommandResult[] = [];

  if (tasksRes?.ok) {
    try {
      const raw: unknown = await tasksRes.json();
      const list: unknown[] = Array.isArray(raw)
        ? raw
        : raw !== null && typeof raw === "object" && "tasks" in raw
        ? (raw as { tasks: unknown[] }).tasks
        : [];
      list.slice(0, 8).forEach((t, i) => {
        const o = t as Record<string, unknown>;
        out.push({
          id: `task-${i}`,
          title: String(o.title ?? o.name ?? "Untitled"),
          subtitle: String(o.status ?? "No status"),
          section: "Tasks",
        });
      });
    } catch { /* ignore */ }
  }

  if (pipelineRes?.ok) {
    try {
      const raw: unknown = await pipelineRes.json();
      const list: unknown[] = Array.isArray(raw)
        ? raw
        : raw !== null && typeof raw === "object" && "leads" in raw
        ? (raw as { leads: unknown[] }).leads
        : [];
      list.slice(0, 8).forEach((l, i) => {
        const o = l as Record<string, unknown>;
        out.push({
          id: `pipeline-${i}`,
          title: String(o.role ?? "Unknown Role"),
          subtitle: String(o.company ?? "Unknown Company"),
          section: "Pipeline",
        });
      });
    } catch { /* ignore */ }
  }

  if (memoryRes?.ok) {
    try {
      const raw: unknown = await memoryRes.json();
      const list: unknown[] = Array.isArray(raw)
        ? raw
        : raw !== null && typeof raw === "object" && "entries" in raw
        ? (raw as { entries: unknown[] }).entries
        : [];
      list.slice(0, 8).forEach((e, i) => {
        const o = e as Record<string, unknown>;
        out.push({
          id: `memory-${i}`,
          title: String(o.title ?? o.name ?? "Memory Entry"),
          subtitle: String(o.category ?? "Note"),
          section: "Memory",
        });
      });
    } catch { /* ignore */ }
  }

  return [...out, ...buildNavResults()];
}

function groupResults(all: CommandResult[], query: string): ResultGroup[] {
  const q = query.toLowerCase().trim();
  const filtered = q
    ? all.filter(
        (r) =>
          r.title.toLowerCase().includes(q) ||
          r.subtitle?.toLowerCase().includes(q)
      )
    : all;

  const map: Record<string, CommandResult[]> = {};
  filtered.forEach((r) => {
    if (!map[r.section]) map[r.section] = [];
    map[r.section].push(r);
  });

  return Object.entries(map)
    .map(([label, items]) => ({ label, items }))
    .sort(
      (a, b) =>
        (SECTION_ORDER.indexOf(a.label) === -1 ? 999 : SECTION_ORDER.indexOf(a.label)) -
        (SECTION_ORDER.indexOf(b.label) === -1 ? 999 : SECTION_ORDER.indexOf(b.label))
    );
}

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [groups, setGroups] = useState<ResultGroup[]>([]);
  const [loading, setLoading] = useState(false);

  const allDataRef = useRef<CommandResult[]>([]);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const router = useRouter();

  const openPalette = useCallback(async () => {
    setOpen(true);
    setQuery("");
    setSelectedIndex(0);
    if (allDataRef.current.length === 0) {
      setLoading(true);
      try {
        const data = await fetchCommandData();
        allDataRef.current = data;
        setGroups(groupResults(data, ""));
      } finally {
        setLoading(false);
      }
    } else {
      setGroups(groupResults(allDataRef.current, ""));
    }
  }, []);

  const closePalette = useCallback(() => {
    setOpen(false);
    setQuery("");
  }, []);

  // Listen for custom event from MissionShell button
  useEffect(() => {
    window.addEventListener("open-command-palette", openPalette);
    return () => window.removeEventListener("open-command-palette", openPalette);
  }, [openPalette]);

  // Focus input when opened
  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => inputRef.current?.focus(), 0);
    return () => clearTimeout(t);
  }, [open]);

  // Keyboard handling
  useEffect(() => {
    function isEditable(target: EventTarget | null) {
      if (!(target instanceof HTMLElement)) return false;
      const tag = target.tagName.toLowerCase();
      return (
        target.isContentEditable ||
        tag === "input" ||
        tag === "textarea" ||
        tag === "select"
      );
    }

    function onKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k" && !isEditable(e.target)) {
        e.preventDefault();
        openPalette();
        return;
      }

      if (e.key === "Escape" && open) {
        e.preventDefault();
        closePalette();
        return;
      }

      if (!open) return;

      const flat = groups.flatMap((g) => g.items);
      if (flat.length === 0) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((i) => (i + 1) % flat.length);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((i) => (i - 1 + flat.length) % flat.length);
      } else if (e.key === "Enter") {
        e.preventDefault();
        const item = flat[selectedIndex];
        if (item?.href) {
          router.push(item.href);
          closePalette();
        }
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, groups, selectedIndex, router, openPalette, closePalette]);

  function handleQueryChange(q: string) {
    setQuery(q);
    setSelectedIndex(0);
    setGroups(groupResults(allDataRef.current, q));
  }

  if (!open) return null;

  const flat = groups.flatMap((g) => g.items);

  return (
    <div
      className="fixed inset-0 z-50 command-overlay flex items-start justify-center pt-16 sm:pt-24 px-4"
      onClick={closePalette}
    >
      <div
        className="glass-dark rounded-[12px] w-full max-w-2xl shadow-2xl animate-slide-down overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[#1E2D45]">
          <svg
            className="h-4 w-4 text-[#4B6A9B] shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"
            />
          </svg>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => handleQueryChange(e.target.value)}
            placeholder="Search tasks, pipeline, memory, pages..."
            className="flex-1 bg-transparent text-sm text-[#e2e8f0] placeholder-[#4B6A9B] outline-none"
            autoComplete="off"
          />
          <kbd className="hidden sm:inline text-[10px] text-[#4B6A9B] border border-[#1E2D45] rounded px-1.5 py-0.5">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-[60vh] overflow-y-auto py-2">
          {loading && (
            <p className="px-4 py-8 text-center text-sm text-[#4B6A9B]">Loading...</p>
          )}
          {!loading && flat.length === 0 && (
            <p className="px-4 py-8 text-center text-sm text-[#4B6A9B]">
              {query === "" ? "No commands available." : "No results found."}
            </p>
          )}
          {!loading &&
            groups.map((group) => (
              <div key={group.label}>
                <p className="px-4 py-1.5 text-[10px] uppercase tracking-widest text-[#2D4163] font-semibold">
                  {group.label}
                </p>
                {group.items.map((item) => {
                  const idx = flat.findIndex((i) => i.id === item.id);
                  const selected = idx === selectedIndex;
                  return (
                    <button
                      key={item.id}
                      className={`w-full text-left px-4 py-2.5 text-sm flex items-center gap-3 transition-colors ${
                        selected
                          ? "bg-[rgba(79,142,247,0.12)] text-[#e2e8f0]"
                          : "text-[#6B8AAE] hover:bg-[rgba(79,142,247,0.06)] hover:text-[#a8c4e8]"
                      }`}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      onClick={() => {
                        if (item.href) {
                          router.push(item.href);
                          closePalette();
                        }
                      }}
                    >
                      {item.shortcut && (
                        <span className="text-xs font-mono text-[#2D4163] w-6">
                          {item.shortcut}
                        </span>
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="truncate">{item.title}</div>
                        {item.subtitle && (
                          <div className="text-xs text-[#4B6A9B] truncate">{item.subtitle}</div>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            ))}
        </div>

        {/* Footer */}
        {!loading && flat.length > 0 && (
          <div className="px-4 py-2 border-t border-[#1E2D45] flex items-center gap-4 text-[10px] text-[#2D4163]">
            <span>
              <kbd className="border border-[#1E2D45] rounded px-1">Ctrl K</kbd> open
            </span>
            <span>
              <kbd className="border border-[#1E2D45] rounded px-1">Esc</kbd> close
            </span>
            <span>
              <kbd className="border border-[#1E2D45] rounded px-1">Enter</kbd> navigate
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
