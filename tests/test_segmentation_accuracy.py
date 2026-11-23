"""Automated Pytest for Phase 3 Accuracy Targets.

Enforces:
- Mean Wall IoU >= 0.88
- Min Wall IoU >= 0.70
- Lightness Correlation r >= 0.95
"""

import pytest
from tests.segmentation_eval.evaluate_segmentation import run_full_evaluation


def test_segmentation_and_recolour_accuracy_targets():
    report = run_full_evaluation()
    assert report["mean_iou"] >= 0.88, f"Mean Wall IoU must be >= 0.88, got {report['mean_iou']:.4f}"
    assert report["min_iou"] >= 0.70, f"Min Wall IoU must be >= 0.70, got {report['min_iou']:.4f}"
    assert report["mean_corr"] >= 0.95, f"Lightness correlation must be >= 0.95, got {report['mean_corr']:.4f}"
