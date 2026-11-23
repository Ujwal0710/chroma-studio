"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Upload, Sparkles, RefreshCw, Download, Image as ImageIcon,
  Layers, Check, Columns, SplitSquareVertical, Sliders,
  ShieldCheck, AlertTriangle, Paintbrush, Undo2, SunMedium
} from "lucide-react";
import { api } from "@/lib/api";
import { RoomAnalysisResponse } from "@/lib/types";

interface StudioViewProps {
  currentFile: File | null;
  setCurrentFile: (f: File | null) => void;
  analysis: RoomAnalysisResponse | null;
  setAnalysis: (a: RoomAnalysisResponse | null) => void;
  selectedColor: string;
  setSelectedColor: (hex: string) => void;
}

export function StudioView({
  currentFile,
  setCurrentFile,
  analysis,
  setAnalysis,
  selectedColor,
  setSelectedColor,
}: StudioViewProps) {
  const [viewMode, setViewMode] = useState<"preview" | "side_by_side" | "split" | "mask">("preview");
  const [splitPos, setSplitPos] = useState<number>(50);
  const [intensity, setIntensity] = useState<number>(0.85);
  const [sensitivity, setSensitivity] = useState<number>(0.55);
  const [activeSurface, setActiveSurface] = useState<"wall" | "ceiling" | "trim" | "accent_wall">("wall");
  
  // Multi-surface color mapping
  const [surfaceColors, setSurfaceColors] = useState<{
    wall: string;
    ceiling: string;
    trim: string;
    accent_wall: string;
  }>({
    wall: selectedColor || "#3B82F6",
    ceiling: "#F8FAFC",
    trim: "#FFFFFF",
    accent_wall: "#D97706"
  });

  const [compensateLighting, setCompensateLighting] = useState<boolean>(true);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [recolouredImage, setRecolouredImage] = useState<string | null>(null);
  const [maskOverlayImage, setMaskOverlayImage] = useState<string | null>(null);
  const [maskRawPng, setMaskRawPng] = useState<string | null>(null);
  const [qualityGate, setQualityGate] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Manual brush correction mode
  const [brushMode, setBrushMode] = useState<"add" | "remove">("add");
  const [brushRadius, setBrushRadius] = useState<number>(18);
  const [manualCorrectionsCount, setManualCorrectionsCount] = useState<number>(0);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLDivElement>(null);

  // Sync selectedColor to active surface
  useEffect(() => {
    if (selectedColor) {
      setSurfaceColors(prev => ({
        ...prev,
        [activeSurface]: selectedColor
      }));
    }
  }, [selectedColor, activeSurface]);

  // Trigger recolouring whenever parameters change
  useEffect(() => {
    if (!currentFile) return;

    const timer = setTimeout(async () => {
      setIsProcessing(true);
      setErrorMsg(null);
      try {
        const res = await api.recolourRoom(
          currentFile,
          surfaceColors.wall,
          intensity,
          "cielab_perceptual",
          sensitivity,
          activeSurface,
          surfaceColors,
          compensateLighting
        );
        setRecolouredImage(res.recoloured_image || res.preview_image);

        // Fetch segmentation & quality gate if not yet loaded or when viewing mask
        if (!qualityGate || viewMode === "mask") {
          const segRes = await api.segmentRoom(currentFile, sensitivity);
          setMaskOverlayImage(segRes.mask_overlay || segRes.overlay_preview);
          setMaskRawPng(segRes.mask_png || segRes.mask_only);
          setQualityGate(segRes.metadata);
        }
      } catch (err: any) {
        setErrorMsg(err.message || "Failed to simulate wall recolouring.");
      } finally {
        setIsProcessing(false);
      }
    }, 280);

    return () => clearTimeout(timer);
  }, [currentFile, surfaceColors, intensity, sensitivity, activeSurface, compensateLighting, viewMode]);

  const handleFileUpload = async (file: File) => {
    setIsProcessing(true);
    setErrorMsg(null);
    setCurrentFile(file);
    try {
      const res = await api.analyseRoom(file);
      setAnalysis(res);
      if (res.tones && res.tones.length > 0) {
        setSelectedColor(res.tones[0].hex);
      }
      setRecolouredImage(res.preview_image || res.image_preview || null);

      // Initial segmentation
      const segRes = await api.segmentRoom(file, sensitivity);
      setMaskOverlayImage(segRes.mask_overlay || segRes.overlay_preview);
      setMaskRawPng(segRes.mask_png);
      setQualityGate(segRes.metadata);
    } catch (err: any) {
      setErrorMsg(err.message || "Error analyzing room photograph.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleClear = () => {
    setCurrentFile(null);
    setAnalysis(null);
    setRecolouredImage(null);
    setMaskOverlayImage(null);
    setMaskRawPng(null);
    setQualityGate(null);
    setErrorMsg(null);
    setManualCorrectionsCount(0);
  };

  // Interactive Tap / Click to refine mask
  const handleCanvasClick = async (e: React.MouseEvent<HTMLDivElement>) => {
    if (viewMode !== "mask" || !maskRawPng || !canvasRef.current) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Normalize coordinates relative to natural aspect ratio
    const normX = Math.round((clickX / rect.width) * 600);
    const normY = Math.round((clickY / rect.height) * 450);

    try {
      setIsProcessing(true);
      const res = await api.refineMask({
        mask_b64: maskRawPng,
        x: normX,
        y: normY,
        action: brushMode,
        brush_radius: brushRadius
      });

      if (res.mask_png) {
        setMaskRawPng(res.mask_png);
        setMaskOverlayImage(res.mask_png);
        setManualCorrectionsCount(prev => prev + 1);
      }
    } catch (err: any) {
      console.error("Mask refinement failed:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = () => {
    const targetUrl = recolouredImage || analysis?.preview_image;
    if (!targetUrl) return;
    const link = document.createElement("a");
    link.href = targetUrl;
    link.download = `chroma_studio_${activeSurface}_recolour.jpg`;
    link.click();
  };

  return (
    <div className="space-y-8" id="atelier-workspace">
      {/* Top Controls Strip */}
      <div className="p-6 rounded-2xl bg-[#1B1E19] border border-[#2E332B] flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-4 w-full md:w-auto">
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
          />

          {!currentFile ? (
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className="flex-1 md:flex-initial flex items-center justify-center gap-3 px-6 py-4 rounded-xl border border-dashed border-[#2E332B] hover:border-[#B85C38] bg-[#242822]/50 hover:bg-[#242822] cursor-pointer transition-colors"
            >
              <Upload className="w-5 h-5 text-[#B85C38]" />
              <div className="text-left">
                <span className="text-xs font-semibold text-[#F4F1EA] block">
                  Upload Room Photo
                </span>
                <span className="text-[10px] text-[#A8A69E]">
                  JPEG, PNG, or WEBP (Local SegFormer Neural Processing)
                </span>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg overflow-hidden bg-[#242822] border border-[#2E332B]">
                <img
                  src={analysis?.preview_image || URL.createObjectURL(currentFile)}
                  alt="Room Thumbnail"
                  className="w-full h-full object-cover"
                />
              </div>
              <div>
                <span className="text-xs font-medium text-[#F4F1EA] block truncate max-w-[200px]">
                  {currentFile.name}
                </span>
                <span className="text-[10px] text-[#4E8752] flex items-center gap-1">
                  <Check className="w-3 h-3" /> SegFormer Neural Engine Active
                </span>
              </div>
              <button
                onClick={handleClear}
                className="ml-3 px-3 py-1.5 rounded-lg border border-[#2E332B] text-xs text-[#A8A69E] hover:text-[#F4F1EA] hover:bg-[#242822] transition-colors"
              >
                Clear
              </button>
            </div>
          )}
        </div>

        {/* View Mode Segmented Switch */}
        {currentFile && (
          <div className="flex items-center gap-1 bg-[#242822] p-1 rounded-xl border border-[#2E332B]">
            <button
              onClick={() => setViewMode("preview")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                viewMode === "preview"
                  ? "bg-[#1B1E19] text-[#F4F1EA] shadow-sm"
                  : "text-[#A8A69E] hover:text-[#F4F1EA]"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              Recoloured
            </button>
            <button
              onClick={() => setViewMode("side_by_side")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                viewMode === "side_by_side"
                  ? "bg-[#1B1E19] text-[#F4F1EA] shadow-sm"
                  : "text-[#A8A69E] hover:text-[#F4F1EA]"
              }`}
            >
              <Columns className="w-3.5 h-3.5" />
              Side-by-Side
            </button>
            <button
              onClick={() => setViewMode("split")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                viewMode === "split"
                  ? "bg-[#1B1E19] text-[#F4F1EA] shadow-sm"
                  : "text-[#A8A69E] hover:text-[#F4F1EA]"
              }`}
            >
              <SplitSquareVertical className="w-3.5 h-3.5" />
              Split Slider
            </button>
            <button
              onClick={() => setViewMode("mask")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                viewMode === "mask"
                  ? "bg-[#1B1E19] text-[#F4F1EA] shadow-sm"
                  : "text-[#A8A69E] hover:text-[#F4F1EA]"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              Mask & Refine
            </button>
          </div>
        )}
      </div>

      {/* Quality Gate Diagnostic Banner */}
      {qualityGate && (
        <div className={`p-4 rounded-xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs ${
          qualityGate.segmentation_confidence === "High"
            ? "bg-[#1B241C] border-[#2E3E2F] text-[#86EFAC]"
            : "bg-[#2A2318] border-[#4E391C] text-[#FDE047]"
        }`}>
          <div className="flex items-center gap-2">
            {qualityGate.segmentation_confidence === "High" ? (
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            )}
            <div>
              <span className="font-semibold">
                Mask Confidence: {qualityGate.segmentation_confidence}
              </span>
              <span className="text-[#A8A69E] ml-2">
                • Wall Coverage: {qualityGate.wall_coverage_percent}% • Edge Sharpness: {qualityGate.edge_sharpness_score}
              </span>
            </div>
          </div>
          {qualityGate.warnings && qualityGate.warnings.length > 0 && (
            <span className="text-[11px] text-[#A8A69E]">
              {qualityGate.warnings[0]}
            </span>
          )}
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/60 text-xs text-red-200">
          {errorMsg}
        </div>
      )}

      {/* Main Studio Canvas & Tuning Parameters */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Canvas Display (8 cols) */}
        <div className="lg:col-span-8 flex flex-col space-y-4">
          <div className="relative rounded-2xl bg-[#1B1E19] border border-[#2E332B] p-2 min-h-[460px] flex items-center justify-center overflow-hidden">
            {!currentFile ? (
              <div className="flex flex-col items-center justify-center p-12 text-center">
                <ImageIcon className="w-16 h-16 text-[#2E332B] mb-4" />
                <h3 className="text-base font-serif text-[#F4F1EA] mb-1">
                  No Room Image Loaded
                </h3>
                <p className="text-xs text-[#A8A69E] max-w-sm mb-6">
                  Upload an interior photo to preview architectural multi-surface recolouring.
                </p>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-5 py-2.5 rounded-full text-xs font-semibold text-[#121411] bg-[#F4F1EA] hover:bg-white transition-all cursor-pointer"
                >
                  Browse Files
                </button>
              </div>
            ) : (
              <div 
                ref={canvasRef}
                onClick={handleCanvasClick}
                className={`relative w-full h-[520px] rounded-xl overflow-hidden bg-black/40 flex items-center justify-center ${
                  viewMode === "mask" ? "cursor-crosshair" : ""
                }`}
              >
                {/* 1. Single Preview Mode */}
                {viewMode === "preview" && (
                  <img
                    src={recolouredImage || analysis?.preview_image}
                    alt="Recoloured Room Preview"
                    className="w-full h-full object-contain"
                  />
                )}

                {/* 2. Side-by-Side Mode */}
                {viewMode === "side_by_side" && (
                  <div className="grid grid-cols-2 w-full h-full gap-1 p-1">
                    <div className="relative w-full h-full overflow-hidden rounded-lg">
                      <img
                        src={analysis?.preview_image}
                        alt="Original Room"
                        className="w-full h-full object-cover"
                      />
                      <span className="absolute top-2 left-2 px-2 py-1 rounded bg-black/70 text-[10px] text-white">
                        Original
                      </span>
                    </div>
                    <div className="relative w-full h-full overflow-hidden rounded-lg">
                      <img
                        src={recolouredImage || analysis?.preview_image}
                        alt="Recoloured Room"
                        className="w-full h-full object-cover"
                      />
                      <span className="absolute top-2 left-2 px-2 py-1 rounded bg-[#B85C38]/90 text-[10px] text-white">
                        Recoloured ({surfaceColors[activeSurface]})
                      </span>
                    </div>
                  </div>
                )}

                {/* 3. Split Slider Mode */}
                {viewMode === "split" && (
                  <div className="relative w-full h-full select-none overflow-hidden">
                    <img
                      src={recolouredImage || analysis?.preview_image}
                      alt="Recoloured"
                      className="absolute inset-0 w-full h-full object-cover"
                    />
                    <div
                      className="absolute inset-0 overflow-hidden"
                      style={{ clipPath: `polygon(0 0, ${splitPos}% 0, ${splitPos}% 100%, 0 100%)` }}
                    >
                      <img
                        src={analysis?.preview_image}
                        alt="Original"
                        className="absolute inset-0 w-full h-full object-cover"
                      />
                    </div>
                    <div
                      className="absolute top-0 bottom-0 w-0.5 bg-white shadow-lg cursor-ew-resize"
                      style={{ left: `${splitPos}%` }}
                    >
                      <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-white text-black text-[10px] flex items-center justify-center font-bold shadow-md">
                        &harr;
                      </div>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={splitPos}
                      onChange={(e) => setSplitPos(Number(e.target.value))}
                      className="absolute inset-0 opacity-0 cursor-ew-resize w-full h-full"
                    />
                  </div>
                )}

                {/* 4. Mask Overlay & Interactive Tap Mode */}
                {viewMode === "mask" && (
                  <div className="relative w-full h-full flex items-center justify-center">
                    <img
                      src={maskOverlayImage || recolouredImage || analysis?.preview_image}
                      alt="Wall Mask Overlay"
                      className="w-full h-full object-contain pointer-events-none"
                    />
                    <div className="absolute top-3 right-3 bg-black/80 px-3 py-1.5 rounded-lg border border-white/10 text-[11px] text-[#F4F1EA]">
                      Tap image to {brushMode === "add" ? "ADD wall area" : "ERASE obstacle"}
                    </div>
                  </div>
                )}

                {isProcessing && (
                  <div className="absolute inset-0 bg-[#121411]/70 backdrop-blur-sm flex items-center justify-center z-20">
                    <div className="flex flex-col items-center gap-2">
                      <RefreshCw className="w-6 h-6 text-[#B85C38] animate-spin" />
                      <span className="text-xs text-[#F4F1EA]">
                        Applying lighting-compensated CIELAB transfer...
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Mask Correction Brush Toolbar (Active in Mask Mode) */}
          {viewMode === "mask" && (
            <div className="p-4 rounded-xl bg-[#1B1E19] border border-[#2E332B] flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <Paintbrush className="w-4 h-4 text-[#B85C38]" />
                <span className="text-xs font-semibold text-[#F4F1EA]">
                  Promptable Mask Correction:
                </span>
                <div className="flex rounded-lg overflow-hidden border border-[#2E332B]">
                  <button
                    onClick={() => setBrushMode("add")}
                    className={`px-3 py-1 text-xs font-medium cursor-pointer ${
                      brushMode === "add" ? "bg-[#B85C38] text-white" : "bg-[#242822] text-[#A8A69E]"
                    }`}
                  >
                    + Add Wall
                  </button>
                  <button
                    onClick={() => setBrushMode("remove")}
                    className={`px-3 py-1 text-xs font-medium cursor-pointer ${
                      brushMode === "remove" ? "bg-red-700 text-white" : "bg-[#242822] text-[#A8A69E]"
                    }`}
                  >
                    - Erase Obstacle
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-xs text-[#A8A69E]">Brush Size: {brushRadius}px</span>
                <input
                  type="range"
                  min="6"
                  max="40"
                  value={brushRadius}
                  onChange={(e) => setBrushRadius(Number(e.target.value))}
                  className="w-24 accent-[#B85C38]"
                />
                {manualCorrectionsCount > 0 && (
                  <span className="text-[10px] text-emerald-400">
                    ({manualCorrectionsCount} edits applied)
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Color Swatch Strip with actual area percentages */}
          {analysis && analysis.tones && analysis.tones.length > 0 && (
            <div className="p-4 rounded-xl bg-[#1B1E19] border border-[#2E332B]">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-[#F4F1EA]">
                  Detected Optical Palette ({analysis.tones.length} Tones)
                </span>
                <span className="text-[10px] text-[#A8A69E]">
                  Assign tone to active surface: <strong className="text-white capitalize">{activeSurface.replace('_', ' ')}</strong>
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {analysis.tones.map((tone, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSelectedColor(tone.hex)}
                    className="flex items-center gap-2.5 p-2 rounded-lg bg-[#242822] hover:bg-[#2E332B] border border-[#2E332B] transition-colors text-left cursor-pointer group"
                  >
                    <div
                      className="w-6 h-6 rounded-md shadow-inner shrink-0 group-hover:scale-105 transition-transform"
                      style={{ backgroundColor: tone.hex }}
                    />
                    <div className="overflow-hidden">
                      <span className="text-[11px] font-mono font-medium text-[#F4F1EA] block">
                        {tone.hex}
                      </span>
                      <span className="text-[9px] text-[#A8A69E] block truncate">
                        {tone.percentage}% {tone.name || "Shade"}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar Parameters: Multi-surface & Lighting Controls (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          {/* Surface Multi-recolour Tabs */}
          <div className="p-6 rounded-2xl bg-[#1B1E19] border border-[#2E332B] space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-[#B85C38]" />
                <h3 className="text-sm font-semibold text-[#F4F1EA]">
                  Architectural Surfaces
                </h3>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {(["wall", "ceiling", "trim", "accent_wall"] as const).map((surf) => {
                const isActive = activeSurface === surf;
                const surfLabel = surf === "wall" ? "Main Walls" : surf === "ceiling" ? "Ceiling" : surf === "trim" ? "Trim / Molding" : "Accent Wall";
                return (
                  <button
                    key={surf}
                    onClick={() => setActiveSurface(surf)}
                    className={`p-3 rounded-xl border text-left transition-colors cursor-pointer flex flex-col justify-between ${
                      isActive 
                        ? "bg-[#242822] border-[#B85C38] text-white" 
                        : "bg-[#1B1E19] border-[#2E332B] text-[#A8A69E] hover:border-neutral-700"
                    }`}
                  >
                    <span className="text-xs font-medium block">{surfLabel}</span>
                    <div className="flex items-center gap-2 mt-2">
                      <div 
                        className="w-4 h-4 rounded-full border border-white/20 shadow-sm"
                        style={{ backgroundColor: surfaceColors[surf] }}
                      />
                      <span className="text-[10px] font-mono text-[#F4F1EA]">
                        {surfaceColors[surf]}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Custom Hex Input for Active Surface */}
            <div className="space-y-2 pt-2 border-t border-[#2E332B]">
              <label className="text-xs text-[#A8A69E] flex justify-between">
                <span>Selected Shade for {activeSurface.replace('_', ' ')}</span>
                <span className="font-mono text-white">{surfaceColors[activeSurface]}</span>
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={surfaceColors[activeSurface]}
                  onChange={(e) => setSelectedColor(e.target.value)}
                  className="w-9 h-9 rounded-lg bg-transparent cursor-pointer border border-[#2E332B]"
                />
                <input
                  type="text"
                  value={surfaceColors[activeSurface]}
                  onChange={(e) => setSelectedColor(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-lg bg-[#242822] border border-[#2E332B] text-xs font-mono text-white focus:outline-none focus:border-[#B85C38]"
                />
              </div>
            </div>
          </div>

          {/* Shading & Lighting Awareness */}
          <div className="p-6 rounded-2xl bg-[#1B1E19] border border-[#2E332B] space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <SunMedium className="w-4 h-4 text-[#B85C38]" />
                <h3 className="text-sm font-semibold text-[#F4F1EA]">
                  Shading & Lighting Engine
                </h3>
              </div>
            </div>

            {/* Lighting Compensation Toggle */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-[#242822] border border-[#2E332B]">
              <div>
                <span className="text-xs font-medium text-white block">
                  Lighting Cast Compensation
                </span>
                <span className="text-[10px] text-[#A8A69E]">
                  Balances 2700K–6800K ambient tint
                </span>
              </div>
              <input
                type="checkbox"
                checked={compensateLighting}
                onChange={(e) => setCompensateLighting(e.target.checked)}
                className="w-4 h-4 accent-[#B85C38] cursor-pointer"
              />
            </div>

            {/* Paint Opacity / Intensity Slider */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-[#A8A69E]">Paint Intensity</span>
                <span className="font-mono text-[#F4F1EA]">{Math.round(intensity * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.2"
                max="1.0"
                step="0.05"
                value={intensity}
                onChange={(e) => setIntensity(Number(e.target.value))}
                className="w-full accent-[#B85C38]"
              />
              <span className="text-[10px] text-[#A8A69E] block">
                Preserves original wall texture, highlights, and shadow gradients.
              </span>
            </div>

            {/* Segmentation Sensitivity */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-[#A8A69E]">Boundary Sensitivity</span>
                <span className="font-mono text-[#F4F1EA]">{Math.round(sensitivity * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={sensitivity}
                onChange={(e) => setSensitivity(Number(e.target.value))}
                className="w-full accent-[#B85C38]"
              />
            </div>

            {/* Export High-Res Button */}
            <button
              onClick={handleDownload}
              disabled={!currentFile || !recolouredImage}
              className="w-full py-2.5 rounded-xl text-xs font-semibold text-[#121411] bg-[#F4F1EA] hover:bg-white disabled:opacity-40 transition-all flex items-center justify-center gap-2 cursor-pointer shadow-sm"
            >
              <Download className="w-4 h-4 text-[#B85C38]" />
              Export Architectural Render (Full Res)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
