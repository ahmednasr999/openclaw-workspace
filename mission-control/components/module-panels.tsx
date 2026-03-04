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
        if (!response.ok) {
          throw new Error(`Failed to load ${module}`);
        }

        const payload = (await response.json()) as { data: T[] };
        if (!cancelled) {
          setData(payload.data || []);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unknown error");
          setData([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [module]);

  return { data, loading, error };
}

export function DocsPanel() {
  const { data, loading, error } = useModuleData<DocsEntry>("docs");

  return (
    <Panel title="Knowledge docs">
      {loading && <p className="text-sm text-zinc-400">Loading docs...</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}
      {!loading && !error && (
        <ul className="space-y-2 text-sm text-zinc-300">
          {data.map((item) => (
            <li key={item.id} className="rounded border border-zinc-800 p-2">
              <p className="text-zinc-100">{item.title}</p>
              <p className="text-xs text-zinc-500">{item.category}, {new Date(item.updatedAt).toLocaleString()}</p>
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
    <div className="grid gap-4 md:grid-cols-2">
      <Panel title="Last decisions">
        {loading && <p className="text-sm text-zinc-400">Loading memory...</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}
        {!loading && !error && (
          <ul className="space-y-2 text-sm text-zinc-300">
            {decisions.map((item) => <li key={item.id}>{item.text}</li>)}
          </ul>
        )}
      </Panel>
      <Panel title="Open threads">
        {!loading && !error && (
          <ul className="space-y-2 text-sm text-zinc-300">
            {threads.map((item) => <li key={item.id}>{item.text}</li>)}
          </ul>
        )}
      </Panel>
    </div>
  );
}

export function TeamPanel() {
  const { data, loading, error } = useModuleData<TeamEntry>("team");

  return (
    <Panel title="Active team matrix">
      {loading && <p className="text-sm text-zinc-400">Loading team...</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}
      {!loading && !error && (
        <ul className="space-y-2 text-sm">
          {data.map((item) => (
            <li key={item.id} className="flex items-center justify-between rounded border border-zinc-800 p-2">
              <span>{item.name}: {item.focus}</span>
              <span className={`text-xs ${item.status === "active" ? "text-emerald-300" : item.status === "busy" ? "text-amber-300" : "text-zinc-400"}`}>{item.status}</span>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

export function OfficePanel() {
  const { data, loading, error } = useModuleData<OfficeMetric>("office");

  return (
    <Panel title="Office activity">
      {loading && <p className="text-sm text-zinc-400">Loading office metrics...</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}
      {!loading && !error && (
        <ul className="space-y-2 text-sm text-zinc-300">
          {data.map((item) => (
            <li key={item.id} className="flex items-center justify-between rounded border border-zinc-800 p-2">
              <span>{item.label}</span>
              <span>{item.value}</span>
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
      <Panel title="Portfolio status">
        {loading && <p className="text-sm text-zinc-400">Loading projects...</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}
        {!loading && !error && (
          <ul className="space-y-2 text-sm">
            {data.map((project) => (
              <li key={project.id}>{project.name}: {project.progress}%</li>
            ))}
          </ul>
        )}
      </Panel>
      <Panel title="Linked tasks">
        {!loading && !error && (
          <ul className="space-y-2 text-sm">
            {data.flatMap((project) => project.linkedTasks).map((task) => (
              <li key={task}>{task}</li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  );
}
