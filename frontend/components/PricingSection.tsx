"use client";

import React, { useState } from "react";
import { Check, Sparkles, Shield, CreditCard, X } from "lucide-react";
import { api } from "@/lib/api";

export function PricingSection() {
  const [billingCycle, setBillingCycle] = useState<"monthly" | "annual">("monthly");
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [checkoutStatus, setCheckoutStatus] = useState<string | null>(null);

  const plans = [
    {
      id: "free",
      name: "Free Atelier",
      priceMonthly: 0,
      priceAnnual: 0,
      description: "For independent homeowners exploring interior concepts.",
      features: [
        "Up to 5 room analyses per month",
        "10 zero-bleed wall recolours",
        "Core 60-30-10 palette generator",
        "Daylight 5500K simulation",
        "Standard paint volume estimator",
        "Watermarked PNG exports",
      ],
      buttonText: "Current Plan",
      popular: false,
    },
    {
      id: "plus",
      name: "Studio Plus",
      priceMonthly: 799,
      priceAnnual: 7990,
      description: "For professional interior designers and boutique studios.",
      features: [
        "Unlimited room uploads & analyses",
        "Unlimited zero-bleed wall recolours",
        "All 4 daylight Kelvins (3200K - 6800K)",
        "9-Material affinity compatibility scoring",
        "Chroma Memory & personalized DNA engine",
        "Full version timeline & instant rollback",
        "High-resolution unwatermarked PDF & CSV specs",
      ],
      buttonText: "Upgrade to Studio Plus",
      popular: true,
    },
    {
      id: "pro",
      name: "Architect Pro",
      priceMonthly: 1999,
      priceAnnual: 19990,
      description: "For architectural firms requiring enterprise-grade CV tools.",
      features: [
        "Everything in Studio Plus",
        "Multi-user team workspace collaboration",
        "Raw EXIF radiometric analysis",
        "Commercial Indian paint brand code matching",
        "Custom substrate texture mapping",
        "Priority CIELAB batch processing",
        "Dedicated architect support & SLA",
      ],
      buttonText: "Get Architect Pro",
      popular: false,
    },
  ];

  const handleSelectPlan = async (planId: string) => {
    if (planId === "free") return;
    setSelectedPlan(planId);
    setModalOpen(true);
    setCheckoutStatus(null);
  };

  const handleSimulatePayment = async () => {
    if (!selectedPlan) return;
    setIsProcessing(true);
    setCheckoutStatus(null);
    try {
      // 1. Create order
      const orderRes = await api.createOrder(selectedPlan, billingCycle);
      if (orderRes.already_active) {
        setCheckoutStatus(orderRes.message || "You already have this plan active.");
        return;
      }
      const checkout = orderRes.checkout;

      // 2. Simulate verified Razorpay payment with cryptographic HMAC signature
      const verifyRes = await api.verifyPayment({
        razorpay_order_id: checkout.order_id,
        razorpay_payment_id: checkout.payment_id,
        razorpay_signature: checkout.signature,
        plan_id: selectedPlan,
        billing_cycle: billingCycle,
      });

      setCheckoutStatus("success");
      setTimeout(() => {
        setModalOpen(false);
        setCheckoutStatus(null);
      }, 1800);
    } catch (err: any) {
      setCheckoutStatus(err.detail || err.message || "Payment verification failed.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <section className="py-20 border-t border-[#2E332B] bg-[#121411]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-14">
          <span className="text-xs uppercase tracking-widest text-[#B85C38] font-bold block mb-2">
            Transparent Pricing
          </span>
          <h2 className="text-3xl sm:text-4xl font-serif text-[#F4F1EA]">
            Architectural intelligence for every project scale.
          </h2>
          <p className="text-sm text-[#A8A69E] mt-3">
            Choose a plan tailored to your workflow. No hidden fees or lock-ins.
          </p>

          {/* Billing Cycle Toggle */}
          <div className="mt-8 inline-flex items-center gap-2 p-1 rounded-full bg-[#1B1E19] border border-[#2E332B]">
            <button
              onClick={() => setBillingCycle("monthly")}
              className={`px-4 py-1.5 rounded-full text-xs font-medium transition-all ${
                billingCycle === "monthly"
                  ? "bg-[#242822] text-[#F4F1EA] shadow-sm"
                  : "text-[#A8A69E] hover:text-[#F4F1EA]"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingCycle("annual")}
              className={`px-4 py-1.5 rounded-full text-xs font-medium transition-all flex items-center gap-1.5 ${
                billingCycle === "annual"
                  ? "bg-[#242822] text-[#F4F1EA] shadow-sm"
                  : "text-[#A8A69E] hover:text-[#F4F1EA]"
              }`}
            >
              <span>Annual</span>
              <span className="text-[10px] text-[#4E8752] font-semibold">
                (Save 17%)
              </span>
            </button>
          </div>
        </div>

        {/* Pricing Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch">
          {plans.map((p) => {
            const price = billingCycle === "monthly" ? p.priceMonthly : Math.round(p.priceAnnual / 12);
            return (
              <div
                key={p.id}
                className={`relative p-8 rounded-2xl flex flex-col justify-between transition-all duration-300 ${
                  p.popular
                    ? "bg-[#1B1E19] border-2 border-[#B85C38] shadow-2xl shadow-[#B85C38]/10 lg:-translate-y-2"
                    : "bg-[#1B1E19] border border-[#2E332B] hover:border-[#444B40]"
                }`}
              >
                {p.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-[#B85C38] text-[10px] uppercase tracking-wider font-bold text-white shadow-md">
                    Most Popular
                  </div>
                )}

                <div>
                  <h3 className="text-xl font-serif text-[#F4F1EA] mb-2">
                    {p.name}
                  </h3>
                  <p className="text-xs text-[#A8A69E] mb-6 min-h-[36px]">
                    {p.description}
                  </p>

                  <div className="flex items-baseline gap-1 mb-6">
                    <span className="text-4xl font-serif font-bold text-[#F4F1EA]">
                      ₹{price.toLocaleString("en-IN")}
                    </span>
                    <span className="text-xs text-[#A8A69E]">
                      / month
                    </span>
                  </div>

                  <ul className="space-y-3 pt-6 border-t border-[#2E332B]">
                    {p.features.map((feat, idx) => (
                      <li key={idx} className="flex items-start gap-2.5 text-xs text-[#F4F1EA]">
                        <Check className="w-4 h-4 text-[#4E8752] shrink-0 mt-0.5" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <button
                  onClick={() => handleSelectPlan(p.id)}
                  disabled={p.id === "free"}
                  className={`mt-8 w-full py-3 rounded-xl text-xs font-semibold uppercase tracking-wider transition-all cursor-pointer ${
                    p.popular
                      ? "bg-[#B85C38] hover:bg-[#D47149] text-white shadow-md shadow-[#B85C38]/20"
                      : p.id === "free"
                      ? "bg-[#242822] text-[#A8A69E] cursor-not-allowed"
                      : "bg-[#242822] hover:bg-[#2E332B] text-[#F4F1EA] border border-[#2E332B]"
                  }`}
                >
                  {p.buttonText}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Razorpay Simulation Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#1B1E19] border border-[#2E332B] rounded-2xl max-w-md w-full p-6 relative">
            <button
              onClick={() => setModalOpen(false)}
              className="absolute top-4 right-4 text-[#A8A69E] hover:text-[#F4F1EA]"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-[#242822] border border-[#2E332B] flex items-center justify-center text-[#B85C38]">
                <CreditCard className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-base font-serif text-[#F4F1EA]">
                  Razorpay Checkout Sandbox
                </h4>
                <span className="text-[10px] text-[#A8A69E]">
                  Secure simulated payment gateway
                </span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#242822] border border-[#2E332B] mb-6 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-[#A8A69E]">Plan:</span>
                <span className="font-semibold text-[#F4F1EA] uppercase">{selectedPlan}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#A8A69E]">Billing Cycle:</span>
                <span className="text-[#F4F1EA] capitalize">{billingCycle}</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-[#2E332B] font-semibold text-sm">
                <span className="text-[#F4F1EA]">Total Amount:</span>
                <span className="text-[#B85C38]">
                  ₹{selectedPlan === "plus" ? "799" : "1,999"}
                </span>
              </div>
            </div>

            {checkoutStatus === "success" ? (
              <div className="p-4 rounded-xl bg-[#4E8752]/20 border border-[#4E8752]/40 text-xs text-[#4E8752] text-center font-medium">
                Payment verified successfully! Subscription activated.
              </div>
            ) : (
              <button
                onClick={handleSimulatePayment}
                disabled={isProcessing}
                className="w-full py-3 rounded-xl bg-[#B85C38] hover:bg-[#D47149] text-xs font-semibold uppercase tracking-wider text-white transition-all cursor-pointer flex items-center justify-center gap-2"
              >
                {isProcessing ? "Verifying..." : "Confirm & Activate Subscription"}
              </button>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
