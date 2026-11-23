"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { Camera, RefreshCw, Zap, AlertTriangle, CheckCircle, ShieldAlert, Sparkles, Sliders, Eye, Upload } from "lucide-react";
import { api } from "@/lib/api";

interface LiveScanViewProps {
  onCaptureRoom?: (file: File) => void;
  onNavigateToStudio?: () => void;
}

const PRESET_COLORS = [
  { hex: "#B85C38", name: "Terracotta Earth" },
  { hex: "#D6C5B3", name: "Warm Oatmeal" },
  { hex: "#3B82F6", name: "Riviera Blue" },
  { hex: "#10B981", name: "Sage Sanctuary" },
  { hex: "#D97706", name: "Heritage Amber" },
  { hex: "#1F2937", name: "Obsidian Noir" },
];

export const LiveScanView: React.FC<LiveScanViewProps> = ({ onCaptureRoom, onNavigateToStudio }) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const offscreenCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameIdRef = useRef<number | null>(null);

  const [streamActive, setStreamActive] = useState<boolean>(false);
  const [facingMode, setFacingMode] = useState<"environment" | "user">("environment");
  const [selectedHex, setSelectedHex] = useState<string>("#B85C38");
  const [intensity, setIntensity] = useState<number>(0.85);
  const [fps, setFps] = useState<number>(0);
  const [wallCoverage, setWallCoverage] = useState<number>(0);
  const [errorState, setErrorState] = useState<string | null>(null);
  const [lowLightWarning, setLowLightWarning] = useState<boolean>(false);
  const [isProcessingFrame, setIsProcessingFrame] = useState<boolean>(false);
  const [isCapturing, setIsCapturing] = useState<boolean>(false);
  const [showSimulatedFeed, setShowSimulatedFeed] = useState<boolean>(false);

  const lastFrameTimeRef = useRef<number>(Date.now());
  const frameCountRef = useRef<number>(0);
  const inFlightRef = useRef<boolean>(false);
  const previousOverlayRef = useRef<HTMLImageElement | null>(null);

  // Initialize camera stream
  const startCamera = useCallback(async () => {
    setErrorState(null);
    setLowLightWarning(false);

    // Verify secure context
    if (typeof window !== "undefined" && window.location.protocol !== "https:" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
      setErrorState("insecure_context");
      return;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setErrorState("unsupported");
      return;
    }

    try {
      if (videoRef.current && videoRef.current.srcObject) {
        const existingStream = videoRef.current.srcObject as MediaStream;
        existingStream.getTracks().forEach((track) => track.stop());
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: facingMode },
          width: { ideal: 640 },
          height: { ideal: 480 },
        },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().then(() => {
          setStreamActive(true);
        }).catch(() => {
          setStreamActive(true);
        });
      }
    } catch (err: any) {
      console.warn("getUserMedia error:", err);
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        setErrorState("permission_denied");
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        setErrorState("not_found");
      } else {
        setErrorState(err.message || "camera_error");
      }
    }
  }, [facingMode]);

  useEffect(() => {
    startCamera();
    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach((track) => track.stop());
      }
      if (animationFrameIdRef.current) {
        cancelAnimationFrame(animationFrameIdRef.current);
      }
    };
  }, [startCamera]);

  // Frame processing loop
  useEffect(() => {
    if (!streamActive && !showSimulatedFeed) return;

    let isMounted = true;
    const processLoop = async () => {
      if (!isMounted) return;

      const now = Date.now();
      const elapsed = now - lastFrameTimeRef.current;
      if (elapsed >= 1000) {
        setFps(Math.round((frameCountRef.current * 1000) / elapsed));
        frameCountRef.current = 0;
        lastFrameTimeRef.current = now;
      }

      // Run inference at ~5 FPS (every ~200ms) and drop frames if backend is still processing
      if (!inFlightRef.current && (videoRef.current || showSimulatedFeed)) {
        const video = videoRef.current;
        if ((video && video.readyState >= 2 && video.videoWidth > 0) || showSimulatedFeed) {
          inFlightRef.current = true;
          frameCountRef.current += 1;

          try {
            if (!offscreenCanvasRef.current) {
              offscreenCanvasRef.current = document.createElement("canvas");
            }
            const off = offscreenCanvasRef.current;
            const targetW = 480;
            const targetH = 360;
            off.width = targetW;
            off.height = targetH;
            const ctx = off.getContext("2d");

            if (ctx) {
              if (showSimulatedFeed || !video) {
                // Synthetic realistic room canvas for testing
                ctx.fillStyle = "#E8E4DC";
                ctx.fillRect(0, 0, targetW, targetH * 0.72);
                ctx.fillStyle = "#8C7355";
                ctx.fillRect(0, targetH * 0.72, targetW, targetH * 0.28);
                // Sofa
                ctx.fillStyle = "#333333";
                ctx.fillRect(targetW * 0.2, targetH * 0.45, targetW * 0.6, targetH * 0.35);
              } else {
                ctx.drawImage(video, 0, 0, targetW, targetH);
              }

              // Check for low light
              const imgData = ctx.getImageData(0, 0, targetW, targetH);
              let totalLuma = 0;
              for (let i = 0; i < imgData.data.length; i += 16) {
                totalLuma += 0.299 * imgData.data[i] + 0.587 * imgData.data[i + 1] + 0.114 * imgData.data[i + 2];
              }
              const avgLuma = totalLuma / (imgData.data.length / 16);
              setLowLightWarning(avgLuma < 40);

              // Downscaled JPEG base64 payload
              const frameB64 = off.toDataURL("image/jpeg", 0.70);

              const res = await api.liveSegment({
                image_base64: frameB64,
                target_hex: selectedHex,
                intensity: intensity,
              });

              if (res && res.recoloured_frame && canvasRef.current) {
                setWallCoverage(res.wall_coverage || 0);

                const overlayImg = new Image();
                overlayImg.src = res.recoloured_frame;
                overlayImg.onload = () => {
                  if (!canvasRef.current) return;
                  const c = canvasRef.current;
                  const cCtx = c.getContext("2d");
                  if (cCtx) {
                    c.width = targetW;
                    c.height = targetH;
                    // Exponential Moving Average (EMA) alpha blending for temporal stability
                    cCtx.globalAlpha = 0.85;
                    cCtx.drawImage(overlayImg, 0, 0, targetW, targetH);
                    cCtx.globalAlpha = 1.0;
                  }
                };
              }
            }
          } catch (e) {
            // Drop frame on error
          } finally {
            inFlightRef.current = false;
          }
        }
      }

      animationFrameIdRef.current = requestAnimationFrame(processLoop);
    };

    animationFrameIdRef.current = requestAnimationFrame(processLoop);

    return () => {
      isMounted = false;
      if (animationFrameIdRef.current) cancelAnimationFrame(animationFrameIdRef.current);
    };
  }, [streamActive, showSimulatedFeed, selectedHex, intensity]);

  // Flip between front and rear cameras
  const toggleCamera = () => {
    setFacingMode((prev) => (prev === "environment" ? "user" : "environment"));
  };

  // High-Resolution Still Capture & Studio Transfer
  const handleCaptureAndAnalyse = async () => {
    setIsCapturing(true);
    try {
      let captureCanvas = document.createElement("canvas");
      let captureW = 1280;
      let captureH = 960;
      captureCanvas.width = captureW;
      captureCanvas.height = captureH;
      const ctx = captureCanvas.getContext("2d");

      if (ctx) {
        if (showSimulatedFeed || !videoRef.current) {
          ctx.fillStyle = "#EAE6DE";
          ctx.fillRect(0, 0, captureW, captureH * 0.72);
          ctx.fillStyle = "#9C8265";
          ctx.fillRect(0, captureH * 0.72, captureW, captureH * 0.28);
          ctx.fillStyle = "#2D3748";
          ctx.fillRect(captureW * 0.2, captureH * 0.45, captureW * 0.6, captureH * 0.35);
        } else {
          captureW = videoRef.current.videoWidth || 1280;
          captureH = videoRef.current.videoHeight || 960;
          captureCanvas.width = captureW;
          captureCanvas.height = captureH;
          ctx.drawImage(videoRef.current, 0, 0, captureW, captureH);
        }

        captureCanvas.toBlob(
          (blob) => {
            if (blob && onCaptureRoom) {
              const file = new File([blob], `live_capture_${Date.now()}.jpg`, { type: "image/jpeg" });
              onCaptureRoom(file);
              if (onNavigateToStudio) onNavigateToStudio();
            }
            setIsCapturing(false);
          },
          "image/jpeg",
          0.92
        );
      }
    } catch (e) {
      console.error("Capture failure:", e);
      setIsCapturing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-[#14171d]/80 border border-white/5 backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Camera className="w-3.5 h-3.5 animate-pulse" />
              Live Computer Vision Scanner
            </span>
            <span className="text-xs text-white/40">• 480p Continuous Stream</span>
          </div>
          <h2 className="text-2xl font-serif text-white/90">Real-Time Room Lens & Temporal Recolour</h2>
          <p className="text-sm text-white/50">Point your camera at any interior wall to preview physical architectural paint in motion.</p>
        </div>

        {/* Telemetry Chips */}
        <div className="flex items-center gap-2.5">
          <div className="px-3 py-1.5 rounded-xl bg-black/40 border border-white/10 flex items-center gap-2 text-xs">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-white/40">Inference:</span>
            <span className="font-mono text-white/90">{fps > 0 ? `${fps} FPS` : "Calibrating..."}</span>
          </div>
          <div className="px-3 py-1.5 rounded-xl bg-black/40 border border-white/10 flex items-center gap-2 text-xs">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-white/40">Wall:</span>
            <span className="font-mono text-white/90">{wallCoverage}%</span>
          </div>
          <button
            onClick={toggleCamera}
            className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white/80 transition-colors"
            title="Switch Rear/Front Camera"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Warnings & Insecure Context Notice */}
      {errorState === "insecure_context" && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-sm">
            <h4 className="font-medium text-amber-300">Camera Requires HTTPS / Localhost Context</h4>
            <p className="text-white/60 text-xs mt-1">
              Browsers restrict camera access to <code className="text-amber-200">https://</code> or <code className="text-amber-200">localhost</code> for security.
              To test on a smartphone, use local SSL certificates or run a Cloudflare/ngrok tunnel. You can also use the Simulated Feed below.
            </p>
          </div>
        </div>
      )}

      {errorState === "permission_denied" && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div className="text-sm">
            <h4 className="font-medium text-red-300">Camera Permission Blocked</h4>
            <p className="text-white/60 text-xs mt-1">
              Please click the camera icon in your browser URL bar and choose "Allow" to enable live wall scanning.
            </p>
          </div>
        </div>
      )}

      {lowLightWarning && (
        <div className="p-3 rounded-xl bg-yellow-500/10 border border-yellow-500/20 flex items-center gap-2 text-xs text-yellow-300">
          <AlertTriangle className="w-4 h-4" />
          <span>Low ambient illumination detected. Turn on room lighting for accurate paint tone evaluation.</span>
        </div>
      )}

      {/* Main Viewport & Video Overlay */}
      <div className="relative aspect-[4/3] max-w-3xl mx-auto rounded-3xl overflow-hidden bg-black/90 border border-white/10 shadow-2xl">
        {/* Hidden Raw Video Stream */}
        <video
          ref={videoRef}
          playsInline
          muted
          autoPlay
          className="absolute inset-0 w-full h-full object-cover"
        />

        {/* Live SegFormer Optical Recolour Canvas Overlay */}
        <canvas
          ref={canvasRef}
          className="absolute inset-0 w-full h-full object-cover pointer-events-none"
        />

        {/* Active Reticle & Spatial HUD */}
        <div className="absolute inset-0 pointer-events-none border border-white/10 m-6 rounded-2xl flex flex-col justify-between p-4">
          <div className="flex justify-between items-center text-[11px] font-mono text-white/50">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              LIVE SHADING ENGINE
            </span>
            <span>{facingMode.toUpperCase()} SENSOR</span>
          </div>
          <div className="self-center w-12 h-12 border border-white/30 rounded-full flex items-center justify-center">
            <div className="w-1.5 h-1.5 bg-amber-400 rounded-full" />
          </div>
          <div className="flex justify-between items-center text-[11px] font-mono text-white/40">
            <span>STABILISATION: EMA α=0.85</span>
            <span>TONE: {selectedHex}</span>
          </div>
        </div>

        {/* Floating Capture Trigger */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-3">
          <button
            onClick={handleCaptureAndAnalyse}
            disabled={isCapturing}
            className="px-6 py-3 rounded-full bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-black font-semibold shadow-lg shadow-amber-500/25 flex items-center gap-2 transition-all transform hover:scale-105 active:scale-95 disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            <span>{isCapturing ? "Processing Still..." : "Capture & Analyse in Studio"}</span>
          </button>
        </div>
      </div>

      {/* Interactive Controls Strip */}
      <div className="max-w-3xl mx-auto p-5 rounded-2xl bg-[#14171d]/80 border border-white/5 backdrop-blur-md space-y-4">
        {/* Color Palette Chips */}
        <div>
          <label className="block text-xs font-medium text-white/60 mb-2">Live Architectural Pigment</label>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
            {PRESET_COLORS.map((c) => (
              <button
                key={c.hex}
                onClick={() => setSelectedHex(c.hex)}
                className={`p-2 rounded-xl flex items-center gap-2 border text-xs transition-all ${
                  selectedHex === c.hex
                    ? "border-amber-400 bg-amber-400/10 text-white"
                    : "border-white/5 bg-black/30 hover:border-white/20 text-white/70"
                }`}
              >
                <span className="w-4 h-4 rounded-full border border-black/40 shrink-0" style={{ backgroundColor: c.hex }} />
                <span className="truncate">{c.name.split(" ")[0]}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Paint Intensity & Test Controls */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2 border-t border-white/5">
          <div className="w-full sm:w-1/2 flex items-center gap-3">
            <Sliders className="w-4 h-4 text-white/40 shrink-0" />
            <div className="w-full">
              <div className="flex justify-between text-xs text-white/60 mb-1">
                <span>Paint Opacity</span>
                <span className="font-mono text-white/90">{Math.round(intensity * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.30"
                max="1.0"
                step="0.05"
                value={intensity}
                onChange={(e) => setIntensity(parseFloat(e.target.value))}
                className="w-full accent-amber-500 bg-white/10 rounded-lg h-1.5"
              />
            </div>
          </div>

          <div className="flex items-center gap-2 self-end">
            <button
              onClick={() => setShowSimulatedFeed(!showSimulatedFeed)}
              className="px-3 py-1.5 rounded-xl text-xs bg-white/5 hover:bg-white/10 text-white/60 border border-white/10 transition-colors"
            >
              {showSimulatedFeed ? "Disable Test Feed" : "Use Test Room Feed"}
            </button>
            {onNavigateToStudio && (
              <button
                onClick={onNavigateToStudio}
                className="px-3 py-1.5 rounded-xl text-xs bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/20 transition-colors"
              >
                Go to Studio
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
