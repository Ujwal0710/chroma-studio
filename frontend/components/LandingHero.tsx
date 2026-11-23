"use client";

import React from "react";
import { Sparkles, ArrowRight, Upload, Play, Shield, CheckCircle2 } from "lucide-react";

interface LandingHeroProps {
  onLoadSample: () => void;
  onTriggerUpload: () => void;
  isLoading: boolean;
}

export function LandingHero({ onLoadSample, onTriggerUpload, isLoading }: LandingHeroProps) {
  return (
    <section className="relative pt-12 pb-20 overflow-hidden">
      {/* Background radial gradient glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-gradient-to-b from-[#B85C38]/15 via-[#B85C38]/5 to-transparent blur-3xl pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Column: Headlines & CTA (7 cols) */}
          <div className="lg:col-span-7 flex flex-col items-start space-y-6">
            {/* Pill Tag */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#1B1E19] border border-[#2E332B] text-xs font-medium text-[#F4F1EA]">
              <span className="w-2 h-2 rounded-full bg-[#B85C38] animate-ping" />
              <span>Version 2.0 • Perceptual CIELAB Engine Active</span>
            </div>

            {/* Editorial Headline */}
            <h1 className="text-4xl sm:text-6xl font-serif tracking-tight text-[#F4F1EA] leading-[1.12]">
              Make a room comfortable &amp;{" "}
              <span className="italic font-normal text-[#B85C38] font-serif">
                elegant.
              </span>
            </h1>

            {/* Subheading */}
            <p className="text-base sm:text-lg text-[#A8A69E] max-w-2xl leading-relaxed">
              Transform interior architecture with zero-bleed optical wall segmentation,
              mathematically balanced 60-30-10 palettes, and photorealistic luminance-preserving paint simulation.
            </p>

            {/* Action buttons */}
            <div className="flex flex-wrap items-center gap-4 pt-2 w-full sm:w-auto">
              <button
                onClick={onLoadSample}
                disabled={isLoading}
                className="flex items-center justify-center gap-2 px-6 py-3.5 rounded-full text-sm font-medium text-[#121411] bg-[#F4F1EA] hover:bg-[#FFFFFF] transition-all shadow-md hover:scale-[1.02] cursor-pointer"
              >
                <Play className="w-4 h-4 fill-current text-[#121411]" />
                {isLoading ? "Analyzing Sample..." : "Try Sample Room"}
              </button>

              <button
                onClick={onTriggerUpload}
                className="flex items-center justify-center gap-2 px-6 py-3.5 rounded-full text-sm font-medium text-[#F4F1EA] bg-[#1B1E19] hover:bg-[#242822] border border-[#2E332B] hover:border-[#B85C38]/50 transition-all hover:scale-[1.02] cursor-pointer"
              >
                <Upload className="w-4 h-4 text-[#B85C38]" />
                Upload Room Photo
              </button>
            </div>

            {/* Value checklist */}
            <div className="flex flex-wrap items-center gap-6 pt-4 text-xs text-[#A8A69E]">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#4E8752]" />
                <span>Zero-Bleed Edge Protection</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#4E8752]" />
                <span>$\Delta E_{2000}$ Contrast Science</span>
              </div>
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-[#B85C38]" />
                <span>100% Private Offline Processing</span>
              </div>
            </div>
          </div>

          {/* Right Column: Visual Architecture Showcase (5 cols) */}
          <div className="lg:col-span-5 relative">
            <div className="relative rounded-2xl p-2 bg-[#1B1E19]/80 border border-[#2E332B] shadow-2xl backdrop-blur-sm">
              <div className="relative rounded-xl overflow-hidden aspect-[4/3] bg-[#242822] flex items-center justify-center group">
                <img
                  src="https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1200&q=80"
                  alt="Modern Architectural Interior"
                  className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                />

                <div className="absolute inset-0 bg-gradient-to-t from-[#121411] via-transparent to-transparent opacity-80" />

                {/* Floating Overlay Badge */}
                <div className="absolute bottom-4 left-4 right-4 p-4 rounded-xl bg-[#1B1E19]/90 border border-[#2E332B] backdrop-blur-md flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-3.5 h-3.5 rounded-full bg-[#B85C38] shadow-sm shadow-[#B85C38]" />
                    <div>
                      <div className="text-xs font-semibold text-[#F4F1EA]">
                        Warm Terracotta &amp; Sand
                      </div>
                      <div className="text-[10px] text-[#A8A69E]">
                        Perceptual Luminance Match (0.85 Intensity)
                      </div>
                    </div>
                  </div>
                  <span className="text-xs font-mono text-[#B85C38] font-bold">
                    99.4%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Strip */}
        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6 pt-10 border-t border-[#2E332B]/80">
          <div className="flex flex-col">
            <span className="text-3xl font-serif text-[#F4F1EA] font-semibold">
              2,500+
            </span>
            <span className="text-xs text-[#A8A69E] mt-1">
              Spaces Reimagined
            </span>
          </div>

          <div className="flex flex-col">
            <span className="text-3xl font-serif text-[#B85C38] font-semibold">
              ΔE &lt; 1.5
            </span>
            <span className="text-xs text-[#A8A69E] mt-1">
              Perceptual Color Precision
            </span>
          </div>

          <div className="flex flex-col">
            <span className="text-3xl font-serif text-[#F4F1EA] font-semibold">
              4 Concepts
            </span>
            <span className="text-xs text-[#A8A69E] mt-1">
              Instant Harmonic Variations
            </span>
          </div>

          <div className="flex flex-col">
            <span className="text-3xl font-serif text-[#4E8752] font-semibold">
              100%
            </span>
            <span className="text-xs text-[#A8A69E] mt-1">
              Zero-Bleed Edge Shield
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
