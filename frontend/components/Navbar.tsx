"use client";

import React from "react";
import { Sparkles, Layers, Sliders, Box, Clock, User, ShieldCheck, SunMedium } from "lucide-react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onOpenAuth: () => void;
  currentUser: any;
}

export function Navbar({ activeTab, setActiveTab, onOpenAuth, currentUser }: NavbarProps) {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-[#2E332B] bg-[#121411]/85 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand Logo */}
        <div 
          onClick={() => setActiveTab("studio")}
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#B85C38] to-[#6E2E18] flex items-center justify-center shadow-lg shadow-[#B85C38]/20 group-hover:scale-105 transition-transform duration-200">
            <Sparkles className="w-5 h-5 text-[#F4F1EA]" />
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-lg tracking-wider text-[#F4F1EA] uppercase">
              Chroma Studio <span className="text-[#B85C38] font-bold">AI</span>
            </span>
            <span className="text-[10px] uppercase tracking-widest text-[#A8A69E]">
              Architectural Colour Intelligence
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1 bg-[#1B1E19]/90 border border-[#2E332B] px-3 py-1.5 rounded-full shadow-inner">
          <button
            onClick={() => setActiveTab("studio")}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium transition-all ${
              activeTab === "studio"
                ? "bg-[#242822] text-[#F4F1EA] shadow-sm border border-[#2E332B]"
                : "text-[#A8A69E] hover:text-[#F4F1EA] hover:bg-[#242822]/40"
            }`}
          >
            <Sliders className="w-3.5 h-3.5 text-[#B85C38]" />
            Studio
          </button>

          <button
            onClick={() => setActiveTab("live-scan")}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium transition-all ${
              activeTab === "live-scan"
                ? "bg-[#242822] text-[#F4F1EA] shadow-sm border border-[#2E332B]"
                : "text-[#A8A69E] hover:text-[#F4F1EA] hover:bg-[#242822]/40"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            Live Scan
          </button>

          <button
            onClick={() => setActiveTab("palette-lab")}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium transition-all ${
              activeTab === "palette-lab"
                ? "bg-[#242822] text-[#F4F1EA] shadow-sm border border-[#2E332B]"
                : "text-[#A8A69E] hover:text-[#F4F1EA] hover:bg-[#242822]/40"
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-[#B85C38]" />
            Palette Lab
          </button>

          <button
            onClick={() => setActiveTab("materials")}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium transition-all ${
              activeTab === "materials"
                ? "bg-[#242822] text-[#F4F1EA] shadow-sm border border-[#2E332B]"
                : "text-[#A8A69E] hover:text-[#F4F1EA] hover:bg-[#242822]/40"
            }`}
          >
            <SunMedium className="w-3.5 h-3.5 text-[#B85C38]" />
            Daylight & Materials
          </button>

          <button
            onClick={() => setActiveTab("3d-room")}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium transition-all ${
              activeTab === "3d-room"
                ? "bg-[#242822] text-[#F4F1EA] shadow-sm border border-[#2E332B]"
                : "text-[#A8A69E] hover:text-[#F4F1EA] hover:bg-[#242822]/40"
            }`}
          >
            <Box className="w-3.5 h-3.5 text-[#B85C38]" />
            3D Spatial Room
          </button>

          <button
            onClick={() => setActiveTab("estimator")}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium transition-all ${
              activeTab === "estimator"
                ? "bg-[#242822] text-[#F4F1EA] shadow-sm border border-[#2E332B]"
                : "text-[#A8A69E] hover:text-[#F4F1EA] hover:bg-[#242822]/40"
            }`}
          >
            <Box className="w-3.5 h-3.5 text-[#B85C38]" />
            Estimator
          </button>

          <button
            onClick={() => setActiveTab("timeline")}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium transition-all ${
              activeTab === "timeline"
                ? "bg-[#242822] text-[#F4F1EA] shadow-sm border border-[#2E332B]"
                : "text-[#A8A69E] hover:text-[#F4F1EA] hover:bg-[#242822]/40"
            }`}
          >
            <Clock className="w-3.5 h-3.5 text-[#B85C38]" />
            Timeline
          </button>

          <button
            onClick={() => setActiveTab("pricing")}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium transition-all ${
              activeTab === "pricing"
                ? "bg-[#242822] text-[#F4F1EA] shadow-sm border border-[#2E332B]"
                : "text-[#A8A69E] hover:text-[#F4F1EA] hover:bg-[#242822]/40"
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5 text-[#B85C38]" />
            Pricing
          </button>
        </nav>

        {/* Right Action buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenAuth}
            className="flex items-center gap-2 px-3 py-2 text-xs font-medium text-[#A8A69E] hover:text-[#F4F1EA] transition-colors border border-transparent hover:border-[#2E332B] rounded-lg"
          >
            <User className="w-4 h-4 text-[#B85C38]" />
            <span className="hidden sm:inline">
              {currentUser ? currentUser.full_name.split(" ")[0] : "Account"}
            </span>
          </button>

          <button
            onClick={() => {
              setActiveTab("studio");
              const el = document.getElementById("atelier-workspace");
              if (el) el.scrollIntoView({ behavior: "smooth" });
            }}
            className="relative group px-5 py-2.5 rounded-full text-xs font-semibold uppercase tracking-wider text-[#F4F1EA] bg-gradient-to-r from-[#B85C38] to-[#924626] hover:from-[#D47149] hover:to-[#B85C38] transition-all duration-300 shadow-md shadow-[#B85C38]/20 hover:shadow-lg hover:shadow-[#B85C38]/40"
          >
            <span className="relative z-10 flex items-center gap-1.5">
              Launch Atelier
              <Sparkles className="w-3.5 h-3.5 animate-pulse" />
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}
