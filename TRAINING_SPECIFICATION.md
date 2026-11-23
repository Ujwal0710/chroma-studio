# Wall-vs-Object Segmentation Model Training Specification

## 1. Datasets & Licences
- **ADE20K Indoor Subset**:
  - Scenes: `living_room`, `bedroom`, `kitchen`, `dining_room`, `home_office`
  - License: BSD 3-Clause / CC-BY-NC 4.0 (Academic and non-commercial research)
  - URL: http://data.csail.mit.edu/places/ADEchallenge/ADEChallengeData2016.zip
- **NYU Depth V2 Indoor Segmentation**:
  - Scenes: 1,449 densely labelled indoor room photographs
  - License: MIT License (Free commercial & research use)
  - URL: https://cs.nyu.edu/~silberman/datasets/nyu_depth_v2.html
- **Custom Studio User-Labelled Dataset**:
  - Path: `data/custom/` (Scanned dynamically for `.jpg` + `.mask.png` pairs)
  - Active user corrections from `/rooms/mask/refine` are appended here.

## 2. Task-Specific Collapsed Classes (7 Classes)
| Class ID | Target Name | Sources in ADE20K / NYU |
| :--- | :--- | :--- |
| `0` | Other / Background | Unclassified, exterior, misc |
| `1` | Wall | `wall` |
| `2` | Ceiling | `ceiling` |
| `3` | Floor | `floor`, `rug`, `carpet` |
| `4` | Door | `door`, `screen door` |
| `5` | Window | `windowpane`, `window` |
| `6` | Furniture & Wall Objects | `sofa`, `chair`, `cabinet`, `table`, `bed`, `shelf`, `painting`, `poster`, `television receiver`, `monitor`, `sconce`, `light`, `clock`, `radiator`, `curtain`, `plant` |

## 3. Loss Function: Boundary-Aware Loss
$$\mathcal{L} = \mathcal{L}_{CE} + 0.5 \cdot \mathcal{L}_{\text{MulticlassDice}} + 1.0 \cdot \mathcal{L}_{\text{Boundary}}$$
where $\mathcal{L}_{\text{Boundary}}$ calculates Dice loss specifically along the 3-pixel morphological dilation of wall-furniture edges, forcing zero tolerance for furniture bleed.

## 4. Execution Commands (GPU Environment)
To run fine-tuning on a machine with PyTorch and CUDA:
```bash
# 1. Install prerequisites in a PyTorch-compatible Python environment (e.g. Python 3.10 / 3.11):
pip install torch torchvision torchaudio transformers onnx onnxruntime albumentations

# 2. Run the fine-tuning pipeline:
python scripts/train_wall_object_segmenter.py \
    --data_dir data/ade20k \
    --custom_dir data/custom \
    --epochs 30 \
    --batch_size 8 \
    --learning_rate 5e-5 \
    --output_model data/models/segformer/model_finetuned.onnx \
    --device cuda
```
Estimated training duration: ~2.5 hours on NVIDIA RTX 3080 / A10G (30 epochs).

## 5. Current Fallback Deployment
In the current runtime environment (Python 3.14 on Windows), pre-built PyTorch C++ wheels are pending PyPI release. 
The system deploys the **ADE20K SegFormer Model with Inference-Time Edge Snapping & Obstacle Suppression Engine**:
- Fast Guided Filter ($\epsilon = 10^{-4}$) boundary edge snapping
- 59-class obstacle exclusion (subtraction of all wall-mounted decor, electronics, curtains, and furniture)
- High-resolution probability upsampling (eliminating 4x4 block quantization)
- Promptable tap/brush manual correction with automatic logging to `data/corrections_log/`
