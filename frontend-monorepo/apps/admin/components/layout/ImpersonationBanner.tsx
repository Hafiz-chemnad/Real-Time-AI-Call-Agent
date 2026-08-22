"use client";

import { useState } from "react";

export default function ImpersonationBanner() {
  const [impersonating, setImpersonating] = useState(false);

  if (!impersonating) {
    return (
      <div className="border-b border-zinc-800 bg-zinc-950 px-4 py-2">
        <div className="flex items-center justify-between">
          <div className="text-xs text-zinc-500">
            Admin Mode
          </div>

          <button
            type="button"
            onClick={() => setImpersonating(true)}
            className="rounded-md border border-zinc-700 px-3 py-1.5 text-xs text-zinc-400 transition hover:bg-zinc-800 hover:text-white"
          >
            Enter God Mode
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="border-b border-yellow-800 bg-yellow-950/40 px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-yellow-900 text-yellow-300">
            ⚠
          </span>

          <div>
            <div className="text-sm font-semibold text-yellow-300">
              GOD MODE ACTIVE
            </div>

            <div className="text-xs text-yellow-500">
              You are currently impersonating Acme Corporation
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setImpersonating(false)}
          className="rounded-md border border-yellow-700 px-3 py-1.5 text-xs text-yellow-300 hover:bg-yellow-900"
        >
          Exit God Mode
        </button>
      </div>
    </div>
  );
}