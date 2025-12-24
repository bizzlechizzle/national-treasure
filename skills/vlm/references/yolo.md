# YOLO: You Only Look Once - Object Detection

> **Generated**: 2025-12-21
> **Sources current as of**: December 2024
> **Version**: 1.0

---

## Executive Summary / TLDR

**YOLO (You Only Look Once)** is the dominant real-time object detection architecture, now in its 11th major version. YOLO models provide the best balance of speed and accuracy for detecting and localizing objects in images and video streams.

**Key capabilities:**
- **Object detection**: Bounding boxes + class labels
- **Instance segmentation**: Pixel-level masks (YOLOv8+)
- **Pose estimation**: Keypoint detection (YOLOv8+)
- **Oriented bounding boxes**: Rotated detection (YOLOv8+)
- **Tracking**: Multi-object tracking (integrated)

**Current state (December 2024):**
- **YOLOv8** (Ultralytics, Jan 2023): Most widely deployed, excellent ecosystem
- **YOLOv9** (Feb 2024): Programmable Gradient Information (PGI)
- **YOLOv10** (May 2024): NMS-free, end-to-end
- **YOLOv11** (Sep 2024): Latest Ultralytics release

**Recommendation**: Use YOLOv8 for production stability, YOLOv11 for latest features.

---

## Model Versions Overview

### Active Versions (2024)

| Version | Date | Key Innovation | Maintainer |
|---------|------|----------------|------------|
| **YOLOv8** | Jan 2023 | Anchor-free, unified API | Ultralytics |
| **YOLOv9** | Feb 2024 | PGI, GELAN architecture | Original authors |
| **YOLOv10** | May 2024 | NMS-free, end-to-end | Tsinghua |
| **YOLOv11** | Sep 2024 | C3k2 block, attention | Ultralytics |

### Model Size Variants

All modern YOLO versions offer these size variants:

| Size | Suffix | Params (v8) | Speed | Use Case |
|------|--------|-------------|-------|----------|
| Nano | -n | 3.2M | Fastest | Edge/mobile |
| Small | -s | 11.2M | Fast | Embedded |
| Medium | -m | 25.9M | Balanced | General |
| Large | -l | 43.7M | Accurate | Server |
| Extra-Large | -x | 68.2M | Most accurate | Cloud |

---

## YOLOv8 (Recommended for Production)

### Installation

```bash
pip install ultralytics
```

### Basic Object Detection

```python
from ultralytics import YOLO

# Load model
model = YOLO("yolov8n.pt")  # nano, fastest
# model = YOLO("yolov8s.pt")  # small
# model = YOLO("yolov8m.pt")  # medium
# model = YOLO("yolov8l.pt")  # large
# model = YOLO("yolov8x.pt")  # extra-large

# Run inference
results = model("image.jpg")

# Process results
for result in results:
    boxes = result.boxes  # Bounding boxes
    for box in boxes:
        xyxy = box.xyxy[0]  # x1, y1, x2, y2
        conf = box.conf[0]  # confidence
        cls = box.cls[0]    # class index
        label = model.names[int(cls)]
        print(f"{label}: {conf:.2f} at {xyxy}")
```

### Instance Segmentation

```python
model = YOLO("yolov8n-seg.pt")  # segmentation model

results = model("image.jpg")

for result in results:
    masks = result.masks  # Segmentation masks
    if masks is not None:
        for mask in masks.data:
            # mask is a binary tensor
            pass
```

### Pose Estimation

```python
model = YOLO("yolov8n-pose.pt")  # pose model

results = model("image.jpg")

for result in results:
    keypoints = result.keypoints  # Keypoints
    if keypoints is not None:
        for kp in keypoints.data:
            # kp contains x, y, confidence for each keypoint
            pass
```

### Oriented Bounding Boxes

```python
model = YOLO("yolov8n-obb.pt")  # oriented bbox model

results = model("aerial_image.jpg")

for result in results:
    obbs = result.obb  # Oriented bounding boxes
    if obbs is not None:
        for obb in obbs:
            # obb contains rotated box coordinates
            pass
```

