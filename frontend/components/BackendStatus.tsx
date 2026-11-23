"use client";

import React, { useState, useEffect } from "react";
import { WifiOff } from "lucide-react";
import { api } from "@/lib/api";

/**
 * Polls GET /health on mount and every 30 s.
 * Shows a slim "Backend offline" banner when unreachable.
 */
export function BackendStatus() {
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function check() {
      try {
        await api.getHealth();
        if (mounted) setOffline(false);
      } catch {
        if (mounted) setOffline(true);
      }
    }

    check();
    const id = setInterval(check, 30_000);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, []);

  if (!offline) return null;

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[9999] flex items-center gap-2 px-4 py-2 rounded-full bg-[#1B1E19]/95 border border-amber-600/60 text-xs text-amber-200 shadow-xl backdrop-blur-md animate-in fade-in slide-in-from-bottom-2">
      <WifiOff className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
      <span>
        Backend connecting... <span className="text-[11px] text-[#A8A69E]">(Render free-tier may take ~45s on first wake-up)</span>
      </span>
    </div>
  );
}
