"""Live Camera Studio: Continuous webcam streaming, WebRTC video processing, and snapshot capture."""
import threading
import time
from typing import Optional, Tuple, Dict, Any
import numpy as np
from PIL import Image
import cv2

# Safe WebRTC imports
try:
    from streamlit_webrtc import VideoTransformerBase
    import av
    HAS_WEBRTC = True
except ImportError:
    HAS_WEBRTC = False
    VideoTransformerBase = object

# Default public STUN server for WebRTC ICE negotiation
RTC_CONFIG = {
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
} if HAS_WEBRTC else {}


class ThreadSafeFrameHolder:
    """Thread-safe frame buffer holding the latest live video frame."""
    def __init__(self):
        self._lock = threading.Lock()
        self._frame: Optional[np.ndarray] = None
        self._timestamp: float = 0.0
        self._fps_count: int = 0
        self._last_fps_time: float = time.time()
        self._current_fps: float = 0.0

    def set_frame(self, frame_bgr: np.ndarray) -> None:
        with self._lock:
            self._frame = frame_bgr.copy()
            self._timestamp = time.time()
            self._fps_count += 1
            now = time.time()
            if now - self._last_fps_time >= 1.0:
                self._current_fps = self._fps_count / (now - self._last_fps_time)
                self._fps_count = 0
                self._last_fps_time = now

    def get_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            if self._frame is None:
                return None
            return self._frame.copy()

    def get_pil_image(self) -> Optional[Image.Image]:
        with self._lock:
            if self._frame is None:
                return None
            rgb = cv2.cvtColor(self._frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb)

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "has_frame": self._frame is not None,
                "fps": round(self._current_fps, 1),
                "timestamp": self._timestamp,
                "resolution": (self._frame.shape[1], self._frame.shape[0]) if self._frame is not None else (0, 0)
            }


class LiveVideoTransformer(VideoTransformerBase):
    """
    WebRTC Video Processor.
    Processes live camera frames, applies optional overlay or analysis,
    and shares frames thread-safely with Streamlit.
    """
    def __init__(self):
        self.frame_holder: Optional[ThreadSafeFrameHolder] = None
        self.overlay_mode: str = "none"  # 'none', 'wall_preview', 'intelligence'
        self.target_rgb: Tuple[int, int, int] = (205, 125, 85)
        self.overlay_intensity: float = 0.80
        self.frame_skip: int = 2  # Process every Nth frame for performance
        self._frame_counter: int = 0
        self._cached_mask: Optional[np.ndarray] = None

    def transform(self, frame: Any) -> Any:
        try:
            img_bgr = frame.to_ndarray(format="bgr24")
        except Exception:
            return frame

        self._frame_counter += 1

        # Store latest original frame thread-safely
        if self.frame_holder is not None:
            self.frame_holder.set_frame(img_bgr)

        # Optimization: Apply heavy transformations only on selected frames
        if self.overlay_mode == "none":
            return av.VideoFrame.from_ndarray(img_bgr, format="bgr24")

        # Live Wall Colour Preview overlay mode
        if self.overlay_mode == "wall_preview":
            processed_bgr = self._apply_quick_wall_overlay(img_bgr)
            return av.VideoFrame.from_ndarray(processed_bgr, format="bgr24")

        return av.VideoFrame.from_ndarray(img_bgr, format="bgr24")

    def _apply_quick_wall_overlay(self, bgr_arr: np.ndarray) -> np.ndarray:
        """
        Lightweight real-time wall recolouring for video stream.
        Optimized with downscaled mask computation and luminance preservation.
        """
        h, w, _ = bgr_arr.shape
        # Recompute mask every 3 frames to maintain 24+ FPS
        if self._frame_counter % self.frame_skip == 0 or self._cached_mask is None:
            small_bgr = cv2.resize(bgr_arr, (w // 2, h // 2), interpolation=cv2.INTER_NEAREST)
            gray = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2GRAY)
            # Find wall candidate: upper 70% with low-to-medium gradient
            sobel = cv2.Sobel(gray, cv2.CV_8U, 1, 1, ksize=3)
            _, mask_inv = cv2.threshold(sobel, 35, 255, cv2.THRESH_BINARY_INV)
            # Remove floor region
            mask_inv[int(mask_inv.shape[0] * 0.75):, :] = 0
            self._cached_mask = cv2.resize(mask_inv, (w, h), interpolation=cv2.INTER_LINEAR)

        mask = self._cached_mask > 0
        if not np.any(mask):
            return bgr_arr

        # Luminance-preserving blend
        out = bgr_arr.copy()
        t_b, t_g, t_r = self.target_rgb[2], self.target_rgb[1], self.target_rgb[0]

        # Calculate local lightness ratio
        orig_gray = cv2.cvtColor(bgr_arr, cv2.COLOR_BGR2GRAY).astype(np.float32)
        lum_norm = np.clip(orig_gray / 180.0, 0.4, 1.4)

        blend_alpha = float(self.overlay_intensity)
        target_b = np.clip(t_b * lum_norm, 0, 255).astype(np.uint8)
        target_g = np.clip(t_g * lum_norm, 0, 255).astype(np.uint8)
        target_r = np.clip(t_r * lum_norm, 0, 255).astype(np.uint8)

        out[mask, 0] = (out[mask, 0] * (1.0 - blend_alpha) + target_b[mask] * blend_alpha).astype(np.uint8)
        out[mask, 1] = (out[mask, 1] * (1.0 - blend_alpha) + target_g[mask] * blend_alpha).astype(np.uint8)
        out[mask, 2] = (out[mask, 2] * (1.0 - blend_alpha) + target_r[mask] * blend_alpha).astype(np.uint8)

        return out


def is_webrtc_available() -> bool:
    """Return whether streamlit-webrtc is installed and active in this environment."""
    return HAS_WEBRTC
