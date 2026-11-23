"use client";

import React, { useState, useEffect } from "react";
import { Calculator, Package, Info, Check, IndianRupee } from "lucide-react";
import { api } from "@/lib/api";
import { PaintEstimateResult } from "@/lib/types";

export function EstimatorView() {
  const [length, setLength] = useState<number>(5.0);
  const [width, setWidth] = useState<number>(4.0);
  const [height, setHeight] = useState<number>(2.8);
  const [doors, setDoors] = useState<number>(1);
  const [windows, setWindows] = useState<number>(2);
  const [coats, setCoats] = useState<number>(2);
  const [ratePerLiter, setRatePerLiter] = useState<number>(450);
  const [result, setResult] = useState<PaintEstimateResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    async function calculate() {
      setLoading(true);
      try {
        const res = await api.calculateEstimate({
          room_length_meters: length,
          room_width_meters: width,
          wall_height_meters: height,
          num_doors: doors,
          num_windows: windows,
          coats: coats,
          cost_per_liter_inr: ratePerLiter,
        });
        setResult(res);
      } catch (err) {
        console.error("Estimation failed:", err);
      } finally {
        setLoading(false);
      }
    }

    const timer = setTimeout(calculate, 200);
    return () => clearTimeout(timer);
  }, [length, width, height, doors, windows, coats, ratePerLiter]);

  return (
    <div className="space-y-8">
      {/* Header bar */}
      <div className="p-6 rounded-2xl bg-[#1B1E19] border border-[#2E332B]">
        <span className="text-xs uppercase tracking-widest text-[#B85C38] font-bold block mb-1">
          Architectural Paint &amp; Bill of Materials
        </span>
        <h2 className="text-2xl font-serif text-[#F4F1EA]">
          Precision Paint Volume &amp; Packaging Estimator
        </h2>
        <p className="text-xs text-[#A8A69E] mt-1 max-w-xl">
          Calculates gross surface area, subtracts standard door/window deductions, and optimizes can container allocation (1L, 4L, 10L, 20L).
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Input Parameters (5 cols) */}
        <div className="lg:col-span-5 p-6 rounded-2xl bg-[#1B1E19] border border-[#2E332B] space-y-5">
          <h3 className="text-sm font-semibold text-[#F4F1EA] uppercase tracking-wider">
            Room Geometry &amp; Specifications
          </h3>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs text-[#A8A69E]">Length (meters)</label>
              <input
                type="number"
                step="0.1"
                min="1"
                value={length}
                onChange={(e) => setLength(parseFloat(e.target.value) || 1)}
                className="w-full px-3 py-2 rounded-lg bg-[#242822] border border-[#2E332B] text-xs text-[#F4F1EA] font-mono focus:border-[#B85C38] focus:outline-none"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-[#A8A69E]">Width (meters)</label>
              <input
                type="number"
                step="0.1"
                min="1"
                value={width}
                onChange={(e) => setWidth(parseFloat(e.target.value) || 1)}
                className="w-full px-3 py-2 rounded-lg bg-[#242822] border border-[#2E332B] text-xs text-[#F4F1EA] font-mono focus:border-[#B85C38] focus:outline-none"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs text-[#A8A69E]">Ceiling Height (meters)</label>
            <input
              type="number"
              step="0.1"
              min="2"
              value={height}
              onChange={(e) => setHeight(parseFloat(e.target.value) || 2.4)}
              className="w-full px-3 py-2 rounded-lg bg-[#242822] border border-[#2E332B] text-xs text-[#F4F1EA] font-mono focus:border-[#B85C38] focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs text-[#A8A69E]">Standard Doors (1.9m²)</label>
              <input
                type="number"
                min="0"
                value={doors}
                onChange={(e) => setDoors(parseInt(e.target.value) || 0)}
                className="w-full px-3 py-2 rounded-lg bg-[#242822] border border-[#2E332B] text-xs text-[#F4F1EA] font-mono focus:border-[#B85C38] focus:outline-none"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-[#A8A69E]">Windows (1.5m²)</label>
              <input
                type="number"
                min="0"
                value={windows}
                onChange={(e) => setWindows(parseInt(e.target.value) || 0)}
                className="w-full px-3 py-2 rounded-lg bg-[#242822] border border-[#2E332B] text-xs text-[#F4F1EA] font-mono focus:border-[#B85C38] focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs text-[#A8A69E]">Paint Coats</label>
              <select
                value={coats}
                onChange={(e) => setCoats(parseInt(e.target.value) || 2)}
                className="w-full px-3 py-2 rounded-lg bg-[#242822] border border-[#2E332B] text-xs text-[#F4F1EA] focus:border-[#B85C38] focus:outline-none"
              >
                <option value={1}>1 Coat (Touch-up)</option>
                <option value={2}>2 Coats (Standard)</option>
                <option value={3}>3 Coats (Deep Pigment)</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-xs text-[#A8A69E]">Paint Rate (₹ / Litre)</label>
              <input
                type="number"
                min="100"
                step="50"
                value={ratePerLiter}
                onChange={(e) => setRatePerLiter(parseFloat(e.target.value) || 450)}
                className="w-full px-3 py-2 rounded-lg bg-[#242822] border border-[#2E332B] text-xs text-[#F4F1EA] font-mono focus:border-[#B85C38] focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* Calculated Results (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {result ? (
            <>
              {/* Primary Total Box */}
              <div className="p-6 rounded-2xl bg-gradient-to-br from-[#1B1E19] to-[#242822] border border-[#2E332B] relative overflow-hidden">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <span className="text-xs text-[#A8A69E] uppercase tracking-wider block">
                      Estimated Material Cost
                    </span>
                    <div className="text-3xl sm:text-4xl font-serif text-[#F4F1EA] font-bold mt-1 flex items-center">
                      <span>₹{result.estimated_cost_inr.toLocaleString("en-IN")}</span>
                    </div>
                  </div>

                  <div className="text-right sm:border-l sm:border-[#2E332B] sm:pl-6">
                    <span className="text-xs text-[#A8A69E] uppercase tracking-wider block">
                      Total Paint Required
                    </span>
                    <div className="text-2xl font-mono text-[#B85C38] font-bold mt-1">
                      {result.paint_liters_required} Litres
                    </div>
                  </div>
                </div>

                {/* Sub-metrics */}
                <div className="mt-6 pt-6 border-t border-[#2E332B] grid grid-cols-3 gap-4 text-xs">
                  <div>
                    <span className="text-[#A8A69E] block">Gross Area</span>
                    <span className="font-mono text-[#F4F1EA] font-medium">
                      {result.gross_wall_area_sqm} m²
                    </span>
                  </div>
                  <div>
                    <span className="text-[#A8A69E] block">Deductions</span>
                    <span className="font-mono text-[#F4F1EA] font-medium">
                      -{result.deductions_sqm} m²
                    </span>
                  </div>
                  <div>
                    <span className="text-[#A8A69E] block">Net Wall Area</span>
                    <span className="font-mono text-[#4E8752] font-semibold">
                      {result.net_wall_area_sqm} m²
                    </span>
                  </div>
                </div>
              </div>

              {/* Recommended Can Containers Breakdown */}
              <div className="p-6 rounded-2xl bg-[#1B1E19] border border-[#2E332B] space-y-4">
                <div className="flex items-center gap-2">
                  <Package className="w-5 h-5 text-[#B85C38]" />
                  <h4 className="text-sm font-semibold text-[#F4F1EA] uppercase tracking-wider">
                    Optimal Packaging Allocation
                  </h4>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  {Object.entries(result.recommended_cans_breakdown).map(([canType, count]) => (
                    <div
                      key={canType}
                      className="p-4 rounded-xl bg-[#242822] border border-[#2E332B] text-center"
                    >
                      <div className="text-2xl font-serif text-[#F4F1EA] font-semibold">
                        {count}
                      </div>
                      <div className="text-[11px] text-[#A8A69E] mt-1">
                        {canType}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Architectural Disclaimer */}
              <div className="p-4 rounded-xl bg-[#242822]/60 border border-[#2E332B] flex items-start gap-3">
                <Info className="w-4 h-4 text-[#B85C38] shrink-0 mt-0.5" />
                <p className="text-[11px] text-[#A8A69E] leading-relaxed">
                  {result.estimator_disclaimer}
                </p>
              </div>
            </>
          ) : (
            <div className="p-12 text-center text-xs text-[#A8A69E]">
              Calculating paint volume...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
