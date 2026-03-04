"use client";

import { useEffect, useState } from "react";

interface StatusBarData {
  gateway: {
    status: "healthy" | "degraded" | "critical";
    latencyMs: number;
  };
  sessions: {
    active: number;
    total: number;
  };
  quotas: {
    claude: {
      used: number;
      limit: number;
      percent: number;
    };
    minimax: {
      used: number;
      limit: number;
      percent: number;
    };
  };
  crons: {
    nextRun: string | null;
    countdownSec: number | null;
  };
  timestamp: string;
}

interface TooltipState {
  visible: boolean;
  content: string;
}

export function StatusBar() {
  const [data, setData] = useState<StatusBarData | null>(null);
  const [loading, setLoading] = useState(true);
  const [tooltip, setTooltip] = useState<TooltipState>({ visible: false, content: "" });
  const [cronCountdown, setCronCountdown] = useState<number | null>(null);

  // Fetch status bar data
  useEffect(() => {
    async function fetchStatusData() {
      try {
        const res = await fetch("/api/status-bar", { cache: "no-store" });
        if (res.ok) {
          const payload = (await res.json()) as StatusBarData;
          setData(payload);
          if (payload.crons.countdownSec !== null) {
            setCronCountdown(payload.crons.countdownSec);
          }
          setLoading(false);
        }
      } catch (e) {
        console.error("Failed to fetch status bar:", e);
        setLoading(false);
      }
    }

    fetchStatusData();
    const interval = setInterval(fetchStatusData, 10000);
    return () => clearInterval(interval);
  }, []);

  // Countdown timer for crons
  useEffect(() => {
    if (cronCountdown === null || cronCountdown <= 0) return;

    const timer = setInterval(() => {
      setCronCountdown((prev) => (prev === null || prev <= 0 ? null : prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [cronCountdown]);

  if (loading || !data) {
    return (
      <div className="h-10 glass border-t border-[#1E2D45] px-4 flex items-center justify-between text-xs text-[#4B6A9B]">
        <div>Loading status...</div>
      </div>
    );
  }

  // Gateway status dot
  const gatewayDotClass =
    data.gateway.status === "healthy"
      ? "bg-emerald-400 animate-pulse"
      : data.gateway.status === "degraded"
      ? "bg-amber-400 animate-glow-amber"
      : "bg-red-500 animate-glow-red";

  // Quota bar colors and text
  const getQuotaColor = (percent: number) => {
    if (percent >= 90) return "bg-red-500";
    if (percent >= 75) return "bg-amber-400";
    return "bg-emerald-400";
  };

  const formatCountdown = (seconds: number) => {
    if (seconds <= 0) return "now";
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h`;
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 h-10 glass border-t border-[#1E2D45] px-4 md:px-6 flex items-center justify-between gap-4">
      {/* Left: Gateway Status */}
      <div
        className="flex items-center gap-2 shrink-0 cursor-help"
        onMouseEnter={() =>
          setTooltip({
            visible: true,
            content: `Gateway: ${data.gateway.status} (${data.gateway.latencyMs}ms)`,
          })
        }
        onMouseLeave={() => setTooltip({ visible: false, content: "" })}
      >
        <div className={`h-2 w-2 rounded-full ${gatewayDotClass}`} />
        <span className="text-xs text-[#4B6A9B] hidden sm:inline">Gateway</span>
        {tooltip.visible && tooltip.content.includes("Gateway") && (
          <div className="absolute bottom-12 left-4 glass rounded px-2 py-1 text-xs text-[#a8c4e8] whitespace-nowrap animate-fade-in">
            {tooltip.content}
          </div>
        )}
      </div>

      {/* Center-Left: Sessions Count */}
      <div
        className="flex items-center gap-1.5 shrink-0 cursor-help"
        onMouseEnter={() =>
          setTooltip({
            visible: true,
            content: `${data.sessions.active}/${data.sessions.total} sessions active`,
          })
        }
        onMouseLeave={() => setTooltip({ visible: false, content: "" })}
      >
        <svg className="h-3 w-3 text-[#4B6A9B]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <span className="text-xs text-[#4B6A9B] hidden sm:inline">{data.sessions.active}</span>
        {tooltip.visible && tooltip.content.includes("sessions") && (
          <div className="absolute bottom-12 left-32 glass rounded px-2 py-1 text-xs text-[#a8c4e8] whitespace-nowrap animate-fade-in">
            {tooltip.content}
          </div>
        )}
      </div>

      {/* Center: Quota Usage Mini-Bar */}
      <div className="flex items-center gap-3 flex-1 min-w-0">
        {/* Claude quota */}
        <div
          className="flex flex-col gap-0.5 flex-1 min-w-0 cursor-help"
          onMouseEnter={() =>
            setTooltip({
              visible: true,
              content: `Claude: ${data.quotas.claude.used}/${data.quotas.claude.limit} (${data.quotas.claude.percent}%)`,
            })
          }
          onMouseLeave={() => setTooltip({ visible: false, content: "" })}
        >
          <div className="text-xs text-[#4B6A9B] hidden sm:inline">Claude</div>
          <div className="h-1.5 w-24 bg-[#0D1220] rounded-full overflow-hidden border border-[#1E2D45]">
            <div
              className={`h-full rounded-full transition-all ${getQuotaColor(data.quotas.claude.percent)}`}
              style={{ width: `${Math.min(100, data.quotas.claude.percent)}%` }}
            />
          </div>
          {tooltip.visible && tooltip.content.includes("Claude") && (
            <div className="absolute bottom-12 left-1/2 -translate-x-1/2 glass rounded px-2 py-1 text-xs text-[#a8c4e8] whitespace-nowrap animate-fade-in">
              {tooltip.content}
            </div>
          )}
        </div>

        {/* MiniMax quota */}
        <div
          className="flex flex-col gap-0.5 flex-1 min-w-0 cursor-help"
          onMouseEnter={() =>
            setTooltip({
              visible: true,
              content: `MiniMax: ${data.quotas.minimax.used}/${data.quotas.minimax.limit} (${data.quotas.minimax.percent}%)`,
            })
          }
          onMouseLeave={() => setTooltip({ visible: false, content: "" })}
        >
          <div className="text-xs text-[#4B6A9B] hidden sm:inline">MiniMax</div>
          <div className="h-1.5 w-24 bg-[#0D1220] rounded-full overflow-hidden border border-[#1E2D45]">
            <div
              className={`h-full rounded-full transition-all ${getQuotaColor(data.quotas.minimax.percent)}`}
              style={{ width: `${Math.min(100, data.quotas.minimax.percent)}%` }}
            />
          </div>
          {tooltip.visible && tooltip.content.includes("MiniMax") && (
            <div className="absolute bottom-12 right-1/2 translate-x-1/2 glass rounded px-2 py-1 text-xs text-[#a8c4e8] whitespace-nowrap animate-fade-in">
              {tooltip.content}
            </div>
          )}
        </div>
      </div>

      {/* Right: Next Cron Countdown */}
      {data.crons.nextRun && (
        <div
          className="flex items-center gap-1.5 shrink-0 cursor-help"
          onMouseEnter={() =>
            setTooltip({
              visible: true,
              content: `Next: ${data.crons.nextRun}`,
            })
          }
          onMouseLeave={() => setTooltip({ visible: false, content: "" })}
        >
          <svg className="h-3 w-3 text-[#4B6A9B]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-xs text-[#4B6A9B] hidden sm:inline font-mono">
            {cronCountdown !== null ? formatCountdown(cronCountdown) : "—"}
          </span>
          {tooltip.visible && tooltip.content.includes("Next") && (
            <div className="absolute bottom-12 right-4 glass rounded px-2 py-1 text-xs text-[#a8c4e8] whitespace-nowrap animate-fade-in">
              {tooltip.content}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
