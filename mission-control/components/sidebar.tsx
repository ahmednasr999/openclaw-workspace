"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { navGroups } from "@/lib/data";

export function Sidebar({ collapsed }: { collapsed: boolean }) {
  const pathname = usePathname();

  return (
    <aside
      className={`border-r border-[#1E2D45] bg-[#0A0F1E] flex flex-col transition-all duration-300 ${collapsed ? "w-16" : "w-full md:w-64"}`}
      style={{ minHeight: "100vh" }}
    >
      {/* Brand header */}
      <div className="px-4 py-5 border-b border-[#1E2D45]">
        <p className="text-[10px] uppercase tracking-[0.25em] text-[#4B6A9B] font-medium">Mission Control</p>
        {!collapsed && (
          <h1 className="mt-1 text-sm font-semibold text-[#e2e8f0]">v3 Console</h1>
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

      {/* Footer heartbeat area */}
      <div className="px-4 py-3 border-t border-[#1E2D45]">
        {!collapsed ? (
          <div className="flex items-center gap-2 text-xs text-[#4B6A9B]">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" id="sidebar-heartbeat" />
            <span id="sidebar-heartbeat-label">Gateway</span>
          </div>
        ) : (
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse inline-block" />
        )}
      </div>
    </aside>
  );
}
