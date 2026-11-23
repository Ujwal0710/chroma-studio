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
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[9999] flex items-center gap-2 px-4 py-2 rounded-full bg-red-900/90 border border-red-700 text-xs text-red-200 shadow-lg backdrop-blur-sm animate-in fade-in slide-in-from-bottom-2">
      <WifiOff className="w-3.5 h-3.5" />
      Backend offline — start the server with <code className="ml-1 font-mono text-red-100">uvicorn backend.main:app</code>
    </div>
  );
}
