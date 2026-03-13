"use client";

import { ReactNode, useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { BackendHealth } from "@/lib/types";

const defaultHealth: BackendHealth = {
  reachable: true,
  latencyMs: 0,
  level: "healthy",
  reason: "Initializing",
  checkedAt: new Date().toISOString(),
};

interface SyncStatus {
  status: "synced" | "syncing" | "error";
  lastSyncAt?: string;
}

function SyncDot({ status, lastSyncAt }: { status: string; lastSyncAt?: string }) {
  const [showTip, setShowTip] = useState(false);
  const dotClass =
    status === "synced"
      ? "bg-emerald-400 animate-pulse"
      : status === "syncing"
      ? "bg-amber-400 animate-pulse"
      : "bg-red-500 animate-glow-red";
  const label = status === "synced" ? "Synced" : status === "syncing" ? "Syncing..." : "Sync error";
  const timeStr = lastSyncAt
    ? new Date(lastSyncAt).toLocaleTimeString("en-US", { timeZone: "Africa/Cairo", hour: "2-digit", minute: "2-digit" })
    : "";

  return (
    <div className="relative flex items-center gap-1.5" onMouseEnter={() => setShowTip(true)} onMouseLeave={() => setShowTip(false)}>
      <span className={`h-2 w-2 rounded-full ${dotClass}`} />
      <span className="text-xs text-[#4B6A9B] hidden sm:inline">{label}</span>
      {showTip && timeStr && (
        <div className="absolute right-0 top-5 z-50 glass rounded px-2 py-1 text-xs text-[#a8c4e8] whitespace-nowrap animate-fade-in">
          Last sync: {timeStr} (Cairo)
        </div>
      )}
    </div>
  );
}



export function MissionShell({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [backendHealth, setBackendHealth] = useState<BackendHealth>(defaultHealth);
  const [syncStatus, setSyncStatus] = useState<SyncStatus>({ status: "synced" });

  const isRedAlert = backendHealth.level === "critical" || !backendHealth.reachable;



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
          const hbDot = document.getElementById("sidebar-heartbeat");
          if (hbDot) { hbDot.className = "h-2 w-2 rounded-full bg-red-500 animate-glow-red"; }
          return;
        }

        if (heartbeatResponse.ok) {
          const heartbeatPayload = await heartbeatResponse.json() as { status: "healthy" | "degraded"; tick: number };
          if (heartbeatPayload.status === "degraded" && payload.level === "healthy") {
            setBackendHealth({ ...payload, level: "degraded", reason: `Heartbeat degraded at tick ${heartbeatPayload.tick}` });
            const hbDot = document.getElementById("sidebar-heartbeat");
            if (hbDot) { hbDot.className = "h-2 w-2 rounded-full bg-amber-400 animate-pulse"; }
            return;
          }
        }

        setBackendHealth(payload);
        const hbDot = document.getElementById("sidebar-heartbeat");
        const hbLabel = document.getElementById("sidebar-heartbeat-label");
        if (hbDot) {
          hbDot.className = payload.level === "healthy"
            ? "h-2 w-2 rounded-full bg-emerald-400 animate-pulse"
            : payload.level === "degraded"
            ? "h-2 w-2 rounded-full bg-amber-400 animate-pulse"
            : "h-2 w-2 rounded-full bg-red-500 animate-glow-red";
        }
        if (hbLabel) {
          hbLabel.textContent = payload.level === "healthy" ? "Gateway" : `Gateway: ${payload.level}`;
        }
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

    async function pollSyncStatus() {
      try {
        const res = await fetch("/api/sync-status", { cache: "no-store" });
        if (res.ok) {
          const data = await res.json() as { status?: string; lastSyncAt?: string };
          setSyncStatus({
            status: (data.status as SyncStatus["status"]) || "synced",
            lastSyncAt: data.lastSyncAt,
          });
        }
      } catch {
        setSyncStatus({ status: "error" });
      }
    }

    pollBackendHealth();
    pollSyncStatus();
    const healthInterval = setInterval(pollBackendHealth, 10000);
    const syncInterval = setInterval(pollSyncStatus, 30000);
    return () => {
      clearInterval(healthInterval);
      clearInterval(syncInterval);
    };
  }, []);



  const healthDotClass =
    backendHealth.level === "healthy"
      ? "bg-emerald-400 animate-pulse"
      : backendHealth.level === "degraded"
      ? "bg-amber-400 animate-pulse"
      : "bg-red-500 animate-glow-red";

  return (
    <div className={`min-h-screen bg-[#080C16] text-[#e2e8f0] md:flex ${isRedAlert ? "red-alert" : ""}`}>
      <Sidebar collapsed={leftCollapsed} />

      <main className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="sticky top-0 z-30 glass border-b border-[#1E2D45] px-4 md:px-6 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => setLeftCollapsed((v) => !v)}
              className="shrink-0 rounded-[6px] border border-[#1E2D45] p-1.5 text-[#4B6A9B] hover:text-[#a8c4e8] hover:border-[#2D4163] transition-colors"
              aria-label="Toggle sidebar"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="min-w-0">
              <h2 className="text-base font-semibold tracking-tight text-[#e2e8f0] truncate">{title}</h2>
              <p className="text-xs text-[#4B6A9B] truncate hidden sm:block">{description}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {/* Sync status */}
            <SyncDot status={syncStatus.status} lastSyncAt={syncStatus.lastSyncAt} />

            {/* Health indicator */}
            <div className="flex items-center gap-1.5 text-xs text-[#4B6A9B]">
              <span className={`h-2 w-2 rounded-full ${healthDotClass}`} />
              <span className="hidden sm:inline">{backendHealth.latencyMs}ms</span>
            </div>

            {/* Command palette button */}
            <button
              onClick={() => {
                const event = new CustomEvent("open-command-palette");
                window.dispatchEvent(event);
              }}
              className="flex items-center gap-2 rounded-[6px] border border-[#1E2D45] px-2.5 py-1.5 text-xs text-[#4B6A9B] hover:text-[#a8c4e8] hover:border-[#2D4163] transition-colors"
              aria-label="Open command palette"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
              </svg>
              <span className="hidden sm:inline">Search</span>
              <kbd className="hidden sm:inline border border-[#1E2D45] rounded px-1 text-[10px]">K</kbd>
            </button>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 p-4 md:p-6">
          {children}
        </div>
      </main>


    </div>
  );
}
