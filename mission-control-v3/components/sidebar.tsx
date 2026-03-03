"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { navGroups } from "@/lib/data";

export function Sidebar({ collapsed }: { collapsed: boolean }) {
  const pathname = usePathname();

  return (
    <aside className={`border-r border-zinc-800 bg-[#101010] p-4 transition-all ${collapsed ? "w-16" : "w-full md:w-72"}`}>
      <div className="mb-6">
        <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Mission Control v3</p>
        {!collapsed && <h1 className="text-lg font-semibold text-zinc-100">Single User Console</h1>}
      </div>
      <nav className="space-y-4">
        {navGroups.map((group) => (
          <section key={group.label}>
            {!collapsed && <h3 className="mb-2 text-xs uppercase tracking-wider text-zinc-500">{group.label}</h3>}
            <div className="space-y-2">
              {group.items.map((item) => {
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`block rounded-md border px-3 py-2 text-sm transition ${active ? "border-zinc-600 bg-zinc-900 text-zinc-100" : "border-transparent text-zinc-400 hover:border-zinc-800 hover:bg-zinc-900/50 hover:text-zinc-200"}`}
                    title={item.label}
                  >
                    {collapsed ? item.short : item.label}
                  </Link>
                );
              })}
            </div>
          </section>
        ))}
      </nav>
      <form action="/api/auth/logout" method="post" className="mt-8">
        <button type="submit" className="w-full rounded-md border border-zinc-700 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-900">{collapsed ? "Out" : "Sign out"}</button>
      </form>
    </aside>
  );
}
