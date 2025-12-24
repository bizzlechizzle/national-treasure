---
name: vlm
description: Specialized Vision Model integration guide for adding computer vision capabilities to applications. Covers task-specific models for detection (YOLO), segmentation (SAM), tagging (RAM++), embeddings (CLIP/SigLIP), multi-task (Florence-2), and depth estimation. Optimized for RTX 3090 (24GB VRAM). Focuses on practical model selection and deployment.
---

# Specialized Vision Models Integration Guide v0.1.0

Add computer vision capabilities to your applications with task-specific models.

## Hardware Context

This guide is optimized for **RTX 3090 (24GB VRAM)**.

| VRAM | What Fits | Examples |
|------|-----------|----------|
| 24GB | All models in this guide | YOLO, SAM, Florence-2, RAM++ |
| 8GB | Most models | YOLO, SAM-B, SigLIP |
| 4GB | Lightweight models | YOLO-n/s, FastSAM, CLIP |

---

## VLM vs VLLM Distinction

This skill covers **specialized vision models** (VLM):

| Category | Models | Use Case |
|----------|--------|----------|
| **VLM (this skill)** | YOLO, SAM, CLIP, Florence-2, RAM++ | Specific vision tasks |
| **VLLM (separate skill)** | LLaVA, Qwen2-VL, GPT-4V | Conversational image understanding |

**When to use VLM**: Need detection, segmentation, embeddings, tagging, or multi-task vision.
**When to use VLLM**: Need to ask questions about images in natural language.

---

## Quick Decision Matrix

```
What do you need to do?
│
├─► DETECT objects → YOLO (references/yolo.md)
│   └─► Bounding boxes, real-time, video
│
├─► SEGMENT objects → SAM (references/sam.md)
│   └─► Pixel-level masks, interactive, zero-shot
│
├─► CLASSIFY/EMBED images → CLIP/SigLIP (references/clip.md, references/siglip.md)
│   └─► Zero-shot classification, image search, embeddings
│
├─► TAG images → RAM++ (references/ram-plus-image-tagging.md)
│   └─► Multi-label tagging, 4,585 categories
│
├─► MULTIPLE TASKS → Florence-2 (references/florence-2.md)
│   └─► Detection + captioning + OCR + grounding
│
├─► ESTIMATE DEPTH → Depth models (references/depth-estimation.md)
│   └─► 3D understanding, AR, robotics
│
└─► NONE OF ABOVE → Check VLLM skill
    └─► Conversational, reasoning, VQA
```

---

## Model Selection by Task

### Object Detection

| Need | Model | Why |
|------|-------|-----|
| Real-time video | YOLOv8n/s | Fastest, 30+ FPS |
| High accuracy | YOLOv8x/YOLOv11x | Best mAP |
| Custom classes | YOLO (fine-tuned) | Easy training |
| Open-vocabulary | Florence-2 `<OPEN_VOCABULARY_DETECTION>` | Any class |
| Zero-shot | Grounding DINO | Text-guided |

**Reference**: `references/yolo.md`

### Image Segmentation

| Need | Model | Why |
|------|-------|-----|
| Interactive (click) | SAM | Best quality |
| Fast/real-time | FastSAM | YOLO-based |
| Video tracking | SAM 2 | Temporal consistency |
| Mobile | MobileSAM | Optimized |
| Instance + class | YOLOv8-seg | Detection + segmentation |

**Reference**: `references/sam.md`

### Image Classification / Embeddings

| Need | Model | Why |
|------|-------|-----|
| Zero-shot classification | SigLIP | Best accuracy |
| Image search | SigLIP/CLIP | Strong embeddings |
| Existing CLIP pipeline | OpenCLIP | Drop-in compatible |
| Domain-specific | BiomedCLIP, etc. | Specialized |
| Maximum accuracy | SigLIP SO400M | 83%+ ImageNet |

**Reference**: `references/siglip.md`, `references/clip.md`

### Image Tagging

| Need | Model | Why |
|------|-------|-----|
| Broad coverage | RAM++ | 4,585 categories |
| Open-set | RAM++ | LLM-enriched descriptions |
| With confidence | SigLIP | Sigmoid outputs |
| Fast batch | RAM++ | Optimized |

**Reference**: `references/ram-plus-image-tagging.md`

### Multi-Task / Unified

| Need | Model | Why |
|------|-------|-----|
| Detection + captioning | Florence-2 | Unified prompts |
| OCR + grounding | Florence-2 | Text + location |
| Edge deployment | Florence-2-base | 232M params |
| Best multi-task | Florence-2-large | 771M params |

**Reference**: `references/florence-2.md`

### Depth Estimation

| Need | Model | Why |
|------|-------|-----|
| General purpose | Depth Anything V2 | Fast, accurate |
| Metric depth | ZoeDepth | Actual distances |
| Best quality | Marigold | Diffusion-based |
| Mobile/edge | Depth Anything V2-S | Lightweight |

