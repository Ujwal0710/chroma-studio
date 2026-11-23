"use client";

import React, { useState, useEffect } from "react";
import { 
  Layers, Heart, ThumbsDown, Shuffle, Lock, Unlock, 
  Sparkles, Dna, Upload
} from "lucide-react";
import { api } from "@/lib/api";
import { PaletteConcept, RoomAnalysisResponse, ChromaDNA } from "@/lib/types";

interface PaletteLabViewProps {
  analysis: RoomAnalysisResponse | null;
  primaryHex: string;
  onSelectTone: (hex: string) => void;
  onNavigateToUpload?: () => void;
}

export function PaletteLabView({
  analysis,
  primaryHex,
  onSelectTone,
  onNavigateToUpload,
}: PaletteLabViewProps) {
  const [concepts, setConcepts] = useState<PaletteConcept[]>([]);
  const [activeConceptIndex, setActiveConceptIndex] = useState<number>(0);
  const [lockedIndices, setLockedIndices] = useState<number[]>([]);
  const [dna, setDna] = useState<ChromaDNA | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  // Load palette concepts ONLY when an analysed room exists
  useEffect(() => {
    if (!analysis) {
      setConcepts([]);
      return;
    }

    async function loadPalettes() {
      setLoading(true);
      setErrorMsg(null);
      try {
        const res = await api.generatePalettes({
          extracted: analysis?.dominant_tones,
          dominant_tones: analysis?.dominant_tones,
          room_analysis: analysis?.room_analysis,
          primary_hex: primaryHex,
          room_type: analysis?.room_analysis?.detected_room_type || "Living Room",
          interior_style: analysis?.room_analysis?.detected_style || "Modern",
        });

        const list = Array.isArray(res) ? res : (res as any)?.concepts || [];
        setConcepts(list);

        const dnaRes = await api.getDNA();
        setDna(dnaRes);
      } catch (err: any) {
        console.error("Failed to load palette concepts:", err);
        setErrorMsg(err.message || "Failed to generate palettes.");
      } finally {
        setLoading(false);
      }
    }

    loadPalettes();
  }, [analysis, primaryHex]);

  // If no room has been analysed yet, show the proper empty state
  if (!analysis) {
    return (
      <div className="p-12 rounded-2xl bg-[#1B1E19] border border-[#2E332B] text-center space-y-5">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-[#242822] border border-[#2E332B] flex items-center justify-center text-[#B85C38]">
          <Layers className="w-8 h-8" />
        </div>
        <div className="max-w-md mx-auto space-y-2">
          <h3 className="text-xl font-serif text-[#F4F1EA]">
            Upload a room photo first
          </h3>
          <p className="text-xs text-[#A8A69E] leading-relaxed">
            Palette Lab generates mathematically balanced 60-30-10 architectural harmonies and CIELAB concepts based on your room&apos;s physical surfaces and lighting.
          </p>
        </div>
        {onNavigateToUpload && (
          <button
            onClick={onNavigateToUpload}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full text-xs font-semibold text-[#121411] bg-[#F4F1EA] hover:bg-white transition-all cursor-pointer shadow-md"
          >
            <Upload className="w-3.5 h-3.5" />
            Go to Studio &amp; Upload Photo
          </button>
        )}
      </div>
    );
  }

  const activeConcept = concepts[activeConceptIndex] || null;

  const handleFavorite = async () => {
    if (!activeConcept) return;
    try {
      await api.favouritePalette(activeConcept);
      setFeedbackMsg(`Saved "${activeConcept.name}" to Chroma Memory!`);
      const dnaRes = await api.getDNA();
      setDna(dnaRes);
      setTimeout(() => setFeedbackMsg(null), 3000);
    } catch {
      setFeedbackMsg("Could not save to favorites.");
    }
  };

  const handleReject = async () => {
    if (!activeConcept) return;
    try {
      await api.rejectPalette(activeConcept);
      setFeedbackMsg(`Dismissed tones from "${activeConcept.name}".`);
      const dnaRes = await api.getDNA();
      setDna(dnaRes);
      setTimeout(() => setFeedbackMsg(null), 3000);
    } catch {
      setFeedbackMsg("Could not record dismissal.");
    }
  };

  const toggleLock = (idx: number) => {
    setLockedIndices((prev) =>
      prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx]
    );
  };

  const handleSwapRoles = async (fromIdx: number, toIdx: number) => {
    if (!activeConcept) return;
    const roleKeys = ["primary_wall", "secondary_wall", "accent", "trim"];
    const fromRole = roleKeys[fromIdx];
    const toRole = roleKeys[toIdx];

    try {
      const updatedConcept = await api.swapPaletteRole(activeConcept, fromRole, toRole);
      const updated = [...concepts];
      updated[activeConceptIndex] = updatedConcept;
      setConcepts(updated);
      setFeedbackMsg(`Swapped ${fromRole.replace("_", " ")} with ${toRole.replace("_", " ")}`);
      setTimeout(() => setFeedbackMsg(null), 2500);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to swap roles.");
    }
  };

  // Helper to get swatch list safely
  const getConceptColors = (c: PaletteConcept) => {
    if (c.colors && c.colors.length > 0) return c.colors;
    return [c.primary_wall, c.secondary_wall, c.accent, c.trim].filter(Boolean);
  };

  return (
    <div className="space-y-8">
      {/* Header bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-[#1B1E19] border border-[#2E332B]">
        <div>
          <span className="text-xs uppercase tracking-widest text-[#B85C38] font-bold block mb-1">
            Harmonic Balance &amp; 60-30-10 Rule
          </span>
          <h2 className="text-2xl font-serif text-[#F4F1EA]">
            Architectural Palette Atelier
          </h2>
        </div>

        {feedbackMsg && (
          <div className="px-4 py-2 rounded-xl bg-[#242822] border border-[#B85C38]/40 text-xs text-[#F4F1EA] flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[#B85C38]" />
            {feedbackMsg}
          </div>
        )}
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/60 text-xs text-red-200">
          {errorMsg}
        </div>
      )}

      {loading && (
        <div className="p-8 text-center text-xs text-[#A8A69E]">
          Computing CIEDE2000 chromatic harmonies from room tones...
        </div>
      )}

      {/* 4 Concept Tabs */}
      {concepts.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {concepts.map((concept, idx) => {
            const swatchList = getConceptColors(concept);
            return (
              <div
                key={concept.id || idx}
                onClick={() => setActiveConceptIndex(idx)}
                className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between ${
                  activeConceptIndex === idx
                    ? "bg-[#242822] border-[#B85C38] shadow-lg shadow-[#B85C38]/10"
                    : "bg-[#1B1E19] border-[#2E332B] hover:border-[#444B40]"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] uppercase tracking-wider text-[#A8A69E] font-medium">
                      Concept {idx + 1}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#121411] text-[#B85C38] font-mono">
                      {concept.harmony_type || "Harmonic"}
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-[#F4F1EA] mb-1">
                    {concept.name}
                  </h3>
                  <p className="text-[11px] text-[#A8A69E] line-clamp-2 mb-3">
                    {concept.description}
                  </p>
                </div>

                {/* Mini swatch strip */}
                <div className="flex h-5 rounded-md overflow-hidden border border-[#2E332B]">
                  {swatchList.map((c, cIdx) => (
                    <div
                      key={cIdx}
                      className="h-full flex-1"
                      style={{ backgroundColor: c?.hex || "#CCCCCC" }}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Active Concept In-Depth Playground */}
      {activeConcept && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Main 60-30-10 Distribution Card (8 cols) */}
          <div className="lg:col-span-8 p-6 rounded-2xl bg-[#1B1E19] border border-[#2E332B] space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-serif text-[#F4F1EA]">
                  {activeConcept.name} — Role Allocation
                </h3>
                <span className="text-xs text-[#A8A69E]">
                  Atmosphere: {activeConcept.atmosphere || "Sophisticated Interior"}
                </span>
              </div>

              {/* Memory Action buttons */}
              <div className="flex items-center gap-2">
                <button
                  onClick={handleFavorite}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#2E332B] hover:border-[#B85C38] text-xs text-[#F4F1EA] bg-[#242822] hover:bg-[#2E332B] transition-colors cursor-pointer"
                >
                  <Heart className="w-3.5 h-3.5 text-rose-500 fill-current" />
                  Save Favourite
                </button>
                <button
                  onClick={handleReject}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#2E332B] hover:border-red-500/40 text-xs text-[#A8A69E] hover:text-[#F4F1EA] bg-[#242822] hover:bg-[#2E332B] transition-colors cursor-pointer"
                >
                  <ThumbsDown className="w-3.5 h-3.5" />
                  Dismiss
                </button>
              </div>
            </div>

            {/* Visual 60-30-10 Proportion Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-[#A8A69E]">
                <span>Dominant Plane (60%)</span>
                <span>Secondary Surface (30%)</span>
                <span>Accent Focal (10%)</span>
              </div>
              <div className="flex h-12 rounded-xl overflow-hidden border border-[#2E332B] shadow-inner">
                {getConceptColors(activeConcept).slice(0, 3).map((col, idx) => {
                  const widthClass = idx === 0 ? "w-[60%]" : idx === 1 ? "w-[30%]" : "w-[10%]";
                  return (
                    <div
                      key={idx}
                      onClick={() => onSelectTone(col.hex)}
                      className={`${widthClass} h-full relative group cursor-pointer transition-transform hover:brightness-110 flex items-center justify-center`}
                      style={{ backgroundColor: col.hex }}
                    >
                      <span className="opacity-0 group-hover:opacity-100 transition-opacity bg-black/75 px-2 py-0.5 rounded text-[10px] text-white font-mono">
                        {col.hex}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Individual Swatch Cards with lock & role swap */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              {getConceptColors(activeConcept).slice(0, 3).map((col, idx) => {
                const isLocked = lockedIndices.includes(idx);
                const roleName = idx === 0 ? "Dominant 60%" : idx === 1 ? "Secondary 30%" : "Accent 10%";
                return (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-[#242822] border border-[#2E332B] flex flex-col justify-between space-y-3"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-[#A8A69E]">
                          {roleName}
                        </span>
                        <button
                          onClick={() => toggleLock(idx)}
                          className="text-[#A8A69E] hover:text-[#F4F1EA] cursor-pointer"
                          title={isLocked ? "Unlock Tone" : "Lock Tone"}
                        >
                          {isLocked ? (
                            <Lock className="w-3.5 h-3.5 text-[#B85C38]" />
                          ) : (
                            <Unlock className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </div>

                      <div
                        className="w-full h-16 rounded-lg mb-3 shadow-inner border border-white/10 cursor-pointer"
                        style={{ backgroundColor: col.hex }}
                        onClick={() => onSelectTone(col.hex)}
                      />

                      <div className="font-mono text-xs text-[#F4F1EA] font-semibold">
                        {col.hex}
                      </div>
                      <div className="text-[11px] text-[#A8A69E]">
                        {col.name || "Architectural Shade"}
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-[#2E332B]">
                      <button
                        onClick={() => onSelectTone(col.hex)}
                        className="text-[10px] text-[#B85C38] hover:underline cursor-pointer"
                      >
                        Apply to Wall &rarr;
                      </button>
                      {idx < 2 && (
                        <button
                          onClick={() => handleSwapRoles(idx, idx + 1)}
                          className="text-[10px] text-[#A8A69E] hover:text-white flex items-center gap-1 cursor-pointer"
                          title="Swap with next role"
                        >
                          <Shuffle className="w-3 h-3" /> Swap
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Chroma DNA Signature Strip (4 cols) */}
          <div className="lg:col-span-4 p-6 rounded-2xl bg-[#1B1E19] border border-[#2E332B] space-y-5">
            <div className="flex items-center gap-2">
              <Dna className="w-5 h-5 text-[#B85C38]" />
              <h3 className="text-base font-serif text-[#F4F1EA]">
                Your Chroma DNA Profile
              </h3>
            </div>
            <p className="text-xs text-[#A8A69E] leading-relaxed">
              Transparent preference signature updated whenever you save or dismiss palettes.
            </p>

            {dna ? (
              <div className="space-y-3 pt-2">
                <div className="p-3 rounded-xl bg-[#242822] border border-[#2E332B]">
                  <span className="text-[10px] uppercase tracking-wider text-[#A8A69E] block">
                    Design Signature
                  </span>
                  <span className="text-xs font-semibold text-[#F4F1EA]">
                    {dna.signature_name}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-[#242822] border border-[#2E332B]">
                  <span className="text-[10px] uppercase tracking-wider text-[#A8A69E] block">
                    Temperature Tendency
                  </span>
                  <span className="text-xs font-semibold text-[#B85C38]">
                    {dna.temperature_bias}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-[#242822] border border-[#2E332B]">
                  <span className="text-[10px] uppercase tracking-wider text-[#A8A69E] block">
                    Contrast Profile
                  </span>
                  <span className="text-xs font-semibold text-[#F4F1EA]">
                    {dna.contrast_level}
                  </span>
                </div>

                {dna.signature_swatches && (
                  <div className="p-3 rounded-xl bg-[#242822] border border-[#2E332B]">
                    <span className="text-[10px] uppercase tracking-wider text-[#A8A69E] block mb-2">
                      Signature Palette
                    </span>
                    <div className="flex h-6 rounded-lg overflow-hidden border border-[#2E332B]">
                      {dna.signature_swatches.map((sw, sIdx) => (
                        <div
                          key={sIdx}
                          className="flex-1 h-full"
                          style={{ backgroundColor: sw.hex }}
                          title={`${sw.name}: ${sw.hex}`}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-xs text-[#A8A69E]">
                Analyzing taste memory...
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
