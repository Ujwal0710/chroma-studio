"""High-level room analysis orchestrator combining vision models and local CV extraction."""
from typing import Optional
from PIL import Image

from models.schemas import RoomAnalysisResult, ExtractedColorAnalysis
from services.vision_provider import perform_room_analysis


def analyze_room_photograph(
    img: Image.Image,
    extracted_analysis: ExtractedColorAnalysis,
    selected_room_type: str = "Automatic Detection",
    selected_style: str = "Automatic Detection",
    override_api_key: Optional[str] = None
) -> RoomAnalysisResult:
    """
    Run structured room analysis using configured vision LLM or resilient local CV fallback.
    """
    return perform_room_analysis(
        img=img,
        extracted_analysis=extracted_analysis,
        selected_room_type=selected_room_type,
        selected_style=selected_style,
        override_api_key=override_api_key
    )
