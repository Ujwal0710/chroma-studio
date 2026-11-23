export interface ColorSwatch {
  hex: string;
  rgb: [number, number, number];
  name?: string;
  percentage?: number;
  role?: string;
  cielab?: [number, number, number];
  hsv?: [number, number, number];
  luminance?: number;
  temperature?: string;
  saturation_category?: string;
  description?: string;
  delta_e?: number;
}

export interface PaletteConcept {
  id: string;
  name: string;
  concept_category?: string;
  harmony_type: string;
  description: string;
  atmosphere?: string;
  primary_wall: ColorSwatch;
  secondary_wall: ColorSwatch;
  accent: ColorSwatch;
  trim: ColorSwatch;
  proportions?: Record<string, string>;
  design_rationale?: string;
  furniture_flooring_compatibility?: string;
  heuristic_score?: number;
  score_breakdown?: Record<string, number>;
  colors: ColorSwatch[];
}

export interface ExtractedColorAnalysis {
  dominant_colors: ColorSwatch[];
  overall_brightness: number;
  overall_temperature_tendency: string;
  mean_saturation: number;
  neutral_count: number;
  warm_count: number;
  cool_count: number;
}

export interface RoomAnalysisResult {
  detected_room_type: string;
  detected_style: string;
  detected_materials: string[];
  lighting_description: string;
  design_challenges: string[];
  wall_flooring_notes: string;
}

export interface RoomAnalysisResponse {
  status: string;
  metadata?: any;
  image_preview?: string;
  preview_image?: string;
  dominant_tones?: ExtractedColorAnalysis;
  room_analysis?: RoomAnalysisResult;
  filename?: string;
  dimensions?: [number, number];
  color_count?: number;
  tones?: ColorSwatch[];
  lighting?: {
    mean_luminance: number;
    dynamic_range: number;
    lighting_condition: string;
    description: string;
  };
  typology?: {
    aspect_ratio: number;
    orientation: string;
    estimated_room_type: string;
  };
  dominant_temperature?: string;
}

export interface WallSegmentationResponse {
  status: string;
  mask_overlay: string;
  overlay_preview?: string;
  mask_only?: string;
  mask_png?: string;
  metadata: {
    wall_pixel_count: number;
    total_pixel_count: number;
    wall_coverage_percent: number;
    bounding_box?: [number, number, number, number];
    algorithm?: string;
    sensitivity?: number;
  };
}

export interface WallRecolourResponse {
  status: string;
  recoloured_image: string;
  target_color: {
    hex: string;
    rgb: [number, number, number];
  };
  mask_metadata: {
    wall_pixel_count: number;
    total_pixel_count: number;
    wall_coverage_percent: number;
  };
}

export interface DaylightSimResponse {
  status: string;
  condition?: string;
  preset?: string;
  target_kelvin?: number;
  simulated_image: string;
  description?: string;
}

export interface MaterialScore {
  name: string;
  category: string;
  score: number;
  status: "Harmonious" | "Balanced" | "Clashing";
  delta_e: number;
  notes: string;
  suggested_texture: string;
}

export interface MaterialsResponse {
  status: string;
  palette_primary_hex: string;
  scores: MaterialScore[];
  summary: string;
}

export interface PaintEstimateResult {
  gross_wall_area_sqm: number;
  deductions_sqm: number;
  net_wall_area_sqm: number;
  total_coated_area_sqm: number;
  paint_liters_required: number;
  recommended_cans_breakdown: Record<string, number>;
  estimated_cost_inr: number;
  estimator_disclaimer: string;
}

export interface ChromaDNA {
  user_id: string;
  signature_name: string;
  dominant_family: string;
  contrast_level: string;
  temperature_bias: string;
  material_affinity: string[];
  preferred_styles: string[];
  signature_swatches: ColorSwatch[];
}

export interface TimelineSnapshot {
  id: string;
  project_id: string;
  version_num: number;
  label: string;
  timestamp: string;
  palette_data: Record<string, any>;
  notes: string;
  thumbnail_data?: string;
}

export interface UserAccount {
  id: string;
  email: string;
  full_name: string;
  role: string;
}
