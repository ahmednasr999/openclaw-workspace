"use client";

import { useEffect, useState } from "react";

const SHORTCUTS = [
  { keys: ["Ctrl", "K"], description: "Open command palette" },
  { keys: ["Ctrl", "?"], description: "Show keyboard shortcuts" },
  { keys: ["Esc"], description: "Close modal / palette" },
  { keys: ["G", "D"], description: "Go to Dashboard" },
  { keys: ["G", "T"], description: "Go to Tasks" },
  { keys: ["G", "P"], description: "Go to Pipeline" },
  { keys: ["G", "M"], description: "Go to Memory" },
  { keys: ["G", "S"], description: "Go to Settings" },
  { keys: ["Ctrl", "N"], description: "Create new task" },
  { keys: ["/"], description: "Focus search" },
];

export function KeyboardShortcutsModal() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === "?") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(4px)" }}
      onClick={() => setOpen(false)}
    >
      <div
        className="glass-dark rounded-[12px] w-full max-w-lg p-6 animate-fade-in"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-[var(--foreground)]">Keyboard Shortcuts</h2>
          <button
            onClick={() => setOpen(false)}
            className="text-[#4B6A9B] hover:text-[var(--foreground)] transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-2">
          {SHORTCUTS.map((shortcut, i) => (
            <div key={i} className="flex items-center justify-between py-2 border-b border-[var(--border)] last:border-0">
              <span className="text-sm text-[#6B8AAE]">{shortcut.description}</span>
              <div className="flex gap-1">
                {shortcut.keys.map((key, j) => (
                  <kbd
                    key={j}
                    className="px-2 py-1 text-xs font-mono bg-[var(--surface)] border border-[var(--border)] rounded text-[var(--foreground)]"
                  >
                    {key}
                  </kbd>
                ))}
              </div>
            </div>
          ))}
        </div>

        <p className="mt-4 text-xs text-[#4B6A9B] text-center">
          Press <kbd className="px-1 py-0.5 bg-[var(--surface)] border border-[var(--border)] rounded">Ctrl</kbd> + <kbd className="px-1 py-0.5 bg-[var(--surface)] border border-[var(--border)] rounded">?</kbd> to toggle this help
        </p>
      </div>
    </div>
  );
}