**Reference**: `references/depth-estimation.md`

---

## Model Comparison Overview

### Speed vs Quality

```
Quality
   ▲
   │                               ┌─────────────┐
   │                               │ Florence-2-L│
   │                     ┌─────────┤   771M      │
   │                     │ SAM-H   └─────────────┘
   │           ┌─────────┤  636M
   │           │ SigLIP  │         ┌─────────────┐
   │  ┌────────┤ SO400M  │         │  YOLOv8x    │
   │  │ RAM++  │ 400M    │         │    68M      │
   │  │  ~3GB  └─────────┘         └─────────────┘
   │  │
   │  │        ┌─────────┐         ┌─────────────┐
   │  │        │ SAM-B   │         │  YOLOv8m    │
   │  │        │  91M    │         │    26M      │
   │  │        └─────────┘         └─────────────┘
   │  │
   │  │        ┌─────────┐         ┌─────────────┐
   │  │        │ FastSAM │         │  YOLOv8n    │
   │  │        │         │         │    3M       │
   │  │        └─────────┘         └─────────────┘
   │  │
   └──┴────────┴─────────┴─────────┴─────────────┴────────▶ Speed
            Slow                              Fast
```

### Task Coverage Matrix

| Model | Detection | Segmentation | Classification | Tagging | OCR | Captioning | Depth |
|-------|-----------|--------------|----------------|---------|-----|------------|-------|
| **YOLO** | ✓✓ | ✓ (seg variant) | ✗ | ✗ | ✗ | ✗ | ✗ |
| **SAM** | ✗ | ✓✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **CLIP/SigLIP** | ✗ | ✗ | ✓✓ | ✓ | ✗ | ✗ | ✗ |
| **RAM++** | ✗ | ✗ | ✓ | ✓✓ | ✗ | ✗ | ✗ |
| **Florence-2** | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ |
| **Depth Anything** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓✓ |

Legend: ✓✓ Excellent | ✓ Good | ✗ Not supported

---

## Common Pipelines

### Pipeline 1: Detect → Segment

Use YOLO for fast detection, SAM for precise segmentation:

```python
from ultralytics import YOLO
from segment_anything import sam_model_registry, SamPredictor

yolo = YOLO("yolov8m.pt")
sam = sam_model_registry["vit_b"](checkpoint="sam_vit_b.pth")
predictor = SamPredictor(sam)

def detect_and_segment(image):
    # Detect with YOLO
    results = yolo(image)[0]
    predictor.set_image(image)

    segments = []
    for box in results.boxes:
        bbox = box.xyxy[0].cpu().numpy()
        masks, _, _ = predictor.predict(box=bbox)
        segments.append({
            'class': yolo.names[int(box.cls[0])],
            'mask': masks[0],
            'bbox': bbox
        })
    return segments
```

### Pipeline 2: Tag → Describe

Use RAM++ for tags, CLIP/SigLIP for similarity:

```python
from ram import inference_ram
from transformers import AutoModel, AutoProcessor

# Get tags with RAM++
tags = inference_ram(image, ram_model)

# Get embedding with SigLIP
processor = AutoProcessor.from_pretrained("google/siglip-so400m-patch14-384")
model = AutoModel.from_pretrained("google/siglip-so400m-patch14-384")

inputs = processor(images=image, return_tensors="pt")
embedding = model.get_image_features(**inputs)
```

### Pipeline 3: Multi-Task with Florence-2

Single model for multiple outputs:

```python
from transformers import AutoProcessor, AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("microsoft/Florence-2-large", trust_remote_code=True)
processor = AutoProcessor.from_pretrained("microsoft/Florence-2-large", trust_remote_code=True)

def florence_multi_task(image):
    tasks = ["<CAPTION>", "<OD>", "<OCR>"]
    results = {}

    for task in tasks:
        inputs = processor(text=task, images=image, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=1024)
        text = processor.batch_decode(outputs, skip_special_tokens=False)[0]
        results[task] = processor.post_process_generation(text, task=task, image_size=image.size)

    return results
```

### Pipeline 4: Text-Guided Segmentation (Grounded-SAM)

```python
# Grounding DINO for text→boxes, SAM for boxes→masks
def segment_by_text(image, text_prompt):
    # Get boxes from Grounding DINO
    boxes = grounding_dino.predict(image, text_prompt)

    # Segment each box with SAM
    sam_predictor.set_image(image)
    masks = []
    for box in boxes:
        mask, _, _ = sam_predictor.predict(box=box)
        masks.append(mask)

    return masks
```

---

## 3090 Performance Guide

### Inference Speed (Batch 1)

