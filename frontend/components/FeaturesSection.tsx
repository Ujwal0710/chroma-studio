"use client";

import React from "react";
import { Cpu, ShieldCheck, PieChart, Eye, Sparkles, Sliders } from "lucide-react";

export function FeaturesSection() {
  const features = [
    {
      icon: Cpu,
      title: "Perceptual CIELAB Science",
      description:
        "Deterministic color physics calculated via Delta E 2000. No AI hallucination or inaccurate paint swatches.",
      badge: "Scientific Accuracy",
    },
    {
      icon: Eye,
      title: "Zero-Bleed Edge Protection",
      description:
        "Photometric edge detection separates architectural walls from mouldings, ceilings, windows, and furniture.",
      badge: "Optical Masking",
    },
    {
      icon: PieChart,
      title: "60-30-10 Harmonic Balance",
      description:
        "Mathematical ratio balancing ensures 60% dominant wall plane, 30% secondary surface, and 10% focal accents.",
      badge: "Architectural Rule",
    },
    {
      icon: ShieldCheck,
      title: "Offline Privacy Shield",
      description:
        "Your architectural blueprints and room photos are processed on-premise without cloud data leaks or retention.",
      badge: "100% Confidential",
    },
  ];

  return (
    <section className="py-20 border-t border-[#2E332B] bg-[#121411]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12">
          <div>
            <div className="text-xs uppercase tracking-widest text-[#B85C38] font-bold mb-2">
              Why Choosing Us
            </div>
            <h2 className="text-3xl sm:text-4xl font-serif text-[#F4F1EA]">
              Built for discerning architects &amp; designers.
            </h2>
          </div>
          <p className="text-sm text-[#A8A69E] max-w-md mt-4 md:mt-0">
            Every swatch, shadow preservation algorithm, and daylight simulation is grounded in physical colour science.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feat, idx) => {
            const Icon = feat.icon;
            return (
              <div
                key={idx}
                className="group relative p-6 rounded-2xl bg-[#1B1E19] border border-[#2E332B] hover:border-[#B85C38]/40 transition-all duration-300 hover:shadow-xl hover:shadow-[#B85C38]/5 flex flex-col justify-between"
              >
                <div>
                  <div className="w-12 h-12 rounded-xl bg-[#242822] border border-[#2E332B] flex items-center justify-center text-[#B85C38] mb-5 group-hover:scale-110 transition-transform">
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className="text-[10px] uppercase tracking-wider font-semibold text-[#A8A69E] mb-2 block">
                    {feat.badge}
                  </span>
                  <h3 className="text-lg font-medium text-[#F4F1EA] mb-3">
                    {feat.title}
                  </h3>
                  <p className="text-xs text-[#A8A69E] leading-relaxed">
                    {feat.description}
                  </p>
                </div>

                <div className="mt-6 pt-4 border-t border-[#2E332B]/60 flex items-center text-[11px] text-[#B85C38] font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                  Inspect Algorithm &rarr;
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
