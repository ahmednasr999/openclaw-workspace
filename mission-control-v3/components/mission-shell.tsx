"use client";

import { ReactNode, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/sidebar";
import { navItems } from "@/lib/data";
import { BackendHealth } from "@/lib/types";

const defaultHealth: BackendHealth = {
  reachable: true,
  latencyMs: 0,
  level: "healthy",
  reason: "Initializing",
  checkedAt: new Date().toISOString(),
};

export function MissionShell({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [backendHealth, setBackendHealth] = useState<BackendHealth>(defaultHealth);
  const router = useRouter();
  const searchInputRef = useRef<HTMLInputElement>(null);

  const filtered = useMemo(() => navItems.filter((n) => n.label.toLowerCase().includes(query.toLowerCase())), [query]);
  const isRedAlert = backendHealth.level === "critical" || !backendHealth.reachable;

  useEffect(() => {
    if (!commandOpen) {
      return;
    }

    const timeout = setTimeout(() => searchInputRef.current?.focus(), 0);
    return () => clearTimeout(timeout);
  }, [commandOpen]);

  useEffect(() => {
    async function pollBackendHealth() {
      try {
        const [healthResponse, heartbeatResponse] = await Promise.all([
          fetch("/api/system/status", { cache: "no-store" }),
          fetch("/api/system/heartbeat", { cache: "no-store" }),
        ]);
        const payload = (await healthResponse.json()) as BackendHealth;

        if (!healthResponse.ok) {
          setBackendHealth({ ...payload, reachable: false, level: "critical" });
          return;
        }

        if (heartbeatResponse.ok) {
          const heartbeatPayload = await heartbeatResponse.json() as { status: "healthy" | "degraded"; tick: number };
          if (heartbeatPayload.status === "degraded" && payload.level === "healthy") {
            setBackendHealth({ ...payload, level: "degraded", reason: `Heartbeat degraded at tick ${heartbeatPayload.tick}` });
            return;
          }
        }

        setBackendHealth(payload);
      } catch {
        setBackendHealth({
          reachable: false,
          latencyMs: 999,
          level: "critical",
          reason: "Health endpoint unavailable",
          checkedAt: new Date().toISOString(),
        });
      }
    }

    pollBackendHealth();
    const interval = setInterval(pollBackendHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function isEditableTarget(target: EventTarget | null) {
      if (!(target instanceof HTMLElement)) {
        return false;
      }
      const tag = target.tagName.toLowerCase();
      return target.isContentEditable || tag === "input" || tag === "textarea" || tag === "select";
    }

    function onKeyDown(event: KeyboardEvent) {
      const triggerPalette = (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k";

      if (triggerPalette && !isEditableTarget(event.target)) {
        event.preventDefault();
        setSelectedIndex(0);
        setCommandOpen(true);
        return;
      }

      if (event.key === "Escape" && commandOpen) {
        event.preventDefault();
        setCommandOpen(false);
        return;
      }

      if (!commandOpen) {
        return;
      }

      if (event.key === "ArrowDown") {
        event.preventDefault();
        setSelectedIndex((current) => (filtered.length === 0 ? 0 : (current + 1) % filtered.length));
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        setSelectedIndex((current) => (filtered.length === 0 ? 0 : (current - 1 + filtered.length) % filtered.length));
      } else if (event.key === "Enter") {
        event.preventDefault();
        const selected = filtered[selectedIndex];
        if (selected) {
          router.push(selected.href);
          setCommandOpen(false);
          setQuery("");
        }
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [commandOpen, filtered, router, selectedIndex]);

  return (
    <div className={`min-h-screen bg-[#0a0a0a] text-zinc-100 md:flex ${isRedAlert ? "red-alert" : ""}`}>
      <Sidebar collapsed={leftCollapsed} />
      <main className="flex-1 p-4 md:p-8">
        <header className="mb-6 border-b border-zinc-800 pb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
            <p className="mt-1 text-sm text-zinc-400">{description}</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setLeftCollapsed((v) => !v)} className="rounded border border-zinc-700 px-2 py-1 text-xs">☰</button>
            <button onClick={() => { setSelectedIndex(0); setCommandOpen(true); }} className="rounded border border-zinc-700 px-2 py-1 text-xs">Command</button>
            <span className="inline-flex items-center gap-1 text-xs text-zinc-400">
              <span className={`h-2 w-2 rounded-full ${backendHealth.level === "healthy" ? "bg-emerald-400" : backendHealth.level === "degraded" ? "bg-amber-400" : "bg-red-500"} ${backendHealth.level === "healthy" ? "animate-pulse" : ""}`} />
              {backendHealth.level} · {backendHealth.latencyMs} ms
            </span>
          </div>
        </header>
        {children}
      </main>

      {commandOpen && (
        <div className="fixed inset-0 z-40 bg-black/60 p-4" onClick={() => setCommandOpen(false)}>
          <div className="mx-auto mt-20 max-w-xl rounded border border-zinc-700 bg-[#111111] p-4" onClick={(e) => e.stopPropagation()}>
            <div className="mb-2 flex items-center justify-between"><strong>Command Palette</strong><button className="text-xs" onClick={() => setCommandOpen(false)}>Close</button></div>
            <input
              ref={searchInputRef}
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setSelectedIndex(0);
              }}
              placeholder="Type route"
              className="mb-3 w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-2"
            />
            <div className="space-y-2">
              {filtered.map((item, index) => (
                <button
                  key={item.href}
                  className={`block w-full rounded border px-3 py-2 text-left ${index === selectedIndex ? "border-zinc-500 bg-zinc-900" : "border-zinc-800 hover:bg-zinc-900"}`}
                  onMouseEnter={() => setSelectedIndex(index)}
                  onClick={() => {
                    router.push(item.href);
                    setCommandOpen(false);
                    setQuery("");
                  }}
                >
                  {item.label}
                </button>
              ))}
            </div>
            <p className="mt-3 text-xs text-zinc-500">Global shortcut: Ctrl+K on Windows/Linux, Cmd+K on macOS. Esc closes palette.</p>
          </div>
        </div>
      )}
    </div>
  );
}
