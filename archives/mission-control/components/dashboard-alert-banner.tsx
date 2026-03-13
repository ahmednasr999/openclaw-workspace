"use client";

import { useState } from "react";

interface Props {
  urgentCount: number;
  urgentTitles: string[];
}

export function DashboardAlertBanner({ urgentCount, urgentTitles }: Props) {
  const [dismissed, setDismissed] = useState(false);

  if (urgentCount === 0 || dismissed) return null;

  return (
    <div className="mb-4 animate-slide-down rounded-[10px] overflow-hidden">
      <div className="gradient-alert p-3 flex items-start justify-between gap-3 border border-red-800/40">
        <div className="flex items-start gap-2.5">
          <svg className="h-4 w-4 text-amber-300 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          </svg>
          <div>
            <p className="text-sm font-semibold text-amber-200">
              {urgentCount} task{urgentCount > 1 ? "s" : ""} due within 48 hours
            </p>
            {urgentTitles.length > 0 && (
              <p className="mt-0.5 text-xs text-amber-300/80">
                {urgentTitles.join(" | ")}
              </p>
            )}
          </div>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="shrink-0 text-amber-300/60 hover:text-amber-200 transition-colors"
          aria-label="Dismiss alert"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
