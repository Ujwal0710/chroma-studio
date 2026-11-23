"use client";

import React, { useState, useEffect } from "react";
import { Clock, RotateCcw, Plus, Check, Trash2, Calendar } from "lucide-react";
import { api } from "@/lib/api";
import { TimelineSnapshot } from "@/lib/types";

interface TimelineViewProps {
  currentPaletteData: any;
  onRollbackToPalette: (palette: any) => void;
}

export function TimelineView({ currentPaletteData, onRollbackToPalette }: TimelineViewProps) {
  const [snapshots, setSnapshots] = useState<TimelineSnapshot[]>([]);
  const [newLabel, setNewLabel] = useState<string>("");
  const [notes, setNotes] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [msg, setMsg] = useState<string | null>(null);

  const loadTimeline = async () => {
    setLoading(true);
    try {
      const res = await api.getTimeline("main_residence_project");
      if (res.versions) {
        setSnapshots(res.versions);
      }
    } catch (err) {
      console.error("Failed to load timeline versions:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTimeline();
  }, []);

  const handleCreateSnapshot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLabel) return;
    try {
      await api.saveTimelineSnapshot({
        project_id: "main_residence_project",
        label: newLabel,
        palette_data: currentPaletteData || { current_tone: "#B85C38" },
        notes: notes || "Manual design milestone",
      });
      setNewLabel("");
      setNotes("");
      setMsg("Saved snapshot to timeline!");
      loadTimeline();
      setTimeout(() => setMsg(null), 3000);
    } catch (err: any) {
      setMsg("Failed to save snapshot.");
    }
  };

  const handleRollback = async (version: TimelineSnapshot) => {
    try {
      await api.rollbackTimeline(version.id);
      onRollbackToPalette(version.palette_data);
      setMsg(`Rolled back to "${version.label}".`);
      loadTimeline();
      setTimeout(() => setMsg(null), 3000);
    } catch (err: any) {
      setMsg("Rollback failed.");
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-[#1B1E19] border border-[#2E332B] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs uppercase tracking-widest text-[#B85C38] font-bold block mb-1">
            Reversible Design History
          </span>
          <h2 className="text-2xl font-serif text-[#F4F1EA]">
            Design Milestones &amp; Version Timeline
          </h2>
          <p className="text-xs text-[#A8A69E] mt-1 max-w-xl">
            Save complete color configurations and roll back without losing past experiments.
          </p>
        </div>

        {msg && (
          <div className="px-4 py-2 rounded-xl bg-[#242822] border border-[#B85C38]/40 text-xs text-[#F4F1EA] flex items-center gap-2">
            <Check className="w-4 h-4 text-[#4E8752]" />
            {msg}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Create Milestone Card (4 cols) */}
        <div className="lg:col-span-4 p-6 rounded-2xl bg-[#1B1E19] border border-[#2E332B] space-y-4">
          <h3 className="text-sm font-semibold text-[#F4F1EA] uppercase tracking-wider">
            Capture New Version
          </h3>
          <form onSubmit={handleCreateSnapshot} className="space-y-4">
            <div>
              <label className="text-xs text-[#A8A69E] block mb-1">Milestone Label</label>
              <input
                type="text"
                placeholder="e.g. Living Room — Autumn Terracotta"
                value={newLabel}
                onChange={(e) => setNewLabel(e.target.value)}
                required
                className="w-full px-3 py-2 rounded-lg bg-[#242822] border border-[#2E332B] text-xs text-[#F4F1EA] focus:border-[#B85C38] focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-[#A8A69E] block mb-1">Notes / Rationale</label>
              <textarea
                placeholder="Client preferred warmer saturation on south-facing wall..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 rounded-lg bg-[#242822] border border-[#2E332B] text-xs text-[#F4F1EA] focus:border-[#B85C38] focus:outline-none"
              />
            </div>
            <button
              type="submit"
              className="w-full py-2.5 rounded-xl bg-[#B85C38] hover:bg-[#D47149] text-xs font-semibold text-white transition-colors flex items-center justify-center gap-2 cursor-pointer"
            >
              <Plus className="w-4 h-4" /> Save Version Snapshot
            </button>
          </form>
        </div>

        {/* Timeline Snapshots List (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          {snapshots.length === 0 ? (
            <div className="p-12 rounded-2xl bg-[#1B1E19] border border-[#2E332B] text-center text-xs text-[#A8A69E]">
              No snapshots saved yet. Save your first version milestone using the form on the left.
            </div>
          ) : (
            snapshots.map((snap) => (
              <div
                key={snap.id}
                className="p-5 rounded-2xl bg-[#1B1E19] border border-[#2E332B] flex items-center justify-between gap-4 hover:border-[#444B40] transition-colors"
              >
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-xl bg-[#242822] border border-[#2E332B] flex items-center justify-center shrink-0 text-[#B85C38]">
                    <Clock className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold text-[#F4F1EA]">
                        {snap.label}
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#242822] text-[#A8A69E]">
                        v{snap.version_num}
                      </span>
                    </div>
                    <p className="text-xs text-[#A8A69E] mb-2">
                      {snap.notes || "No notes recorded"}
                    </p>
                    <div className="flex items-center gap-2 text-[10px] text-[#A8A69E]">
                      <Calendar className="w-3 h-3" />
                      <span>{new Date(snap.timestamp).toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => handleRollback(snap)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#242822] hover:bg-[#B85C38] border border-[#2E332B] text-xs font-medium text-[#F4F1EA] transition-all hover:scale-105 shrink-0"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  Rollback
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
