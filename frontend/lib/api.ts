import { PaletteConcept, RoomAnalysisResponse, ChromaDNA } from "./types";

/**
 * Automatically determine backend base URL:
 * 1. Explicit NEXT_PUBLIC_API_URL environment variable if set.
 * 2. If running on production (Vercel / non-localhost domain), automatically connect to Render backend.
 * 3. Default to local http://localhost:8000 when developing locally.
 */
export function getApiBase(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (envUrl && !envUrl.includes("localhost") && !envUrl.includes("127.0.0.1")) {
    return envUrl.replace(/\/+$/, "");
  }
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (host !== "localhost" && host !== "127.0.0.1") {
      return "https://chroma-studio-api.onrender.com";
    }
  }
  return (envUrl || "http://localhost:8000").replace(/\/+$/, "");
}

/** Default request timeout in milliseconds (short timeout). */
const REQUEST_TIMEOUT_MS = 10_000;

/** Maximum retries for idempotent GET requests on network failure. */
const GET_RETRY_COUNT = 1;

// ---------------------------------------------------------------------------
// Core request helper
// ---------------------------------------------------------------------------

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  { retries = 0 }: { retries?: number } = {}
): Promise<T> {
  const url = `${getApiBase()}${endpoint}`;
  const defaultHeaders: HeadersInit = {
    Accept: "application/json",
  };

  // Don't set Content-Type if sending FormData (let browser set boundary)
  if (!(options.body instanceof FormData)) {
    defaultHeaders["Content-Type"] = "application/json";
  }

  // AbortController for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let res: Response;
  try {
    res = await fetch(url, {
      ...options,
      credentials: "include", // Send/receive httpOnly JWT cookies
      signal: controller.signal,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });
  } catch (err: unknown) {
    clearTimeout(timeoutId);

    // Retry idempotent GET requests once on network failure
    if (retries < GET_RETRY_COUNT && (!options.method || options.method === "GET")) {
      return request<T>(endpoint, options, { retries: retries + 1 });
    }

    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(
        `Request to ${endpoint} timed out after ${REQUEST_TIMEOUT_MS / 1000}s. Is the backend running?`
      );
    }

    throw new Error("Cannot reach the server. Is the backend running?");
  } finally {
    clearTimeout(timeoutId);
  }

  if (!res.ok) {
    let errorDetail = "An unexpected error occurred.";
    try {
      const errJson = await res.json();
      if (errJson.errors && Array.isArray(errJson.errors) && errJson.errors.length > 0) {
        errorDetail = errJson.errors.join("; ");
      } else if (errJson.detail) {
        if (typeof errJson.detail === "string") {
          errorDetail = errJson.detail;
        } else if (Array.isArray(errJson.detail)) {
          errorDetail = errJson.detail
            .map((d: any) => `${d.loc ? d.loc.join(" -> ") : "field"}: ${d.msg || JSON.stringify(d)}`)
            .join("; ");
        } else {
          errorDetail = JSON.stringify(errJson.detail);
        }
      } else {
        errorDetail = errJson.message || JSON.stringify(errJson);
      }
    } catch {
      errorDetail = await res.text();
    }
    throw new Error(errorDetail || `Request failed with status ${res.status}`);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Public API surface
// ---------------------------------------------------------------------------

export const api = {
  // Health
  getHealth: () => request<{ status: string; version: string; offline_mode: boolean }>("/health"),

  // Sample room
  getSampleRoom: () =>
    request<{
      status: string;
      filename: string;
      image_data_url?: string;
      image_data?: string;
      description?: string;
    }>("/rooms/sample"),

  // Rooms
  analyseRoom: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<RoomAnalysisResponse>("/rooms/analyse", {
      method: "POST",
      body: formData,
    });
  },

  segmentRoom: (file: File, sensitivity: number = 0.55, edgeProtection: number = 0.65) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("sensitivity", sensitivity.toString());
    formData.append("edge_protection", edgeProtection.toString());
    return request<any>("/rooms/segment", {
      method: "POST",
      body: formData,
    });
  },

  recolourRoom: (
    file: File,
    targetHex: string,
    intensity: number = 0.85,
    strategy: string = "cielab_perceptual",
    sensitivity: number = 0.55,
    surface: string = "wall",
    multiColors?: { wall?: string; ceiling?: string; trim?: string; accent_wall?: string },
    compensateLighting: boolean = true
  ) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("target_hex", targetHex);
    formData.append("intensity", intensity.toString());
    formData.append("strategy", strategy);
    formData.append("sensitivity", sensitivity.toString());
    formData.append("surface", surface);
    formData.append("compensate_lighting", compensateLighting.toString());

    if (multiColors) {
      if (multiColors.wall) formData.append("wall_hex", multiColors.wall);
      if (multiColors.ceiling) formData.append("ceiling_hex", multiColors.ceiling);
      if (multiColors.trim) formData.append("trim_hex", multiColors.trim);
      if (multiColors.accent_wall) formData.append("accent_hex", multiColors.accent_wall);
    }

    return request<any>("/rooms/recolour", {
      method: "POST",
      body: formData,
    });
  },

  refineMask: (data: {
    mask_b64: string;
    x: number;
    y: number;
    action: "add" | "remove";
    brush_radius?: number;
    guide_image_b64?: string;
  }) =>
    request<any>("/rooms/mask/refine", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  liveSegment: (data: {
    image_base64: string;
    target_hex?: string;
    intensity?: number;
    sensitivity?: number;
  }) =>
    request<{
      status: string;
      recoloured_frame: string;
      mask_png: string;
      wall_coverage: number;
    }>("/rooms/live-segment", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Palettes
  generatePalettes: (params: {
    extracted?: any;
    dominant_tones?: any;
    room_analysis?: any;
    primary_hex?: string;
    room_type?: string;
    interior_style?: string;
    selected_materials?: string[];
  }) =>
    request<PaletteConcept[]>("/palettes/generate", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  swapPaletteRole: (palette: PaletteConcept, fromRole: string, toRole: string) =>
    request<PaletteConcept>("/palettes/swap", {
      method: "POST",
      body: JSON.stringify({
        palette,
        from_role: fromRole,
        to_role: toRole,
      }),
    }),

  swapPaletteColor: (palette: PaletteConcept, targetRole: string, newHex: string) =>
    request<PaletteConcept>("/palettes/swap", {
      method: "POST",
      body: JSON.stringify({
        palette,
        target_role: targetRole,
        new_hex: newHex,
      }),
    }),

  // Daylight & Materials
  simulateDaylight: (file: File, preset: string) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("preset", preset);
    return request<any>("/daylight/simulate", {
      method: "POST",
      body: formData,
    });
  },

  scoreMaterials: (primaryHex: string, palette?: PaletteConcept) =>
    request<any>("/materials/score", {
      method: "POST",
      body: JSON.stringify({ primary_hex: primaryHex, palette }),
    }),

  // Estimator
  calculateEstimate: (params: {
    room_length_meters: number;
    room_width_meters: number;
    wall_height_meters: number;
    num_doors: number;
    num_windows: number;
    coats: number;
    cost_per_liter_inr?: number;
  }) =>
    request<any>("/estimator/calculate", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  // Timeline
  getTimeline: (projectId: string = "default_project") =>
    request<any>(`/timeline?project_id=${encodeURIComponent(projectId)}`),

  saveTimelineSnapshot: (data: {
    project_id: string;
    label: string;
    palette?: PaletteConcept;
    palette_data?: any;
    notes?: string;
    thumbnail_data?: string;
  }) =>
    request<any>("/timeline", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  rollbackTimeline: (versionId: string) =>
    request<any>("/timeline/rollback", {
      method: "POST",
      body: JSON.stringify({ version_id: versionId }),
    }),

  // Memory & DNA
  favouritePalette: (palette: PaletteConcept, style?: string) =>
    request<any>("/memory/favourite", {
      method: "POST",
      body: JSON.stringify({ palette, style }),
    }),

  rejectPalette: (palette: PaletteConcept) =>
    request<any>("/memory/reject", {
      method: "POST",
      body: JSON.stringify({ palette }),
    }),

  getDNA: () => request<ChromaDNA>("/dna"),

  // Plans & Billing
  getPlans: () => request<any>("/plans"),

  createOrder: (planId: string, billingCycle: string = "monthly") =>
    request<any>("/billing/order", {
      method: "POST",
      body: JSON.stringify({ plan_id: planId, billing_cycle: billingCycle }),
    }),

  verifyPayment: (data: {
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
    plan_id: string;
    billing_cycle?: string;
  }) =>
    request<any>("/billing/verify", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  switchPlan: (data: { plan_id: string; billing_cycle?: string }) =>
    request<any>("/billing/switch-plan", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getCurrentSubscription: () => request<any>("/billing/subscription"),

  // Auth
  register: (data: { email: string; full_name: string; password: string; terms_accepted?: boolean }) =>
    request<any>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: { email: string; password: string }) =>
    request<any>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  logout: () =>
    request<any>("/auth/logout", {
      method: "POST",
    }),

  getMe: () => request<{ authenticated: boolean; user: any }>("/auth/me"),

  requestReset: (email: string) =>
    request<any>("/auth/reset-request", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  confirmReset: (data: { token: string; new_password: string }) =>
    request<any>("/auth/reset-confirm", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // 3D Experience (Modes A, B, C & GLB Export)
  get3DDepthMesh: (file: File, targetHex?: string, resolution: number = 60) => {
    const formData = new FormData();
    formData.append("file", file);
    if (targetHex) formData.append("target_hex", targetHex);
    formData.append("resolution", resolution.toString());
    return request<any>("/3d/depth-mesh", {
      method: "POST",
      body: formData,
    });
  },

  get3DRoomBox: (params: {
    file?: File;
    wall_color?: string;
    ceiling_color?: string;
    floor_color?: string;
    room_width_m?: number;
    room_depth_m?: number;
    room_height_m?: number;
  }) => {
    const formData = new FormData();
    if (params.file) formData.append("file", params.file);
    if (params.wall_color) formData.append("wall_color", params.wall_color);
    if (params.ceiling_color) formData.append("ceiling_color", params.ceiling_color);
    if (params.floor_color) formData.append("floor_color", params.floor_color);
    if (params.room_width_m) formData.append("room_width_m", params.room_width_m.toString());
    if (params.room_depth_m) formData.append("room_depth_m", params.room_depth_m.toString());
    if (params.room_height_m) formData.append("room_height_m", params.room_height_m.toString());
    return request<any>("/3d/room-box", {
      method: "POST",
      body: formData,
    });
  },

  startMultiPhotoScan: (photosCount: number = 15, projectName?: string) =>
    request<any>("/3d/reconstruct-multi", {
      method: "POST",
      body: JSON.stringify({ photos_count: photosCount, project_name: projectName }),
    }),

  get3DJobStatus: (jobId: string) => request<any>(`/3d/job/${jobId}`),

  getGlbExportUrl: () => `${getApiBase()}/3d/export/glb`,

  // GDPR Account Data
  getAccountData: () => request<any>("/account/data"),
  deleteAccount: (confirmation: string) =>
    request<any>("/account/data", {
      method: "DELETE",
      body: JSON.stringify({ confirmation }),
    }),
};
