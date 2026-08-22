"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const navigation = [
  {
    name: "Pulse",
    href: "/pulse",
    icon: "◉",
    description: "System overview",
  },
  {
    name: "Customers",
    href: "/customers",
    icon: "◌",
    description: "CRM & accounts",
  },
  {
    name: "Engine",
    href: "/engine",
    icon: "⚙",
    description: "AI providers",
  },
  {
    name: "Telecom",
    href: "/telecom",
    icon: "⌁",
    description: "Voice infrastructure",
  },
  {
    name: "Security",
    href: "/security",
    icon: "◇",
    description: "Security controls",
  },
];

export default function AdminSidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`flex min-h-screen flex-col border-r border-zinc-800 bg-zinc-950 text-white transition-all duration-300 ${
        collapsed ? "w-20" : "w-64"
      }`}
    >
      {/* Brand */}
      <div className="flex h-16 items-center justify-between border-b border-zinc-800 px-4">
        {!collapsed ? (
          <div>
            <div className="text-lg font-bold tracking-tight">
              CALL.AI
            </div>

            <div className="mt-0.5 text-[10px] uppercase tracking-[0.2em] text-zinc-500">
              Command Center
            </div>
          </div>
        ) : (
          <div className="mx-auto text-lg font-bold">
            CA
          </div>
        )}

        <button
          type="button"
          onClick={() => setCollapsed(!collapsed)}
          className="rounded-lg p-2 text-zinc-400 transition hover:bg-zinc-800 hover:text-white"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? "→" : "←"}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-5">
        {!collapsed && (
          <div className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-zinc-600">
            Operations
          </div>
        )}

        <div className="space-y-1">
          {navigation.map((item) => {
            const active =
              pathname === item.href ||
              pathname.startsWith(`${item.href}/`);

            return (
              <Link
                key={item.href}
                href={item.href}
                title={collapsed ? item.name : undefined}
                className={`group flex items-center gap-3 rounded-lg px-3 py-3 transition ${
                  active
                    ? "bg-zinc-800 text-white"
                    : "text-zinc-400 hover:bg-zinc-900 hover:text-white"
                }`}
              >
                {/* Icon */}
                <span
                  className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-sm ${
                    active
                      ? "bg-zinc-700 text-white"
                      : "text-zinc-500 group-hover:text-white"
                  }`}
                >
                  {item.icon}
                </span>

                {!collapsed && (
                  <div className="min-w-0">
                    <div className="text-sm font-medium">
                      {item.name}
                    </div>

                    <div
                      className={`truncate text-[10px] ${
                        active
                          ? "text-zinc-400"
                          : "text-zinc-600 group-hover:text-zinc-500"
                      }`}
                    >
                      {item.description}
                    </div>
                  </div>
                )}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* System status */}
      <div className="border-t border-zinc-800 p-3">
        <div
          className={`flex items-center gap-3 rounded-lg px-3 py-3 ${
            collapsed ? "justify-center" : ""
          }`}
        >
          <span className="relative flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-500 opacity-50" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-green-500" />
          </span>

          {!collapsed && (
            <div>
              <div className="text-xs font-medium">
                System Online
              </div>

              <div className="text-[10px] text-zinc-600">
                All services operational
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}