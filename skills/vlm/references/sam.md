# SAM: Segment Anything Model

> **Generated**: 2025-12-21
> **Sources current as of**: December 2024
> **Version**: 1.0

---

## Executive Summary / TLDR

**SAM (Segment Anything Model)** is Meta AI's foundation model for image segmentation, released in April 2023. It can segment any object in any image using points, boxes, or text prompts, achieving zero-shot generalization to new objects and domains without additional training.

**Key capabilities:**
- **Point prompts**: Click on any point to segment the object
- **Box prompts**: Draw a bounding box to segment within
- **Mask prompts**: Refine existing masks
- **Text prompts**: Segment objects by description (SAM 2 / Grounded-SAM)
- **Automatic segmentation**: Segment everything in an image

**Model versions:**
- **SAM** (Apr 2023): Original, image-only
- **SAM 2** (Jul 2024): Adds video segmentation, faster, more accurate
- **EfficientSAM**: Distilled, 20x faster
- **FastSAM**: YOLO-based alternative
- **MobileSAM**: Mobile-optimized

**Recommendation**: Use SAM 2 for accuracy, FastSAM/EfficientSAM for speed.

---

## Model Architecture

### SAM Overview

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│   Image     │────▶│  Image Encoder  │────▶│   Image     │
│             │     │  (ViT-H/L/B)    │     │  Embeddings │
└─────────────┘     └─────────────────┘     └─────────────┘
                                                   │
                                                   ▼
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│   Prompt    │────▶│ Prompt Encoder  │────▶│   Prompt    │
│(point/box)  │     │                 │     │  Embeddings │
└─────────────┘     └─────────────────┘     └─────────────┘
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │   Mask      │
                                            │  Decoder    │
                                            └─────────────┘
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │  Output     │
                                            │  Masks      │
                                            └─────────────┘
```

### Model Variants

| Model | Image Encoder | Params | Speed | Quality |
|-------|---------------|--------|-------|---------|
| SAM-B | ViT-B | 91M | Fast | Good |
| SAM-L | ViT-L | 308M | Medium | Very Good |
| SAM-H | ViT-H | 636M | Slow | Excellent |
| SAM 2-T | Hiera-T | 38M | Very Fast | Good |
| SAM 2-S | Hiera-S | 46M | Fast | Good |
| SAM 2-B+ | Hiera-B+ | 80M | Medium | Very Good |
| SAM 2-L | Hiera-L | 224M | Slow | Excellent |

---

## Installation & Setup

### SAM (Original)

```bash
pip install git+https://github.com/facebookresearch/segment-anything.git
pip install opencv-python matplotlib

# Download checkpoints
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
```

### SAM 2

```bash
pip install git+https://github.com/facebookresearch/sam2.git

# Download SAM 2 checkpoints
# sam2.1_hiera_tiny.pt
# sam2.1_hiera_small.pt
# sam2.1_hiera_base_plus.pt
# sam2.1_hiera_large.pt
```

### Alternatives

```bash
# FastSAM (YOLO-based, very fast)
pip install ultralytics

# EfficientSAM (distilled, balanced)
pip install git+https://github.com/yformer/EfficientSAM.git

# MobileSAM (mobile-optimized)
pip install git+https://github.com/ChaoningZhang/MobileSAM.git
```

---

## Basic Usage

### Point Prompt

```python
import numpy as np
from segment_anything import sam_model_registry, SamPredictor
from PIL import Image

# Load model
sam = sam_model_registry["vit_h"](checkpoint="sam_vit_h_4b8939.pth")
sam.to("cuda")

predictor = SamPredictor(sam)

# Load and set image
image = np.array(Image.open("image.jpg"))
predictor.set_image(image)

# Segment with point prompt
input_point = np.array([[500, 375]])  # x, y coordinates
input_label = np.array([1])  # 1 = foreground, 0 = background

masks, scores, logits = predictor.predict(
    point_coords=input_point,
    point_labels=input_label,
    multimask_output=True  # Returns 3 masks
)

# Use best mask
best_mask = masks[scores.argmax()]
```

### Box Prompt

```python
# Segment with bounding box
input_box = np.array([100, 100, 400, 400])  # x1, y1, x2, y2

masks, scores, logits = predictor.predict(
    box=input_box,
    multimask_output=False
)
```

### Multiple Points

```python
# Multiple points for better segmentation
input_points = np.array([
    [500, 375],   # Foreground point 1
    [600, 400],   # Foreground point 2
    [200, 100]    # Background point
])
input_labels = np.array([1, 1, 0])  # 1=foreground, 0=background

masks, scores, logits = predictor.predict(
    point_coords=input_points,
    point_labels=input_labels,
    multimask_output=True
)
```

### Automatic Mask Generation

```python
from segment_anything import SamAutomaticMaskGenerator