### Video Processing

```python
# Process video
results = model("video.mp4", stream=True)

for result in results:
    # Process each frame
    annotated = result.plot()
    # Display or save annotated frame
```

### Tracking

```python
# Multi-object tracking
results = model.track("video.mp4", persist=True)

for result in results:
    boxes = result.boxes
    if boxes.id is not None:
        track_ids = boxes.id.int().tolist()
        # Each detection now has a persistent track ID
```

---

## YOLOv11 (Latest)

### Installation

```bash
pip install ultralytics>=8.3.0
```

### Usage (Same API as v8)

```python
from ultralytics import YOLO

# Load YOLOv11
model = YOLO("yolo11n.pt")  # Note: yolo11, not yolov11

# Same API as YOLOv8
results = model("image.jpg")
```

### YOLOv11 Improvements

- **C3k2 block**: More efficient backbone
- **Attention mechanisms**: Better feature extraction
- **Improved small object detection**
- **Better accuracy/speed tradeoff**

---

## Training Custom Models

### Dataset Format (YOLO)

```yaml
# dataset.yaml
path: /path/to/dataset
train: images/train
val: images/val
test: images/test

names:
  0: person
  1: car
  2: bicycle
```

Label format (one `.txt` per image):
```
# class_id center_x center_y width height (normalized 0-1)
0 0.5 0.5 0.2 0.3
1 0.7 0.8 0.1 0.15
```

### Training

```python
from ultralytics import YOLO

# Load pretrained model
model = YOLO("yolov8n.pt")

# Train
results = model.train(
    data="dataset.yaml",
    epochs=100,
    imgsz=640,
    batch=16,
    device=0,  # GPU
    workers=8,
    patience=50,  # Early stopping
    save=True,
    project="runs/detect",
    name="custom_model"
)
```

### Training on COCO

```python
model = YOLO("yolov8n.pt")
model.train(data="coco.yaml", epochs=300, imgsz=640)
```

### Export to Different Formats

```python
# Export to ONNX
model.export(format="onnx")

# Export to TensorRT
model.export(format="engine")

# Export to CoreML (iOS)
model.export(format="coreml")

# Export to TFLite (mobile)
model.export(format="tflite")
```

---

## Performance Benchmarks

### COCO val2017 Results

| Model | mAP50-95 | Params | FLOPs | Speed (A100) |
|-------|----------|--------|-------|--------------|
| YOLOv8n | 37.3 | 3.2M | 8.7G | 0.99ms |
| YOLOv8s | 44.9 | 11.2M | 28.6G | 1.20ms |
| YOLOv8m | 50.2 | 25.9M | 78.9G | 1.83ms |
| YOLOv8l | 52.9 | 43.7M | 165G | 2.39ms |
| YOLOv8x | 53.9 | 68.2M | 258G | 3.53ms |
| YOLOv11n | 39.5 | 2.6M | 6.5G | 1.55ms |
| YOLOv11s | 47.0 | 9.4M | 21.5G | 2.46ms |
| YOLOv11m | 51.5 | 20.1M | 68.0G | 4.70ms |
| YOLOv11l | 53.4 | 25.3M | 87.6G | 6.16ms |
| YOLOv11x | 54.7 | 56.9M | 195G | 11.3ms |

### Speed on Different Hardware

| Model | A100 | RTX 3090 | RTX 4090 | T4 |
|-------|------|----------|----------|-----|
| YOLOv8n | 0.99ms | 1.5ms | 1.2ms | 3ms |
| YOLOv8s | 1.20ms | 2.0ms | 1.5ms | 5ms |
| YOLOv8m | 1.83ms | 3.5ms | 2.5ms | 10ms |
| YOLOv8l | 2.39ms | 5.0ms | 3.5ms | 15ms |

---

## Hardware Requirements (3090)

