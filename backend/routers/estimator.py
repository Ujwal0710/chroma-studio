"""Paint & Project Estimator router: Wall area math, can breakdown, and INR budgeting."""
from fastapi import APIRouter
from models.schemas import PaintEstimateInput, PaintEstimateResult
from modules.paint_estimator import estimate_paint_quantity

router = APIRouter(prefix="/estimator", tags=["Paint Estimator"])


@router.post("/calculate", response_model=PaintEstimateResult)
def calculate_paint_estimation(inputs: PaintEstimateInput):
    """Calculate exact wall surface area, deductions, paint liters required, packaging cans breakdown, and INR cost."""
    return estimate_paint_quantity(inputs)
