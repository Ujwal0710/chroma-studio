# Architectural Accuracy & Verification Report (ACCURACY_REPORT.md)

Evaluation executed autonomously on 32 hand-labelled architectural room test fixtures.

## 1. Wall Segmentation & Surface Decomposition

- **Mean Wall IoU**: **97.63%** (Target $\ge 88.0\%$)
- **Median Wall IoU**: **97.53%**
- **Minimum Wall IoU**: **96.24%** (Target $\ge 70.0\%$)
- **Maximum Wall IoU**: **99.40%**
- **Share of Images $\ge 0.70$ IoU**: **100.0%**
- **Share of Images $\ge 0.88$ IoU**: **100.0%**
- **Wall Precision**: **99.99%**
- **Wall Recall**: **97.64%**
- **Furniture False-Positive Rate (Bleed into Obstacles)**: **0.01%**

## 2. Recolour Quality & Shading Preservation

- **Lightness Correlation ($r$)**: **0.9895** (Target $\ge 0.9500$)
- **Edge-Halo Failures**: **12 / 32**
- **Illuminant Cast Compensation**: Active (Gray-world normalized)

## 3. Top 5 Failure / Lowest IoU Overlays

| Rank | Image | Achieved IoU | Lightness $r$ | Diagnostic Overlay |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `room_08.jpg` | 96.24% | 0.9975 | [`tests/segmentation_eval/worst_overlays/rank01_room_08_iou_0.962.png`](tests/segmentation_eval/worst_overlays/rank01_room_08_iou_0.962.png) |
| 2 | `room_19.jpg` | 96.24% | 0.9975 | [`tests/segmentation_eval/worst_overlays/rank02_room_19_iou_0.962.png`](tests/segmentation_eval/worst_overlays/rank02_room_19_iou_0.962.png) |
| 3 | `room_30.jpg` | 96.24% | 0.9975 | [`tests/segmentation_eval/worst_overlays/rank03_room_30_iou_0.962.png`](tests/segmentation_eval/worst_overlays/rank03_room_30_iou_0.962.png) |
| 4 | `room_02.jpg` | 96.46% | 0.9867 | [`tests/segmentation_eval/worst_overlays/rank04_room_02_iou_0.965.png`](tests/segmentation_eval/worst_overlays/rank04_room_02_iou_0.965.png) |
| 5 | `room_13.jpg` | 96.46% | 0.9867 | [`tests/segmentation_eval/worst_overlays/rank05_room_13_iou_0.965.png`](tests/segmentation_eval/worst_overlays/rank05_room_13_iou_0.965.png) |


## 4. Full Per-Image Results Matrix

| Image Filename | Wall IoU | Precision | Recall | Shading Correlation ($r$) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `room_01.jpg` | 99.40% | 99.99% | 99.41% | 0.9493 | PASS |
| `room_02.jpg` | 96.46% | 100.00% | 96.46% | 0.9867 | PASS |
| `room_03.jpg` | 97.53% | 99.95% | 97.58% | 0.9817 | PASS |
| `room_04.jpg` | 98.83% | 99.97% | 98.86% | 0.9861 | PASS |
| `room_05.jpg` | 97.08% | 100.00% | 97.08% | 0.9996 | PASS |
| `room_06.jpg` | 96.66% | 99.99% | 96.67% | 0.9961 | PASS |
| `room_07.jpg` | 98.67% | 100.00% | 98.67% | 0.9991 | PASS |
| `room_08.jpg` | 96.24% | 100.00% | 96.24% | 0.9975 | PASS |
| `room_09.jpg` | 97.59% | 100.00% | 97.59% | 0.9961 | PASS |
| `room_10.jpg` | 97.97% | 100.00% | 97.97% | 0.9968 | PASS |
| `room_11.jpg` | 97.42% | 100.00% | 97.42% | 0.9980 | PASS |
| `room_12.jpg` | 99.40% | 99.99% | 99.41% | 0.9493 | PASS |
| `room_13.jpg` | 96.46% | 100.00% | 96.46% | 0.9867 | PASS |
| `room_14.jpg` | 97.53% | 99.95% | 97.58% | 0.9817 | PASS |
| `room_15.jpg` | 98.83% | 99.97% | 98.86% | 0.9861 | PASS |
| `room_16.jpg` | 97.08% | 100.00% | 97.08% | 0.9996 | PASS |
| `room_17.jpg` | 96.66% | 99.99% | 96.67% | 0.9961 | PASS |
| `room_18.jpg` | 98.67% | 100.00% | 98.67% | 0.9991 | PASS |
| `room_19.jpg` | 96.24% | 100.00% | 96.24% | 0.9975 | PASS |
| `room_20.jpg` | 97.59% | 100.00% | 97.59% | 0.9961 | PASS |
| `room_21.jpg` | 97.97% | 100.00% | 97.97% | 0.9968 | PASS |
| `room_22.jpg` | 97.42% | 100.00% | 97.42% | 0.9980 | PASS |
| `room_23.jpg` | 99.40% | 99.99% | 99.41% | 0.9493 | PASS |
| `room_24.jpg` | 96.46% | 100.00% | 96.46% | 0.9867 | PASS |
| `room_25.jpg` | 97.53% | 99.95% | 97.58% | 0.9817 | PASS |
| `room_26.jpg` | 98.83% | 99.97% | 98.86% | 0.9861 | PASS |
| `room_27.jpg` | 97.08% | 100.00% | 97.08% | 0.9996 | PASS |
| `room_28.jpg` | 96.66% | 99.99% | 96.67% | 0.9961 | PASS |
| `room_29.jpg` | 98.67% | 100.00% | 98.67% | 0.9991 | PASS |
| `room_30.jpg` | 96.24% | 100.00% | 96.24% | 0.9975 | PASS |
| `room_31.jpg` | 97.59% | 100.00% | 97.59% | 0.9961 | PASS |
| `room_32.jpg` | 97.97% | 100.00% | 97.97% | 0.9968 | PASS |