| Model | VRAM Usage | Batch Size | Throughput |
|-------|------------|------------|------------|
| YOLOv8n | 2GB | 64 | ~800 FPS |
| YOLOv8s | 3GB | 32 | ~500 FPS |
| YOLOv8m | 5GB | 16 | ~300 FPS |
| YOLOv8l | 8GB | 8 | ~200 FPS |
| YOLOv8x | 12GB | 4 | ~150 FPS |

For training on 3090:
- **YOLOv8n-m**: Batch 32-64
- **YOLOv8l**: Batch 8-16
- **YOLOv8x**: Batch 4-8

---

## Integration Patterns

### FastAPI Service

```python
from fastapi import FastAPI, UploadFile
from ultralytics import YOLO
from PIL import Image
import io

app = FastAPI()
model = YOLO("yolov8m.pt")

@app.post("/detect")
async def detect(file: UploadFile):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    results = model(image)

    detections = []
    for result in results:
        for box in result.boxes:
            detections.append({
                "class": model.names[int(box.cls[0])],
                "confidence": float(box.conf[0]),
                "bbox": box.xyxy[0].tolist()
            })

    return {"detections": detections}
```

### Batch Processing

```python
from pathlib import Path
from ultralytics import YOLO

model = YOLO("yolov8m.pt")

# Process directory of images
image_dir = Path("images/")
images = list(image_dir.glob("*.jpg"))

# Batch inference
results = model(images, batch=16, stream=True)

for result, path in zip(results, images):
    print(f"{path}: {len(result.boxes)} detections")
```

### Real-Time Video Stream

```python
import cv2
from ultralytics import YOLO

model = YOLO("yolov8n.pt")  # Use nano for speed
cap = cv2.VideoCapture(0)  # Webcam

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run detection
    results = model(frame, verbose=False)

    # Draw results
    annotated = results[0].plot()

    cv2.imshow("YOLO", annotated)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

---

## YOLO vs Other Detection Models

| Model | Speed | Accuracy | Use Case |
|-------|-------|----------|----------|
| **YOLO** | Very Fast | Good-Excellent | Real-time, production |
| **Florence-2** | Medium | Good | Multi-task, flexible |
| **DINO/DETR** | Slow | Excellent | High accuracy needed |
| **Faster R-CNN** | Slow | Excellent | Research, accuracy-first |
| **EfficientDet** | Medium | Very Good | Balanced |

### When to Use YOLO

- **Real-time requirements**: Video, webcam, robotics
- **High throughput**: Batch processing millions of images
- **Edge deployment**: Mobile, embedded, Jetson
- **Production stability**: Well-tested, huge community

### When NOT to Use YOLO

- **Need other tasks too**: Use Florence-2 for multi-task
- **Maximum accuracy**: Use DINO/DETR
- **Need segmentation + detection**: YOLOv8-seg or SAM+YOLO
- **Zero-shot/open-vocab**: Use Florence-2 or Grounding DINO

---

## Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Fixed classes** | Only detects trained classes | Fine-tune or use open-vocab models |
| **Small objects** | Lower accuracy on tiny objects | Use higher resolution, SAHI |
| **Crowded scenes** | Overlapping objects can merge | Tune NMS, use higher confidence |
| **Aspect ratio sensitivity** | Very long/tall objects | Adjust input size |

---

## Source Appendix

| # | Source | Date | Type |
|---|--------|------|------|
| 1 | [Ultralytics YOLOv8 Docs](https://docs.ultralytics.com/) | 2024 | Primary |
| 2 | [YOLOv11 Announcement](https://docs.ultralytics.com/models/yolo11/) | Sep 2024 | Primary |
| 3 | [YOLOv9 Paper](https://arxiv.org/abs/2402.13616) | Feb 2024 | Primary |
| 4 | [YOLOv10 Paper](https://arxiv.org/abs/2405.14458) | May 2024 | Primary |
| 5 | [YOLO History](https://docs.ultralytics.com/models/) | 2024 | Secondary |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-21 | Initial version |