| Model | Time | VRAM |
|-------|------|------|
| YOLOv8n | 2ms | 1GB |
| YOLOv8m | 4ms | 2GB |
| YOLOv8x | 8ms | 4GB |
| SAM ViT-B | 400ms | 3GB |
| SAM ViT-H | 3s | 8GB |
| FastSAM | 60ms | 2GB |
| SigLIP SO400M | 50ms | 3GB |
| RAM++ | 200ms | 3GB |
| Florence-2-base | 100ms | 2GB |
| Florence-2-large | 200ms | 4GB |
| Depth Anything V2-L | 60ms | 4GB |

### Concurrent Models

With 24GB VRAM, you can run multiple models simultaneously:

| Combination | VRAM | Use Case |
|-------------|------|----------|
| YOLO + SAM-B | 5GB | Detect + segment |
| YOLO + SigLIP | 5GB | Detect + classify |
| Florence-2 + Depth | 8GB | Multi-task + 3D |
| RAM++ + SigLIP | 6GB | Tag + embed |
| Full pipeline* | 15GB | Everything |

*YOLO + SAM-B + SigLIP + Florence-2-base

---

## Installation Quick Reference

### All Models (Recommended)

```bash
# Core
pip install torch torchvision
pip install transformers

# Detection
pip install ultralytics

# Segmentation
pip install git+https://github.com/facebookresearch/segment-anything.git

# Tagging
pip install git+https://github.com/xinyu1205/recognize-anything.git

# Depth
pip install depth-anything-v2
```

### Minimal (Per Model)

```bash
# YOLO only
pip install ultralytics

# SAM only
pip install segment-anything

# CLIP/SigLIP only
pip install transformers open-clip-torch

# Florence-2 only
pip install transformers flash_attn timm
```

---

## Feasibility Checklist

### Before Using Specialized VLMs

- [ ] **Task is well-defined**: Detection, segmentation, tagging, embedding, etc.
- [ ] **Speed requirements known**: Real-time vs batch processing
- [ ] **Accuracy requirements known**: Good enough vs maximum
- [ ] **Hardware constraints identified**: VRAM, CPU, edge
- [ ] **Not needing conversation**: Use VLLM for conversational AI

### Model Selection Criteria

| Factor | Question to Ask |
|--------|-----------------|
| **Task** | What exactly do I need? (boxes, masks, tags, etc.) |
| **Speed** | Real-time (<50ms)? Near real-time (<200ms)? Batch OK? |
| **Accuracy** | Production (good enough)? Research (maximum)? |
| **Zero-shot** | Need to handle new classes without training? |
| **Combination** | Need multiple tasks? Consider Florence-2 or pipelines |

---

## Reference Documents

### Task-Specific

| Document | Covers |
|----------|--------|
| `references/yolo.md` | Object detection, tracking, segmentation |
| `references/sam.md` | Interactive segmentation, video segmentation |
| `references/clip.md` | Zero-shot classification, embeddings |
| `references/siglip.md` | Improved CLIP, better small batch |
| `references/ram-plus-image-tagging.md` | Multi-label tagging |
| `references/florence-2.md` | Multi-task vision |
| `references/depth-estimation.md` | Monocular depth |

### Model Cards

| Model | Size | Key Strength |
|-------|------|--------------|
| YOLOv8/11 | 3-68M | Real-time detection |
| SAM | 91-636M | Universal segmentation |
| SigLIP | 86-1B | Zero-shot classification |
| RAM++ | ~3GB | Comprehensive tagging |
| Florence-2 | 232-771M | Multi-task unified |
| Depth Anything V2 | 25-335M | Fast depth |

---

## Common Patterns

### 1. Image Analysis Service

```python
class ImageAnalyzer:
    def __init__(self):
        self.yolo = YOLO("yolov8m.pt")
        self.siglip = AutoModel.from_pretrained("google/siglip-so400m-patch14-384")
        self.ram = load_ram_model()

    def analyze(self, image):
        return {
            "detections": self.yolo(image),
            "tags": inference_ram(image, self.ram),
            "embedding": self.siglip.get_image_features(image)
        }
```

### 2. Content Moderation

```python
def moderate_image(image):
    # Detect objects
    detections = yolo(image)

    # Get tags
    tags = ram_inference(image)

    # Check against policies
    flagged = check_policies(detections, tags)

    return flagged
```

### 3. Visual Search Index

```python
# Build index
embeddings = []
for image_path in image_paths:
    embedding = siglip.get_image_features(load_image(path))
    embeddings.append(embedding)

index = faiss.IndexFlatIP(embeddings.shape[1])
index.add(np.vstack(embeddings))

# Search
query_embedding = siglip.get_image_features(query_image)
distances, indices = index.search(query_embedding, k=10)
```

---

## When NOT to Use These Models

| Don't Use | Use Instead |
|-----------|-------------|
| Need to ask questions about images | VLLM (LLaVA, Qwen2-VL) |
| Need image generation | Stable Diffusion, DALL-E |
| Need video generation | Sora, Runway |
| Need audio from video | Whisper, audio models |
| Simple rule-based detection | OpenCV, traditional CV |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-01 | Initial version — 3090 optimized |
