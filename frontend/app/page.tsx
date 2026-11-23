"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/Navbar";
import { LandingHero } from "@/components/LandingHero";
import { FeaturesSection } from "@/components/FeaturesSection";
import { StudioView } from "@/components/StudioView";
import { PaletteLabView } from "@/components/PaletteLabView";
import { DaylightMaterialsView } from "@/components/DaylightMaterialsView";
import { EstimatorView } from "@/components/EstimatorView";
import { TimelineView } from "@/components/TimelineView";
import { Room3DView } from "@/components/Room3DView";
import { LiveScanView } from "@/components/LiveScanView";
import { PricingSection } from "@/components/PricingSection";
import { AccountModal } from "@/components/AccountModal";
import { Footer } from "@/components/Footer";
import { BackendStatus } from "@/components/BackendStatus";
import { api } from "@/lib/api";
import { RoomAnalysisResponse, PaletteConcept } from "@/lib/types";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<string>("studio");
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<RoomAnalysisResponse | null>(null);
  const [selectedColor, setSelectedColor] = useState<string>("#B85C38");
  const [activePalette, setActivePalette] = useState<PaletteConcept | null>(null);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [isAuthOpen, setIsAuthOpen] = useState<boolean>(false);
  const [isLoadingSample, setIsLoadingSample] = useState<boolean>(false);

  // Check auth status on mount
  useEffect(() => {
    async function checkAuth() {
      try {
        const me = await api.getMe();
        if (me.authenticated && me.user) {
          setCurrentUser(me.user);
        }
      } catch (err) {
        // Guest user mode
      }
    }
    checkAuth();
  }, []);

  // Auto-generate active palette when room analysis exists
  useEffect(() => {
    if (!analysis) {
      setActivePalette(null);
      return;
    }
    let cancelled = false;
    async function initPalette() {
      try {
        const palettes = await api.generatePalettes({
          extracted: analysis?.dominant_tones,
          dominant_tones: analysis?.dominant_tones,
          room_analysis: analysis?.room_analysis,
          primary_hex: selectedColor || "#B85C38",
        });
        if (!cancelled && palettes && palettes.length > 0) {
          setActivePalette(palettes[0]);
        }
      } catch (err) {
        console.error("Auto palette generation failed:", err);
      }
    }
    initPalette();
    return () => {
      cancelled = true;
    };
  }, [analysis, selectedColor]);

  // Helper to load sample room
  const handleLoadSample = async () => {
    setIsLoadingSample(true);
    try {
      const sample = await api.getSampleRoom();
      const dataUrl = (sample as any).image_data_url || (sample as any).image_data;
      if (!dataUrl) throw new Error("No image data returned from sample room endpoint");

      // Convert base64 data URL to File object
      const res = await fetch(dataUrl);
      const blob = await res.blob();
      const file = new File([blob], sample.filename || "roomie_default_room.jpg", { type: "image/jpeg" });
      setCurrentFile(file);

      // Analyze the file
      const analysisRes = await api.analyseRoom(file);
      setAnalysis(analysisRes);
      if (analysisRes.tones && analysisRes.tones.length > 0) {
        setSelectedColor(analysisRes.tones[0].hex);
      }

      // Smooth scroll to atelier workspace
      const el = document.getElementById("atelier-workspace");
      if (el) el.scrollIntoView({ behavior: "smooth" });
    } catch (err) {
      console.error("Failed to load sample room:", err);
    } finally {
      setIsLoadingSample(false);
    }
  };

  const handleTriggerUpload = () => {
    const el = document.getElementById("atelier-workspace");
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-[#121411] text-[#F4F1EA] flex flex-col font-sans selection:bg-[#B85C38] selection:text-white">
      {/* Sticky Architectural Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenAuth={() => setIsAuthOpen(true)}
        currentUser={currentUser}
      />

      {/* Main Content Area */}
      <main className="flex-1">
        {/* Figma Reference Hero */}
        <LandingHero
          onLoadSample={handleLoadSample}
          onTriggerUpload={handleTriggerUpload}
          isLoading={isLoadingSample}
        />

        {/* Why Choosing Us (Features Grid) */}
        <FeaturesSection />

        {/* Interactive Atelier Workspace Container */}
        <section className="py-16 border-t border-[#2E332B] bg-[#121411]" id="atelier-workspace">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {/* View Switcher Bar */}
            <div className="flex items-center justify-between pb-8 mb-8 border-b border-[#2E332B]">
              <div>
                <span className="text-xs uppercase tracking-widest text-[#B85C38] font-bold block mb-1">
                  Active Atelier View
                </span>
                <h2 className="text-2xl sm:text-3xl font-serif text-[#F4F1EA]">
                  {activeTab === "studio" && "Studio & Optical Recolour"}
                  {activeTab === "live-scan" && "Live Camera Scanner & Temporal Lens"}
                  {activeTab === "palette-lab" && "Palette Lab & Harmonic Balance"}
                  {activeTab === "materials" && "Daylight & Substrate Scoring"}
                  {activeTab === "3d-room" && "3D Spatial Room Model & PBR Illumination"}
                  {activeTab === "estimator" && "Precision Paint & Can Packaging"}
                  {activeTab === "timeline" && "Milestone Timeline & Rollback"}
                  {activeTab === "pricing" && "Plans & Atelier Subscriptions"}
                </h2>
              </div>
            </div>

            {/* Sub-Views */}
            {activeTab === "live-scan" && (
              <LiveScanView
                onCaptureRoom={(file) => {
                  setCurrentFile(file);
                  api.analyseRoom(file).then((res) => {
                    setAnalysis(res);
                    if (res.tones && res.tones.length > 0) {
                      setSelectedColor(res.tones[0].hex);
                    }
                  });
                }}
                onNavigateToStudio={() => {
                  setActiveTab("studio");
                  const el = document.getElementById("atelier-workspace");
                  if (el) el.scrollIntoView({ behavior: "smooth" });
                }}
              />
            )}

            {activeTab === "studio" && (
              <StudioView
                currentFile={currentFile}
                setCurrentFile={setCurrentFile}
                analysis={analysis}
                setAnalysis={setAnalysis}
                selectedColor={selectedColor}
                setSelectedColor={setSelectedColor}
              />
            )}

            {activeTab === "palette-lab" && (
              <PaletteLabView
                analysis={analysis}
                primaryHex={selectedColor}
                onSelectTone={(hex) => {
                  setSelectedColor(hex);
                  setActiveTab("studio");
                }}
                onNavigateToUpload={() => {
                  setActiveTab("studio");
                  const el = document.getElementById("atelier-workspace");
                  if (el) el.scrollIntoView({ behavior: "smooth" });
                }}
              />
            )}

            {activeTab === "materials" && (
              <DaylightMaterialsView
                currentFile={currentFile}
                primaryHex={selectedColor}
                palette={activePalette}
                hasAnalysis={!!analysis}
              />
            )}

            {activeTab === "3d-room" && (
              <Room3DView
                analysis={analysis}
                primaryColor={selectedColor}
                palette={null}
                onSelectTone={(hex) => {
                  setSelectedColor(hex);
                  setActiveTab("studio");
                }}
              />
            )}

            {activeTab === "estimator" && <EstimatorView />}

            {activeTab === "timeline" && (
              <TimelineView
                currentPaletteData={{
                  selected_tone: selectedColor,
                  analysis_metadata: analysis ? { filename: analysis.filename } : null,
                }}
                onRollbackToPalette={(data) => {
                  if (data && data.selected_tone) {
                    setSelectedColor(data.selected_tone);
                    setActiveTab("studio");
                  }
                }}
              />
            )}

            {activeTab === "pricing" && <PricingSection />}
          </div>
        </section>

        {/* Pricing Section (Accessible on landing as well) */}
        {activeTab !== "pricing" && <PricingSection />}
      </main>

      {/* Footer */}
      <Footer />

      {/* Account / Auth / GDPR Modal */}
      <AccountModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        currentUser={currentUser}
        setCurrentUser={setCurrentUser}
      />

      {/* Backend health banner */}
      <BackendStatus />
    </div>
  );
}
