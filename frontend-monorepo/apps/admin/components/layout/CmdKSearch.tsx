"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const commands = [
  {
    name: "Pulse",
    description: "System overview",
    shortcut: "P",
    path: "/pulse",
  },
  {
    name: "Customers",
    description: "Manage customers",
    shortcut: "C",
    path: "/customers",
  },
  {
    name: "Engine",
    description: "AI provider management",
    shortcut: "E",
    path: "/engine",
  },
  {
    name: "Telecom",
    description: "Voice infrastructure",
    shortcut: "T",
    path: "/telecom",
  },
  {
    name: "Security",
    description: "Security controls",
    shortcut: "S",
    path: "/security",
  },
];

export default function CmdKSearch() {
  const router = useRouter();

  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((current) => !current);
      }

      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  const filteredCommands = commands.filter((command) =>
    command.name.toLowerCase().includes(search.toLowerCase())
  );

  function navigate(path: string) {
    setOpen(false);
    setSearch("");
    router.push(path);
  }

  return (
    <>
      {/* Search button */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-400 hover:border-zinc-700 hover:text-white"
      >
        <span>⌕</span>

        <span className="hidden sm:inline">
          Search
        </span>

        <kbd className="hidden rounded border border-zinc-700 px-1.5 py-0.5 text-[10px] text-zinc-500 sm:inline">
          Ctrl K
        </kbd>
      </button>

      {/* Command palette */}
      {open && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/70 px-4 pt-[15vh]">
          {/* Close when clicking background */}
          <button
            type="button"
            aria-label="Close command palette"
            className="absolute inset-0 cursor-default"
            onClick={() => setOpen(false)}
          />

          <div className="relative w-full max-w-xl overflow-hidden rounded-xl border border-zinc-700 bg-zinc-950 shadow-2xl">
            {/* Search */}
            <div className="border-b border-zinc-800 p-4">
              <input
                autoFocus
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search commands..."
                className="w-full bg-transparent text-sm text-white outline-none placeholder:text-zinc-600"
              />
            </div>

            {/* Commands */}
            <div className="max-h-80 overflow-y-auto p-2">
              {filteredCommands.length > 0 ? (
                filteredCommands.map((command) => (
                  <button
                    key={command.path}
                    type="button"
                    onClick={() => navigate(command.path)}
                    className="flex w-full items-center justify-between rounded-lg px-3 py-3 text-left hover:bg-zinc-900"
                  >
                    <div>
                      <div className="text-sm font-medium text-white">
                        {command.name}
                      </div>

                      <div className="mt-1 text-xs text-zinc-500">
                        {command.description}
                      </div>
                    </div>

                    <kbd className="rounded border border-zinc-800 px-2 py-1 text-xs text-zinc-500">
                      {command.shortcut}
                    </kbd>
                  </button>
                ))
              ) : (
                <div className="px-3 py-8 text-center text-sm text-zinc-500">
                  No commands found.
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="border-t border-zinc-800 px-4 py-3 text-[10px] text-zinc-600">
              Press ESC to close
            </div>
          </div>
        </div>
      )}
    </>
  );
}