"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Sun, Sunset, CloudSun, Sunrise, Layers, RefreshCw, AlertCircle, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { DaylightSimResponse, MaterialScore, PaletteConcept } from "@/lib/types";

interface DaylightMaterialsViewProps {
  currentFile: File | null;
  primaryHex: string;
  palette?: PaletteConcept | null;
  /** Set to true once a room has been analysed (colours extracted). */
  hasAnalysis?: boolean;
}

type LoadState = "idle" | "loading" | "success" | "error";

export function DaylightMaterialsView({
  currentFile,
  primaryHex,
  palette,
  hasAnalysis = false,
}: DaylightMaterialsViewProps) {
  const [activePreset, setActivePreset] = useState<string>("noon_5500k");
  const [daylightData, setDaylightData] = useState<DaylightSimResponse | null>(null);
  const [materials, setMaterials] = useState<MaterialScore[]>([]);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  const [materialsState, setMaterialsState] = useState<LoadState>("idle");
  const [materialsError, setMaterialsError] = useState<string>("");

  // ------------------------------------------------------------------
  // Load materials scores — only when we have a valid hex to score
  // ------------------------------------------------------------------
  const loadMaterials = useCallback(async () => {
    if (!primaryHex) return;

    setMaterialsState("loading");
    setMaterialsError("");
    try {
      const res = await api.scoreMaterials(primaryHex, palette ?? undefined);
      if (res.scores) {
        setMaterials(res.scores);
      }
      setMaterialsState("success");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load material scores.";
      console.error("Failed to load materials scores:", msg);
      setMaterialsError(msg);
      setMaterialsState("error");
    }
  }, [primaryHex, palette]);

  useEffect(() => {
    // Don't call scoreMaterials until an analysed room and palette exist
    if (!hasAnalysis || !palette) {
      setMaterialsState("idle");
      return;
    }
    loadMaterials();
  }, [hasAnalysis, palette, loadMaterials]);

  // Simulate daylight when preset or image changes
  useEffect(() => {
    if (!currentFile) return;

    async function runDaylight() {
      if (!currentFile) return;
      setIsSimulating(true);
      try {
        const res = await api.simulateDaylight(currentFile, activePreset);
        setDaylightData(res);
      } catch (err) {
        console.error("Failed to simulate daylight:", err);
      } finally {
        setIsSimulating(false);
      }
    }

    runDaylight();
  }, [currentFile, activePreset]);

  const presets = [
    { id: "morning_3200k", name: "Morning Sun", kelvin: "3200K", icon: Sunrise, desc: "Warm slanted golden rays" },
    { id: "noon_5500k", name: "High Noon", kelvin: "5500K", icon: Sun, desc: "True neutral daylight spectrum" },
    { id: "overcast_6800k", name: "Overcast Sky", kelvin: "6800K", icon: CloudSun, desc: "Cool diffused shadows" },
    { id: "evening_2700k", name: "Golden Hour / Tungsten", kelvin: "2700K", icon: Sunset, desc: "Deep amber warm ambience" },
  ];

  // ------------------------------------------------------------------
  // Materials section sub-renders
  // ------------------------------------------------------------------

  const renderMaterialsEmpty = () => (
    <div className="flex flex-col items-center justify-center py-16 text-center space-y-3">
      <Layers className="w-10 h-10 text-[#2E332B]" />
      <p className="text-sm text-[#A8A69E] max-w-md">
        Upload and analyse a room photo in the <span className="text-[#F4F1EA] font-medium">Studio</span> tab first.
        Material compatibility scores will appear here once a palette is active.
      </p>
    </div>
  );

  const renderMaterialsLoading = () => (
    <div className="flex flex-col items-center justify-center py-16 text-center space-y-3">
      <Loader2 className="w-8 h-8 text-[#B85C38] animate-spin" />
      <p className="text-xs text-[#A8A69E]">Scoring material compatibility…</p>
    </div>
  );

  const renderMaterialsError = () => (
    <div className="flex flex-col items-center justify-center py-16 text-center space-y-4">
      <AlertCircle className="w-10 h-10 text-red-400" />
      <p className="text-sm text-red-400 max-w-md">{materialsError}</p>
      <button
        onClick={loadMaterials}
        className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium text-[#F4F1EA] bg-[#B85C38] hover:bg-[#D47149] transition-colors"
      >
        <RefreshCw className="w-3.5 h-3.5" />
        Retry
      </button>
    </div>
  );

  return (
    <div className="space-y-10">
      {/* Daylight Simulator Section */}
      <div className="p-6 rounded-2xl bg-[#1B1E19] border border-[#2E332B] space-y-6">
        <div>
          <span className="text-xs uppercase tracking-widest text-[#B85C38] font-bold block mb-1">
            Chrono-Photometric Simulation
          </span>
          <h2 className="text-2xl font-serif text-[#F4F1EA]">
            Daylight &amp; Kelvin Color Temperature Shift
          </h2>
          <p className="text-xs text-[#A8A69E] mt-1 max-w-xl">
            Colours appear dramatically different under 3200K morning light versus 6800K overcast skies.
            Test physical metamers before committing to paint.
          </p>
        </div>

        {/* Preset Selector */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {presets.map((p) => {
            const Icon = p.icon;
            const isSelected = activePreset === p.id;
            return (
              <button
                key={p.id}
                onClick={() => setActivePreset(p.id)}
                className={`p-4 rounded-xl border transition-all text-left flex flex-col justify-between ${
                  isSelected
                    ? "bg-[#242822] border-[#B85C38] shadow-md shadow-[#B85C38]/15"
                    : "bg-[#121411]/60 border-[#2E332B] hover:border-[#444B40]"
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <Icon className={`w-5 h-5 ${isSelected ? "text-[#B85C38]" : "text-[#A8A69E]"}`} />
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#121411] text-[#F4F1EA]">
                    {p.kelvin}
                  </span>
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-[#F4F1EA] mb-0.5">
                    {p.name}
                  </h4>
                  <span className="text-[10px] text-[#A8A69E]">
                    {p.desc}
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Daylight Canvas */}
        <div className="relative rounded-xl overflow-hidden bg-black/40 border border-[#2E332B] min-h-[380px] flex items-center justify-center">
          {daylightData ? (
            <img
              src={daylightData.simulated_image}
              alt="Daylight Simulation"
              className="w-full max-h-[500px] object-contain"
            />
          ) : currentFile ? (
            <img
              src={URL.createObjectURL(currentFile)}
              alt="Room Preview"
              className="w-full max-h-[500px] object-contain"
            />
          ) : (
            <div className="text-center p-8 text-[#A8A69E] text-xs">
              Upload a room photo in the Studio tab to preview daylight shifts.
            </div>
          )}

          {isSimulating && (
            <div className="absolute inset-0 bg-[#121411]/70 backdrop-blur-sm flex items-center justify-center text-xs text-[#F4F1EA]">
              Simulating Planckian chromatic adaptation...
            </div>
          )}
        </div>
      </div>

      {/* 9 Architectural Materials Compatibility Grid */}
      <div className="p-6 rounded-2xl bg-[#1B1E19] border border-[#2E332B] space-y-6">
        <div>
          <span className="text-xs uppercase tracking-widest text-[#B85C38] font-bold block mb-1">
            Material Affinity &amp; Texture Compatibility
          </span>
          <h2 className="text-2xl font-serif text-[#F4F1EA]">
            9 Architectural Substrate Scores
          </h2>
          <p className="text-xs text-[#A8A69E] mt-1 max-w-xl">
            Evaluated against current target shade ({primaryHex}) using CIELAB chromatic distance and reflectance indexing.
          </p>
        </div>

        {/* State-dependent render */}
        {materialsState === "idle" && renderMaterialsEmpty()}
        {materialsState === "loading" && renderMaterialsLoading()}
        {materialsState === "error" && renderMaterialsError()}

        {materialsState === "success" && materials.length === 0 && renderMaterialsEmpty()}

        {materialsState === "success" && materials.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {materials.map((mat, idx) => (
              <div
                key={idx}
                data-testid="material-card"
                className="p-5 rounded-xl bg-[#242822] border border-[#2E332B] flex flex-col justify-between space-y-3"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-[#F4F1EA]">
                      {mat.name}
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                        mat.status === "Harmonious"
                          ? "bg-[#4E8752]/20 text-[#4E8752] border border-[#4E8752]/30"
                          : mat.status === "Balanced"
                          ? "bg-[#B85C38]/20 text-[#B85C38] border border-[#B85C38]/30"
                          : "bg-red-500/20 text-red-400 border border-red-500/30"
                      }`}
                    >
                      {mat.status}
                    </span>
                  </div>

                  <div className="text-[11px] text-[#A8A69E] mb-3">
                    Category: {mat.category}
                  </div>

                  <p className="text-xs text-[#F4F1EA] leading-relaxed">
                    {mat.notes}
                  </p>
                </div>

                <div className="pt-3 border-t border-[#2E332B] flex items-center justify-between text-[11px]">
                  <span className="text-[#A8A69E]">
                    Suggested: <span className="text-[#F4F1EA]">{mat.suggested_texture}</span>
                  </span>
                  <span className="font-mono text-xs text-[#B85C38] font-bold">
                    {mat.score}/100
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
