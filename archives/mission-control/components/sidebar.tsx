"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { navGroups } from "@/lib/data";
import { useTheme } from "@/lib/theme-provider";

export function Sidebar({ collapsed }: { collapsed: boolean }) {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();

  return (
    <aside
      className={`border-r border-[var(--border)] bg-[var(--surface)] flex flex-col transition-all duration-300 ${collapsed ? "w-16" : "w-full md:w-64"}`}
      style={{ minHeight: "100vh" }}
    >
      {/* Brand header */}
      <div className="px-4 py-5 border-b border-[var(--border)]">
        <p className="text-[10px] uppercase tracking-[0.25em] text-[#4B6A9B] font-medium">Mission Control</p>
        {!collapsed && (
          <h1 className="mt-1 text-sm font-semibold text-[var(--foreground)]">v3 Console</h1>
        )}
      </div>

      {/* Nav groups */}
      <nav className="flex-1 overflow-y-auto px-2 py-4 space-y-5">
        {navGroups.map((group) => (
          <section key={group.label}>
            {!collapsed && (
              <h3 className="mb-2 px-2 text-[10px] uppercase tracking-[0.2em] text-[#2D4163] font-semibold">
                {group.label}
              </h3>
            )}
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    title={item.label}
                    className={`
                      relative block rounded-[8px] px-3 py-2 text-sm transition-all duration-150 overflow-hidden
                      ${active
                        ? "sidebar-active"
                        : "text-[#6B8AAE] hover:bg-[rgba(79,142,247,0.05)] hover:text-[#a8c4e8] border border-transparent hover:border-[rgba(31,45,69,0.4)]"
                      }
                    `}
                  >
                    {collapsed ? (
                      <span className="text-xs font-mono font-semibold">{item.short}</span>
                    ) : (
                      item.label
                    )}
                  </Link>
                );
              })}
            </div>
          </section>
        ))}
      </nav>

      {/* Footer: Theme toggle + heartbeat */}
      <div className="px-4 py-3 border-t border-[var(--border)]">
        {!collapsed ? (
          <div className="flex items-center justify-between">
            <button
              onClick={toggleTheme}
              className="flex items-center gap-2 text-xs text-[#4B6A9B] hover:text-[var(--foreground)] transition-colors"
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            >
              {theme === 'dark' ? (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
              <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
            </button>
            <div className="flex items-center gap-2 text-xs text-[#4B6A9B]">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" id="sidebar-heartbeat" />
              <span id="sidebar-heartbeat-label">Gateway</span>
            </div>
          </div>
        ) : (
          <button
            onClick={toggleTheme}
            className="h-6 w-6 flex items-center justify-center text-[#4B6A9B] hover:text-[var(--foreground)] transition-colors"
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>
        )}
      </div>
    </aside>
  );
}
