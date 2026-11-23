"""Smart Paint Estimator: Practical mathematical room paint quantity and cost estimator."""
import math
from models.schemas import PaintEstimateInput, PaintEstimateResult

STANDARD_DOOR_AREA_SQM = 1.89   # 0.9m x 2.1m standard interior doorway
STANDARD_WINDOW_AREA_SQM = 1.44 # 1.2m x 1.2m standard window opening
WASTAGE_MARGIN_PERCENT = 0.10   # 10% safety margin for brush absorption, tray residue, and touch-ups


def estimate_paint_quantity(inputs: PaintEstimateInput) -> PaintEstimateResult:
    """
    Calculate practical paint requirements from geometric room measurements.
    Strictly rule-based calculations without fabricated prices or secret formulas.
    """
    effective_coats = inputs.num_coats if inputs.num_coats is not None else inputs.coats

    if inputs.total_wall_area_sqft is not None and inputs.total_wall_area_sqft > 0:
        # Direct sqft conversion (1 sqft ≈ 0.092903 sqm)
        gross_wall_area = inputs.total_wall_area_sqft * 0.092903
        doors_deduction = inputs.num_doors * STANDARD_DOOR_AREA_SQM
        windows_deduction = inputs.num_windows * STANDARD_WINDOW_AREA_SQM
        total_deductions = doors_deduction + windows_deduction
    else:
        perimeter = 2.0 * (inputs.room_length_meters + inputs.room_width_meters)
        gross_wall_area = perimeter * inputs.wall_height_meters
        doors_deduction = inputs.num_doors * STANDARD_DOOR_AREA_SQM
        windows_deduction = inputs.num_windows * STANDARD_WINDOW_AREA_SQM
        total_deductions = doors_deduction + windows_deduction

    # Net wall surface to be painted
    net_wall_area = max(0.0, gross_wall_area - total_deductions)
    total_coated_area = net_wall_area * effective_coats
    
    # Raw litres required
    coverage = max(1.0, inputs.coverage_sqm_per_liter)
    raw_liters = total_coated_area / coverage
    
    # Total with 10% architectural wastage margin
    liters_with_margin = raw_liters * (1.0 + WASTAGE_MARGIN_PERCENT)
    total_liters = round(liters_with_margin, 2)
    
    # Packaging recommendations: standard Indian paint tin sizes (10L, 4L, 1L)
    remaining_liters = math.ceil(total_liters)
    cans_10l = remaining_liters // 10
    rem = remaining_liters % 10
    cans_4l = rem // 4
    rem = rem % 4
    cans_1l = rem
    
    cans_breakdown = {
        "10-Litre Buckets": cans_10l,
        "4-Litre Tins": cans_4l,
        "1-Litre Cans": cans_1l
    }
    
    # Optional cost estimate if user provided rate
    estimated_cost = None
    if inputs.cost_per_liter_inr and inputs.cost_per_liter_inr > 0:
        # Based on purchased whole tin volume
        purchased_volume = (cans_10l * 10) + (cans_4l * 4) + (cans_1l * 1)
        estimated_cost = round(purchased_volume * inputs.cost_per_liter_inr, 2)
        
    return PaintEstimateResult(
        gross_wall_area_sqm=round(gross_wall_area, 2),
        deductions_sqm=round(total_deductions, 2),
        net_wall_area_sqm=round(net_wall_area, 2),
        total_coated_area_sqm=round(total_coated_area, 2),
        paint_liters_required=total_liters,
        recommended_cans_breakdown=cans_breakdown,
        estimated_cost_inr=estimated_cost
    )
