"use client";

import { useEffect, useState } from "react";
import { Panel } from "@/components/ui";
import { DocsEntry, MemoryEntry, OfficeMetric, ProjectEntry, TeamEntry } from "@/lib/types";

type ModuleName = "docs" | "memory" | "team" | "office" | "projects";

function useModuleData<T>(module: ModuleName) {
  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(`/api/modules?module=${module}`, { cache: "no-store" });
        if (!response.ok) throw new Error(`Failed to load ${module}`);
        const payload = (await response.json()) as { data: T[] };
        if (!cancelled) setData(payload.data || []);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unknown error");
          setData([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [module]);

  return { data, loading, error };
}

export function DocsPanel() {
  const { data, loading, error } = useModuleData<DocsEntry>("docs");

  return (
    <Panel title="Knowledge docs">
      {loading && <p className="text-sm text-[#4B6A9B]">Loading workspace docs...</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}
      {!loading && !error && data.length === 0 && <p className="text-sm text-[#2D4163]">No docs found.</p>}
      {!loading && !error && (
        <ul className="space-y-2 text-sm">
          {data.map((item) => (
            <li key={item.id} className="glass-light rounded-[8px] p-2.5 transition-smooth hover:bg-[rgba(79,142,247,0.05)]">
              <p className="text-[#e2e8f0] text-xs font-medium">{item.title}</p>
              <p className="ts mt-0.5">
                {item.category} - {new Date(item.updatedAt).toLocaleString("en-US", { timeZone: "Africa/Cairo" })}
              </p>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

export function MemoryPanels() {
  const { data, loading, error } = useModuleData<MemoryEntry>("memory");
  const decisions = data.filter((item) => item.type === "decision");
  const threads = data.filter((item) => item.type === "thread");

  return (
    <div className="space-y-4">
      {/* Decisions */}
      <div className="glass rounded-[10px] p-4">
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">Strategic decisions</h3>
        {loading && <p className="text-sm text-[#4B6A9B]">Loading memory...</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}
        {!loading && !error && decisions.length === 0 && <p className="text-sm text-[#2D4163]">No decisions found.</p>}
        {!loading && !error && (
          <div className="grid gap-2 md:grid-cols-2">
            {decisions.map((item) => (
              <div key={item.id} className="glass-light rounded-[8px] p-3 card-glow transition-smooth hover:bg-[rgba(79,142,247,0.05)]">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <p className="text-[#a8c4e8] text-xs leading-snug flex-1">{item.text}</p>
                  {item.updatedAt && (
                    <span className="ts shrink-0 bg-[#1E2D45] px-1.5 py-0.5 rounded text-[10px] text-[#4B6A9B]">
                      {new Date(item.updatedAt).toLocaleDateString("en-US", { timeZone: "Africa/Cairo", month: "short", day: "numeric" })}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Open threads and lessons */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="glass rounded-[10px] p-4">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">Open threads</h3>
          {!loading && !error && threads.length === 0 && <p className="text-sm text-[#2D4163]">No open threads.</p>}
          {!loading && !error && (
            <ul className="space-y-2">
              {threads.map((item) => (
                <li key={item.id} className="glass-light rounded-[8px] p-2.5 flex items-start gap-2 transition-smooth">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0 animate-pulse" />
                  <p className="text-xs text-[#a8c4e8] leading-snug">{item.text}</p>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="glass rounded-[10px] p-4">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">Lessons learned</h3>
          {!loading && !error && threads.length === 0 && (
            <p className="text-sm text-[#2D4163]">No lessons recorded.</p>
          )}
          {!loading && !error && (
            <ul className="space-y-2">
              {threads.map((item) => (
                <li key={`lesson-${item.id}`} className="glass-light rounded-[8px] p-2.5 flex items-start gap-2 transition-smooth border-l-2 border-[#2D4163]">
                  <p className="text-xs leading-snug text-[#6B8AAE]">{item.text}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

export function TeamPanel() {
  const { data, loading, error } = useModuleData<TeamEntry>("team");

  function statusDot(status: string) {
    if (status === "active") return "bg-emerald-400 animate-pulse";
    if (status === "busy") return "bg-amber-400";
    return "bg-[#2D4163]";
  }

  function statusClass(status: string) {
    if (status === "active") return "text-emerald-300";
    if (status === "busy") return "text-amber-300";
    return "text-[#4B6A9B]";
  }

  return (
    <Panel title="Active team matrix">
      {loading && <p className="text-sm text-[#4B6A9B]">Loading team...</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}
      {!loading && !error && data.length === 0 && <p className="text-sm text-[#2D4163]">No agents found.</p>}
      {!loading && !error && (
        <ul className="space-y-2">
          {data.map((item) => (
            <li key={item.id} className="glass-light rounded-[8px] p-2.5 flex items-center justify-between transition-smooth hover:bg-[rgba(79,142,247,0.05)]">
              <div className="flex items-center gap-2.5">
                <span className={`h-2 w-2 rounded-full ${statusDot(item.status)}`} />
                <div>
                  <span className="text-xs font-medium text-[#e2e8f0]">{item.name}</span>
                  <span className="ml-2 text-xs text-[#4B6A9B]">{item.focus}</span>
                </div>
              </div>
              <span className={`text-[10px] font-semibold uppercase tracking-wide ${statusClass(item.status)}`}>{item.status}</span>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

export function OfficePanel() {
  const { data, loading, error } = useModuleData<OfficeMetric>("office");

  function trendArrow(trend: string) {
    if (trend === "up") return "up";
    if (trend === "down") return "dn";
    return "--";
  }

  function trendClass(trend: string) {
    if (trend === "up") return "text-red-400";
    if (trend === "down") return "text-emerald-400";
    return "text-[#4B6A9B]";
  }

  return (
    <Panel title="System metrics">
      {loading && <p className="text-sm text-[#4B6A9B]">Loading system metrics...</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}
      {!loading && !error && data.length === 0 && <p className="text-sm text-[#2D4163]">No metrics available.</p>}
      {!loading && !error && (
        <ul className="space-y-2">
          {data.map((item) => (
            <li key={item.id} className="glass-light rounded-[8px] p-2.5 flex items-center justify-between transition-smooth">
              <span className="text-xs text-[#6B8AAE]">{item.label}</span>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-[#e2e8f0]">{item.value}</span>
                <span className={`text-[10px] font-mono ${trendClass(item.trend)}`}>{trendArrow(item.trend)}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

export function ProjectsPanels() {
  const { data, loading, error } = useModuleData<ProjectEntry>("projects");

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="glass rounded-[10px] p-4">
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">Goal objectives</h3>
        {loading && <p className="text-sm text-[#4B6A9B]">Loading goals...</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}
        {!loading && !error && data.length === 0 && <p className="text-sm text-[#2D4163]">No objectives found.</p>}
        {!loading && !error && (
          <ul className="space-y-4">
            {data.map((project) => (
              <li key={project.id}>
                <div className="mb-1.5 flex items-center justify-between">
                  <p className="text-xs text-[#a8c4e8]">{project.name}</p>
                  <span className="text-[10px] text-[#4B6A9B]">{project.progress}%</span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-[#1E2D45]">
                  <div className="h-1.5 rounded-full gradient-accent" style={{ width: `${Math.min(100, project.progress)}%` }} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="glass rounded-[10px] p-4">
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">Key results</h3>
        {!loading && !error && (
          <ul className="space-y-2">
            {data.flatMap((project) =>
              project.linkedTasks.map((task) => (
                <li key={`${project.id}-${task}`} className="glass-light rounded-[8px] p-2.5 transition-smooth hover:bg-[rgba(79,142,247,0.05)]">
                  <p className="text-[10px] text-[#2D4163]">{project.name}</p>
                  <p className="text-xs text-[#a8c4e8] mt-0.5">{task}</p>
                </li>
              ))
            )}
            {data.every((p) => p.linkedTasks.length === 0) && (
              <li className="text-sm text-[#2D4163]">No key results found.</li>
            )}
          </ul>
        )}
      </div>
    </div>
  );
}
