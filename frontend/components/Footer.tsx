"use client";

import React from "react";
import { Sparkles, ShieldCheck, Heart } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-[#2E332B] bg-[#121411] text-[#A8A69E] py-14">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
          {/* Brand Col */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-[#B85C38] flex items-center justify-center text-white">
                <Sparkles className="w-4 h-4" />
              </div>
              <span className="font-semibold text-base text-[#F4F1EA] tracking-wider uppercase">
                Chroma Studio <span className="text-[#B85C38]">AI</span>
              </span>
            </div>
            <p className="text-xs leading-relaxed max-w-xs">
              Scientific architectural color intelligence, zero-bleed optical segmentation, and photorealistic paint simulation.
            </p>
          </div>

          {/* Capabilities */}
          <div className="space-y-3">
            <h4 className="text-xs uppercase font-semibold text-[#F4F1EA] tracking-wider">
              Computer Vision
            </h4>
            <ul className="space-y-2 text-xs">
              <li>Perceptual CIELAB Transfer</li>
              <li>Delta E 2000 Distance</li>
              <li>Edge-Feathered Masking</li>
              <li>Radiometric Kelvin Shifts</li>
            </ul>
          </div>

          {/* Design Engine */}
          <div className="space-y-3">
            <h4 className="text-xs uppercase font-semibold text-[#F4F1EA] tracking-wider">
              Architecture &amp; Rules
            </h4>
            <ul className="space-y-2 text-xs">
              <li>60-30-10 Harmonic Ratios</li>
              <li>9-Material Affinity Matrix</li>
              <li>Transparent Chroma DNA</li>
              <li>Packaging Volume Optimizer</li>
            </ul>
          </div>

          {/* Privacy & Governance */}
          <div className="space-y-3">
            <h4 className="text-xs uppercase font-semibold text-[#F4F1EA] tracking-wider">
              Security &amp; Privacy
            </h4>
            <ul className="space-y-2 text-xs">
              <li>100% On-Premise Execution</li>
              <li>Zero Cloud Image Logging</li>
              <li>GDPR Export &amp; Erasure</li>
              <li>PBKDF2 SHA-256 Auth</li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-[#2E332B] flex flex-col sm:flex-row items-center justify-between text-xs text-[#A8A69E]">
          <div>
            &copy; 2026 CHROMA STUDIO AI. Built for Architectural Excellence.
          </div>
          <div className="flex items-center gap-1 mt-4 sm:mt-0">
            <span>Powered by FastAPI &amp; Next.js</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