mask_generator = SamAutomaticMaskGenerator(sam)

# Generate all masks
masks = mask_generator.generate(image)

# Each mask is a dict with:
# - 'segmentation': binary mask
# - 'area': pixel area
# - 'bbox': bounding box
# - 'predicted_iou': model's IoU prediction
# - 'stability_score': mask stability

for mask in masks:
    print(f"Area: {mask['area']}, IoU: {mask['predicted_iou']:.2f}")
```

### Configurable Auto Mask Generation

```python
mask_generator = SamAutomaticMaskGenerator(
    model=sam,
    points_per_side=32,          # Grid density
    pred_iou_thresh=0.88,        # IoU threshold
    stability_score_thresh=0.95, # Stability threshold
    crop_n_layers=1,             # Multi-scale crops
    crop_n_points_downscale_factor=2,
    min_mask_region_area=100     # Filter small masks
)
```

---

## SAM 2 (Video Support)

### Video Segmentation

```python
import torch
from sam2.build_sam import build_sam2_video_predictor

# Load SAM 2
checkpoint = "sam2.1_hiera_large.pt"
model_cfg = "configs/sam2.1/sam2.1_hiera_l.yaml"
predictor = build_sam2_video_predictor(model_cfg, checkpoint)

# Initialize with video
inference_state = predictor.init_state(video_path="video.mp4")

# Add prompt on first frame
predictor.add_new_points_or_box(
    inference_state=inference_state,
    frame_idx=0,
    obj_id=1,
    points=np.array([[100, 100]], dtype=np.float32),
    labels=np.array([1], dtype=np.int32)
)

# Propagate through video
video_segments = {}
for frame_idx, object_ids, mask_logits in predictor.propagate_in_video(inference_state):
    video_segments[frame_idx] = {
        obj_id: (mask_logits[i] > 0.0).cpu().numpy()
        for i, obj_id in enumerate(object_ids)
    }
```

### SAM 2 for Images

```python
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

sam2 = build_sam2(model_cfg, checkpoint)
predictor = SAM2ImagePredictor(sam2)

# Same API as SAM 1
predictor.set_image(image)
masks, scores, logits = predictor.predict(
    point_coords=input_point,
    point_labels=input_label
)
```

---

## Grounded-SAM (Text Prompts)

Combine SAM with Grounding DINO for text-based segmentation:

```python
from groundingdino.util.inference import load_model, predict
from segment_anything import sam_model_registry, SamPredictor
import torch

# Load Grounding DINO
grounding_dino = load_model(
    "GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py",
    "groundingdino_swint_ogc.pth"
)

# Load SAM
sam = sam_model_registry["vit_h"](checkpoint="sam_vit_h_4b8939.pth")
sam_predictor = SamPredictor(sam)

def segment_with_text(image, text_prompt, box_threshold=0.3, text_threshold=0.25):
    """Segment objects described by text."""

    # Get bounding boxes from Grounding DINO
    boxes, logits, phrases = predict(
        model=grounding_dino,
        image=image,
        caption=text_prompt,
        box_threshold=box_threshold,
        text_threshold=text_threshold
    )

    # Convert boxes to SAM format
    sam_predictor.set_image(image)

    masks_list = []
    for box in boxes:
        masks, scores, _ = sam_predictor.predict(
            box=box.cpu().numpy(),
            multimask_output=False
        )
        masks_list.append(masks[0])

    return masks_list, boxes, phrases

# Usage
masks, boxes, labels = segment_with_text(
    image,
    "person. dog. cat."  # Period-separated labels
)
```

---

## Fast Alternatives

### FastSAM (YOLO-based)

```python
from ultralytics import FastSAM

model = FastSAM("FastSAM-x.pt")  # or FastSAM-s.pt

# Everything mode
results = model(
    "image.jpg",
    device="cuda",
    retina_masks=True,
    imgsz=1024,
    conf=0.4,
    iou=0.9
)

# Point prompt
results = model(
    "image.jpg",
    points=[[200, 300]],
    labels=[1]
)

# Box prompt
results = model(
    "image.jpg",
    bboxes=[[100, 100, 400, 400]]
)

# Text prompt (requires CLIP)
results = model(
    "image.jpg",
    texts="a cat"
)
```

### EfficientSAM

```python
from efficient_sam.build_efficient_sam import build_efficient_sam_vits
import torch

model = build_efficient_sam_vits()
model.eval()
model.to("cuda")

# Similar API to SAM
# ~20x faster than ViT-H SAM
```

### MobileSAM

```python
from mobile_sam import sam_model_registry, SamPredictor

mobile_sam = sam_model_registry["vit_t"](checkpoint="mobile_sam.pt")
mobile_sam.to("cuda")

