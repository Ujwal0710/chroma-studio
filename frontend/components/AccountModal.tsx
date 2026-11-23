"use client";

import React, { useState, useEffect, useCallback } from "react";
import { X, User, KeyRound, Download, Trash2, Check, AlertCircle, Shield, Sparkles, RefreshCw, Layers, ArrowUpRight, ArrowDownRight, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";

interface AccountModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: any;
  setCurrentUser: (u: any) => void;
}

const AVAILABLE_PLANS = [
  {
    id: "free",
    name: "Free Starter",
    priceMonthlyInr: 0,
    analysesLimit: 3,
    aiPreviewLimit: 0,
    description: "For personal interior experiments & concept sketches."
  },
  {
    id: "plus",
    name: "Plus Creator",
    priceMonthlyInr: 299,
    analysesLimit: 30,
    aiPreviewLimit: 5,
    description: "For residential designers & boutique architectural studios."
  },
  {
    id: "pro",
    name: "Architect Pro",
    priceMonthlyInr: 699,
    analysesLimit: 999,
    aiPreviewLimit: 50,
    description: "For commercial architectural firms requiring unrestricted compute."
  }
];

export function AccountModal({ isOpen, onClose, currentUser, setCurrentUser }: AccountModalProps) {
  const [tab, setTab] = useState<"login" | "register" | "reset" | "profile">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [infoMsg, setInfoMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [switchingPlanId, setSwitchingPlanId] = useState<string | null>(null);

  // Live Subscription & Usage state from DB
  const [subscription, setSubscription] = useState<any>(null);
  const [usage, setUsage] = useState<any>(null);

  const fetchSubscriptionDetails = useCallback(async () => {
    try {
      const data = await api.getCurrentSubscription();
      if (data && data.subscription) {
        setSubscription(data.subscription);
        setUsage(data.usage);
      }
    } catch (e) {
      console.warn("Failed to fetch fresh subscription details:", e);
    }
  }, []);

  useEffect(() => {
    if (currentUser?.id && isOpen) {
      setTab("profile");
      fetchSubscriptionDetails();
    } else if (!currentUser?.id) {
      setTab("login");
      setSubscription(null);
      setUsage(null);
    }
    setErrorMsg(null);
    setSuccessMsg(null);
    setInfoMsg(null);
  }, [currentUser?.id, isOpen, fetchSubscriptionDetails]);

  if (!isOpen) return null;

  const currentPlanId = subscription?.plan_id || currentUser?.plan_id || "free";
  const currentPlanDetails = subscription?.plan_details || AVAILABLE_PLANS.find(p => p.id === currentPlanId) || AVAILABLE_PLANS[0];

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setInfoMsg(null);
    try {
      const res = await api.login({ email, password });
      setCurrentUser(res.user);
      setSuccessMsg("Logged in successfully!");
      setTimeout(() => {
        setSuccessMsg(null);
        onClose();
      }, 1000);
    } catch (err: any) {
      setErrorMsg(err.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setInfoMsg(null);
    try {
      const res = await api.register({ email, password, full_name: fullName });
      setCurrentUser(res.user);
      setSuccessMsg("Account created and signed in!");
      setTimeout(() => {
        setSuccessMsg(null);
        onClose();
      }, 1000);
    } catch (err: any) {
      setErrorMsg(err.message || "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleResetRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.requestReset(email);
      setSuccessMsg(res.message);
      if (res.dev_token) {
        setResetToken(res.dev_token);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Password recovery failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleResetConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.confirmReset({ token: resetToken, new_password: newPassword });
      setSuccessMsg(res.message);
      setTab("login");
    } catch (err: any) {
      setErrorMsg(err.message || "Password reset failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await api.logout();
      setCurrentUser(null);
      setSubscription(null);
      setUsage(null);
      setTab("login");
    } catch (err) {
      console.error(err);
    }
  };

  // Plan Switching Handler (Upgrade, Downgrade, Repeat Check)
  const handleSwitchPlan = async (targetPlanId: string) => {
    setErrorMsg(null);
    setSuccessMsg(null);
    setInfoMsg(null);

    // Guard against switching to current active plan
    if (targetPlanId === currentPlanId) {
      setInfoMsg(`You already have the ${currentPlanDetails.name} active. Choose another tier to upgrade or downgrade.`);
      return;
    }

    setSwitchingPlanId(targetPlanId);
    try {
      const res = await api.switchPlan({ plan_id: targetPlanId, billing_cycle: "monthly" });

      if (res.already_active) {
        setInfoMsg(res.message);
      } else {
        setSuccessMsg(res.message || `Successfully switched to ${targetPlanId.toUpperCase()}!`);
        if (res.user) {
          setCurrentUser(res.user);
        }
        if (res.subscription) {
          setSubscription(res.subscription);
          setUsage(res.usage);
        }
        // Refresh fresh data from server
        fetchSubscriptionDetails();
      }
    } catch (err: any) {
      setErrorMsg(err.detail || err.message || "Payment verification failed. Could not switch plan.");
    } finally {
      setSwitchingPlanId(null);
    }
  };

  const handleExportData = async () => {
    try {
      const res = await api.getAccountData();
      const blob = new Blob([JSON.stringify(res, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `chroma_account_data_${Date.now()}.json`;
      a.click();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to download data.");
    }
  };

  const handleDeleteAccount = async () => {
    if (!window.confirm("Are you sure you want to permanently delete your account and all associated project data?")) return;
    try {
      await api.deleteAccount("DELETE_MY_ACCOUNT");
      setCurrentUser(null);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || "Account deletion failed.");
    }
  };

  const expiryDateFormatted = subscription?.current_period_end
    ? new Date(subscription.current_period_end).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : "Lifetime Active";

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-[#181B16] border border-[#2E332B] rounded-3xl max-w-lg w-full p-6 sm:p-8 relative shadow-2xl my-8">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-full bg-white/5 hover:bg-white/10 text-[#A8A69E] hover:text-[#F4F1EA] transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Modal Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-[#B85C38]" />
            <span className="text-[10px] uppercase font-mono tracking-widest text-[#B85C38]">
              {currentUser ? "Client Identity & Entitlements" : "Atelier Gateway"}
            </span>
          </div>
          <h3 className="text-2xl font-serif text-[#F4F1EA]">
            {currentUser ? "Architect Profile & Subscription" : tab === "login" ? "Sign In to Atelier" : tab === "register" ? "Create Architect Account" : "Reset Password"}
          </h3>
          <p className="text-xs text-[#A8A69E] mt-1">
            {currentUser ? "Single source of truth for your plan quotas, usage, and privacy." : "Access saved architectural palettes, timeline snapshots, and Chroma DNA."}
          </p>
        </div>

        {/* Notification Banners */}
        {errorMsg && (
          <div className="p-3.5 mb-4 rounded-xl bg-red-950/60 border border-red-800/80 text-xs text-red-200 flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-400" />
            <span>{errorMsg}</span>
          </div>
        )}

        {infoMsg && (
          <div className="p-3.5 mb-4 rounded-xl bg-blue-950/50 border border-blue-800/60 text-xs text-blue-200 flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-blue-400" />
            <span>{infoMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="p-3.5 mb-4 rounded-xl bg-emerald-950/60 border border-emerald-800/80 text-xs text-emerald-200 flex items-start gap-2.5">
            <Check className="w-4 h-4 shrink-0 mt-0.5 text-emerald-400" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Profile & Plan Management View */}
        {currentUser ? (
          <div className="space-y-6">
            {/* Identity Strip */}
            <div className="p-4 rounded-2xl bg-[#20241E] border border-[#2E332B] space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-[#A8A69E]">Full Name</span>
                <span className="text-[#F4F1EA] font-medium">{currentUser.full_name}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[#A8A69E]">Email</span>
                <span className="text-[#F4F1EA] font-mono">{currentUser.email}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[#A8A69E]">Design Role</span>
                <span className="px-2 py-0.5 rounded-md bg-[#B85C38]/10 text-[#B85C38] border border-[#B85C38]/20 font-mono uppercase text-[10px]">
                  {currentUser.role || "Architect"}
                </span>
              </div>
            </div>

            {/* Current Active Plan Card */}
            <div className="p-5 rounded-2xl bg-gradient-to-br from-[#20241E] to-[#1A1D17] border border-[#2E332B] relative overflow-hidden">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-[#B85C38]" />
                  <span className="text-xs font-semibold text-[#F4F1EA]">Current Plan</span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#B85C38] text-white">
                  {currentPlanDetails.name}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs pt-1 mb-4">
                <div>
                  <span className="text-[#A8A69E] block text-[11px]">Billing Cycle:</span>
                  <span className="text-[#F4F1EA] font-medium capitalize">
                    {subscription?.billing_cycle || "Monthly"}
                  </span>
                </div>
                <div>
                  <span className="text-[#A8A69E] block text-[11px]">Renewal / Expiry:</span>
                  <span className="text-[#F4F1EA] font-mono text-[11px]">
                    {expiryDateFormatted}
                  </span>
                </div>
              </div>

              {/* Real-time Usage Progress */}
              <div className="space-y-3 pt-3 border-t border-white/5 text-xs">
                <div>
                  <div className="flex justify-between text-[11px] text-[#A8A69E] mb-1">
                    <span>Monthly Room Analyses</span>
                    <span className="font-mono text-[#F4F1EA]">
                      {usage?.analyses_used ?? 0} / {currentPlanDetails.analysesLimit > 500 ? "Unlimited" : currentPlanDetails.analysesLimit}
                    </span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-black/40 overflow-hidden">
                    <div
                      className="h-full bg-[#B85C38] rounded-full transition-all"
                      style={{
                        width: `${Math.min(
                          100,
                          currentPlanDetails.analysesLimit > 500
                            ? 15
                            : ((usage?.analyses_used ?? 0) / Math.max(1, currentPlanDetails.analysesLimit)) * 100
                        )}%`,
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-[11px] text-[#A8A69E] mb-1">
                    <span>AI Photometric Previews</span>
                    <span className="font-mono text-[#F4F1EA]">
                      {usage?.ai_previews_used ?? 0} / {currentPlanDetails.aiPreviewLimit}
                    </span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-black/40 overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full transition-all"
                      style={{
                        width: `${Math.min(
                          100,
                          currentPlanDetails.aiPreviewLimit === 0
                            ? 0
                            : ((usage?.ai_previews_used ?? 0) / Math.max(1, currentPlanDetails.aiPreviewLimit)) * 100
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Change Plan Tier Grid */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs uppercase tracking-wider font-semibold text-[#A8A69E]">
                  Change Plan Tier
                </span>
                <span className="text-[10px] text-white/40">Instant server activation</span>
              </div>

              <div className="space-y-2.5">
                {AVAILABLE_PLANS.map((plan) => {
                  const isCurrent = plan.id === currentPlanId;
                  const isUpgrade = plan.priceMonthlyInr > (currentPlanDetails.priceMonthlyInr ?? 0);
                  const isDowngrade = plan.priceMonthlyInr < (currentPlanDetails.priceMonthlyInr ?? 0);
                  const isPending = switchingPlanId === plan.id;

                  return (
                    <div
                      key={plan.id}
                      className={`p-3.5 rounded-2xl border transition-all flex items-center justify-between gap-3 ${
                        isCurrent
                          ? "bg-[#B85C38]/10 border-[#B85C38]/40"
                          : "bg-[#20241E] border-[#2E332B] hover:border-white/20"
                      }`}
                    >
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-[#F4F1EA]">{plan.name}</span>
                          <span className="text-[11px] font-mono text-white/50">
                            {plan.priceMonthlyInr === 0 ? "Free" : `₹${plan.priceMonthlyInr}/mo`}
                          </span>
                        </div>
                        <p className="text-[11px] text-[#A8A69E] truncate mt-0.5">{plan.description}</p>
                      </div>

                      <button
                        onClick={() => handleSwitchPlan(plan.id)}
                        disabled={isPending}
                        className={`px-3.5 py-1.5 rounded-xl text-xs font-medium shrink-0 flex items-center gap-1.5 transition-all ${
                          isCurrent
                            ? "bg-white/10 text-white/80 cursor-default"
                            : isUpgrade
                            ? "bg-[#B85C38] hover:bg-[#A04D2E] text-white shadow-md shadow-[#B85C38]/20"
                            : "bg-white/5 hover:bg-white/10 text-white/70 border border-white/10"
                        }`}
                      >
                        {isPending ? (
                          <>
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                            <span>Updating...</span>
                          </>
                        ) : isCurrent ? (
                          <>
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                            <span>Active</span>
                          </>
                        ) : isUpgrade ? (
                          <>
                            <ArrowUpRight className="w-3.5 h-3.5" />
                            <span>Upgrade</span>
                          </>
                        ) : (
                          <>
                            <ArrowDownRight className="w-3.5 h-3.5" />
                            <span>Downgrade</span>
                          </>
                        )}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* GDPR & Account Actions */}
            <div className="pt-2 border-t border-white/5 space-y-2">
              <button
                onClick={handleExportData}
                className="w-full py-2.5 rounded-xl bg-[#20241E] hover:bg-[#2E332B] border border-[#2E332B] text-xs text-[#F4F1EA] flex items-center justify-center gap-2 transition-colors cursor-pointer"
              >
                <Download className="w-3.5 h-3.5 text-[#B85C38]" /> Export Personal Data (GDPR)
              </button>

              <button
                onClick={handleLogout}
                className="w-full py-2.5 rounded-xl bg-[#20241E] hover:bg-[#2E332B] border border-[#2E332B] text-xs text-[#F4F1EA] transition-colors cursor-pointer"
              >
                Sign Out
              </button>

              <button
                onClick={handleDeleteAccount}
                className="w-full py-2 text-xs text-red-400 hover:text-red-300 transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" /> Delete Account Permanently
              </button>
            </div>
          </div>
        ) : (
          /* Authentication Forms */
          <div>
            {tab === "login" && (
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="text-xs text-[#A8A69E] block mb-1">Email Address</label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-[#20241E] border border-[#2E332B] text-xs text-[#F4F1EA] focus:border-[#B85C38] focus:outline-none"
                    placeholder="architect@atelier.com"
                  />
                </div>
                <div>
                  <label className="text-xs text-[#A8A69E] block mb-1">Password</label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-[#20241E] border border-[#2E332B] text-xs text-[#F4F1EA] focus:border-[#B85C38] focus:outline-none"
                    placeholder="••••••••••••"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-[#B85C38] hover:bg-[#A04D2E] text-xs text-white font-medium transition-all shadow-lg shadow-[#B85C38]/25 cursor-pointer disabled:opacity-50"
                >
                  {loading ? "Authenticating..." : "Sign In to Studio"}
                </button>
                <div className="flex justify-between items-center pt-2 text-xs text-[#A8A69E]">
                  <button
                    type="button"
                    onClick={() => setTab("register")}
                    className="hover:text-[#F4F1EA] transition-colors cursor-pointer"
                  >
                    Need an account? Register
                  </button>
                  <button
                    type="button"
                    onClick={() => setTab("reset")}
                    className="hover:text-[#F4F1EA] transition-colors cursor-pointer"
                  >
                    Forgot Password?
                  </button>
                </div>
              </form>
            )}

            {tab === "register" && (
              <form onSubmit={handleRegister} className="space-y-4">
                <div>
                  <label className="text-xs text-[#A8A69E] block mb-1">Full Name</label>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-[#20241E] border border-[#2E332B] text-xs text-[#F4F1EA] focus:border-[#B85C38] focus:outline-none"
                    placeholder="Jane Doe, Architect"
                  />
                </div>
                <div>
                  <label className="text-xs text-[#A8A69E] block mb-1">Email Address</label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-[#20241E] border border-[#2E332B] text-xs text-[#F4F1EA] focus:border-[#B85C38] focus:outline-none"
                    placeholder="architect@atelier.com"
                  />
                </div>
                <div>
                  <label className="text-xs text-[#A8A69E] block mb-1">Password</label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-[#20241E] border border-[#2E332B] text-xs text-[#F4F1EA] focus:border-[#B85C38] focus:outline-none"
                    placeholder="Min 8 chars, 1 uppercase, 1 digit, 1 symbol"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-[#B85C38] hover:bg-[#A04D2E] text-xs text-white font-medium transition-all shadow-lg shadow-[#B85C38]/25 cursor-pointer disabled:opacity-50"
                >
                  {loading ? "Creating Account..." : "Register & Start Free"}
                </button>
                <div className="text-center pt-2">
                  <button
                    type="button"
                    onClick={() => setTab("login")}
                    className="text-xs text-[#A8A69E] hover:text-[#F4F1EA] transition-colors cursor-pointer"
                  >
                    Already have an account? Sign In
                  </button>
                </div>
              </form>
            )}

            {tab === "reset" && (
              <form onSubmit={resetToken ? handleResetConfirm : handleResetRequest} className="space-y-4">
                {!resetToken ? (
                  <div>
                    <label className="text-xs text-[#A8A69E] block mb-1">Registered Email Address</label>
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-[#20241E] border border-[#2E332B] text-xs text-[#F4F1EA] focus:border-[#B85C38] focus:outline-none"
                      placeholder="architect@atelier.com"
                    />
                  </div>
                ) : (
                  <>
                    <div>
                      <label className="text-xs text-[#A8A69E] block mb-1">Recovery Token</label>
                      <input
                        type="text"
                        required
                        value={resetToken}
                        onChange={(e) => setResetToken(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl bg-[#20241E] border border-[#2E332B] text-xs text-[#F4F1EA] font-mono focus:border-[#B85C38] focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-[#A8A69E] block mb-1">New Password</label>
                      <input
                        type="password"
                        required
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="w-full px-3.5 py-2.5 rounded-xl bg-[#20241E] border border-[#2E332B] text-xs text-[#F4F1EA] focus:border-[#B85C38] focus:outline-none"
                      />
                    </div>
                  </>
                )}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-[#B85C38] hover:bg-[#A04D2E] text-xs text-white font-medium transition-all shadow-lg shadow-[#B85C38]/25 cursor-pointer disabled:opacity-50"
                >
                  {loading ? "Processing..." : resetToken ? "Set New Password" : "Send Recovery Token"}
                </button>
                <div className="text-center pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setTab("login");
                      setResetToken("");
                    }}
                    className="text-xs text-[#A8A69E] hover:text-[#F4F1EA] transition-colors cursor-pointer"
                  >
                    Back to Sign In
                  </button>
                </div>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