predictor = SamPredictor(mobile_sam)
# Same API as SAM, ~10x faster
```

---

## Performance Comparison

| Model | Speed (A100) | Quality | VRAM | Use Case |
|-------|--------------|---------|------|----------|
| SAM ViT-H | 2.3s | Excellent | 8GB | Best quality |
| SAM ViT-B | 0.3s | Good | 3GB | Balanced |
| SAM 2-L | 0.5s | Excellent | 6GB | Video, quality |
| SAM 2-T | 0.1s | Good | 2GB | Video, fast |
| FastSAM | 0.04s | Good | 2GB | Real-time |
| EfficientSAM | 0.1s | Very Good | 2GB | Balanced |
| MobileSAM | 0.05s | Good | 1GB | Mobile/edge |

### 3090 Performance

| Model | Inference Time | VRAM |
|-------|----------------|------|
| SAM ViT-H | ~3s | 8GB |
| SAM ViT-B | ~0.4s | 3GB |
| SAM 2-L | ~0.6s | 6GB |
| FastSAM-x | ~0.06s | 3GB |

---

## Integration Patterns

### With YOLO (Detect then Segment)

```python
from ultralytics import YOLO
from segment_anything import sam_model_registry, SamPredictor

# Load models
yolo = YOLO("yolov8m.pt")
sam = sam_model_registry["vit_b"](checkpoint="sam_vit_b_01ec64.pth")
sam_predictor = SamPredictor(sam)

def detect_and_segment(image):
    """Detect objects with YOLO, segment with SAM."""
    # Detect
    results = yolo(image)[0]

    # Set image for SAM
    sam_predictor.set_image(image)

    segmentations = []
    for box in results.boxes:
        # Get SAM mask for each detection
        bbox = box.xyxy[0].cpu().numpy()
        masks, scores, _ = sam_predictor.predict(
            box=bbox,
            multimask_output=False
        )
        segmentations.append({
            'class': yolo.names[int(box.cls[0])],
            'confidence': float(box.conf[0]),
            'mask': masks[0],
            'bbox': bbox
        })

    return segmentations
```

### With RAM++ (Tag then Segment)

```python
# Use RAM++ for tags, SAM for segmentation
# RAM++ provides semantic tags, SAM provides masks
```

### FastAPI Service

```python
from fastapi import FastAPI, UploadFile
from segment_anything import sam_model_registry, SamPredictor
from PIL import Image
import numpy as np
import io

app = FastAPI()

sam = sam_model_registry["vit_b"](checkpoint="sam_vit_b_01ec64.pth")
predictor = SamPredictor(sam)

@app.post("/segment")
async def segment(
    file: UploadFile,
    x: int,
    y: int
):
    contents = await file.read()
    image = np.array(Image.open(io.BytesIO(contents)))

    predictor.set_image(image)

    masks, scores, _ = predictor.predict(
        point_coords=np.array([[x, y]]),
        point_labels=np.array([1]),
        multimask_output=False
    )

    # Return mask as base64 or coordinates
    return {"mask": masks[0].tolist()}
```

---

## Use Cases

### When to Use SAM

- **Interactive segmentation**: User clicks to segment
- **Zero-shot segmentation**: Segment novel objects
- **Annotation tools**: Create training data
- **Image editing**: Cut out objects
- **Video tracking**: Track objects through frames (SAM 2)

### When NOT to Use SAM

- **Need class labels**: SAM doesn't classify, combine with detector
- **Real-time video**: Use FastSAM or dedicated trackers
- **Semantic segmentation**: Use dedicated semantic seg models
- **Simple detection only**: Use YOLO instead

---

## Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **No class labels** | Just segments, doesn't identify | Combine with YOLO/RAM++ |
| **Slow for ViT-H** | ~2-3s per image | Use ViT-B, FastSAM, or SAM 2-T |
| **Prompt required** | Needs point/box input | Use auto-mask for everything |
| **Memory intensive** | Large image encoder | Batch carefully, use smaller variant |

---

## Source Appendix

| # | Source | Date | Type |
|---|--------|------|------|
| 1 | [SAM Paper - Segment Anything](https://arxiv.org/abs/2304.02643) | Apr 2023 | Primary |
| 2 | [SAM GitHub](https://github.com/facebookresearch/segment-anything) | 2023 | Primary |
| 3 | [SAM 2 Paper](https://arxiv.org/abs/2408.00714) | Jul 2024 | Primary |
| 4 | [SAM 2 GitHub](https://github.com/facebookresearch/sam2) | 2024 | Primary |
| 5 | [FastSAM](https://github.com/CASIA-IVA-Lab/FastSAM) | 2023 | Secondary |
| 6 | [Grounded-SAM](https://github.com/IDEA-Research/Grounded-Segment-Anything) | 2023 | Secondary |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-21 | Initial version |
