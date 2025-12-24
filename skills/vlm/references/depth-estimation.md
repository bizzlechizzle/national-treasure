# Depth Estimation Models

> **Generated**: 2025-12-21
> **Sources current as of**: December 2024
> **Version**: 1.0

---

## Executive Summary / TLDR

**Monocular depth estimation** predicts depth maps from single RGB images, enabling 3D understanding without specialized hardware. Recent foundation models achieve remarkable zero-shot generalization across domains.

**Key models:**
- **Depth Anything V2** (Jun 2024): Current SOTA, fast, robust
- **MiDaS** (2020-2024): Mature, widely used, multiple versions
- **Marigold**: Diffusion-based, high quality
- **ZoeDepth**: Metric depth (actual distances)
- **UniDepth**: Metric depth with camera intrinsics

**Key distinction:**
- **Relative depth**: Orders surfaces by distance (most models)
- **Metric depth**: Actual distances in meters (ZoeDepth, UniDepth)

**Recommendation**: Depth Anything V2 for general use, ZoeDepth for metric depth.

---

## Model Comparison

| Model | Type | Quality | Speed | Zero-Shot | Metric |
|-------|------|---------|-------|-----------|--------|
| **Depth Anything V2** | Encoder-decoder | Excellent | Fast | Yes | No* |
| **MiDaS v3.1** | Encoder-decoder | Very Good | Fast | Yes | No |
| **Marigold** | Diffusion | Excellent | Slow | Yes | No |
| **ZoeDepth** | Two-stage | Very Good | Medium | Yes | Yes |
| **UniDepth** | Encoder-decoder | Very Good | Fast | Yes | Yes |
| **Metric3D V2** | Encoder-decoder | Very Good | Fast | Yes | Yes |

*Depth Anything V2 has metric variants

---

## Depth Anything V2

### Installation

```bash
pip install transformers torch
# or
pip install depth-anything-v2
```

### Basic Usage (Transformers)

```python
import torch
from transformers import pipeline
from PIL import Image

# Load pipeline
pipe = pipeline(
    task="depth-estimation",
    model="depth-anything/Depth-Anything-V2-Small-hf",
    device=0
)

# Predict depth
image = Image.open("image.jpg")
depth = pipe(image)["depth"]

# depth is a PIL Image, convert to numpy
import numpy as np
depth_array = np.array(depth)
```

### Model Variants

| Variant | Params | Speed | Quality |
|---------|--------|-------|---------|
| **Small** | 24.8M | Very Fast | Good |
| **Base** | 97.5M | Fast | Very Good |
| **Large** | 335M | Medium | Excellent |
| **Giant** | 1.3B | Slow | Best |

### Direct Usage (More Control)

```python
import torch
from depth_anything_v2.dpt import DepthAnythingV2
from PIL import Image
import numpy as np
import cv2

# Load model
model = DepthAnythingV2(
    encoder='vitl',  # vits, vitb, vitl, vitg
    features=256,
    out_channels=[256, 512, 1024, 1024]
)
model.load_state_dict(torch.load('depth_anything_v2_vitl.pth'))
model.eval().cuda()

# Prepare image
image = cv2.imread('image.jpg')
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Predict
with torch.no_grad():
    depth = model.infer_image(image_rgb)

# depth is relative (0-1 range after normalization)
depth_normalized = (depth - depth.min()) / (depth.max() - depth.min())
```

### Metric Depth Variant

```python
from transformers import pipeline

# Metric depth model (outputs in meters)
pipe = pipeline(
    task="depth-estimation",
    model="depth-anything/Depth-Anything-V2-Metric-Indoor-Large-hf"
)

depth = pipe(image)["depth"]
# Values are actual distances in meters
```

---

## MiDaS

### Installation

```bash
pip install timm torch
# Download models from https://github.com/isl-org/MiDaS
```

### Usage

```python
import torch
import cv2

# Load model
model_type = "DPT_Large"  # DPT_Large, DPT_Hybrid, MiDaS_small
midas = torch.hub.load("intel-isl/MiDaS", model_type)
midas.eval().cuda()

# Load transform
midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
transform = midas_transforms.dpt_transform

# Predict
img = cv2.imread("image.jpg")
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

input_batch = transform(img_rgb).cuda()

with torch.no_grad():
    prediction = midas(input_batch)
    prediction = torch.nn.functional.interpolate(
        prediction.unsqueeze(1),
        size=img.shape[:2],
        mode="bicubic",
        align_corners=False,
    ).squeeze()

depth = prediction.cpu().numpy()
```

### MiDaS Variants

| Variant | Backbone | Quality | Speed |
|---------|----------|---------|-------|
| MiDaS v2.1 Small | EfficientNet | Good | Very Fast |
| MiDaS v3.0 DPT-Hybrid | ViT-Hybrid | Very Good | Fast |
| MiDaS v3.0 DPT-Large | ViT-Large | Excellent | Medium |
| MiDaS v3.1 BEiT-Large | BEiT-Large | Excellent | Medium |

---

## ZoeDepth (Metric Depth)

### Installation

```bash
pip install zoedepth
# or
git clone https://github.com/isl-org/ZoeDepth
```

### Usage

```python
import torch
from zoedepth.models.builder import build_model
from zoedepth.utils.config import get_config
from PIL import Image
import numpy as np

# Load model
conf = get_config("zoedepth", "infer")
model = build_model(conf).cuda().eval()

# Predict metric depth
image = Image.open("image.jpg")
depth = model.infer_pil(image)

# depth values are in meters
print(f"Min depth: {depth.min():.2f}m, Max depth: {depth.max():.2f}m")
```

### ZoeDepth Variants

| Variant | Training Data | Best For |
|---------|---------------|----------|
| ZoeDepth-NK | NYU + KITTI | Indoor + outdoor |
| ZoeDepth-N | NYU only | Indoor scenes |
| ZoeDepth-K | KITTI only | Driving/outdoor |

---

## Marigold (Diffusion-based)

### Installation

```bash
pip install diffusers transformers accelerate
```

### Usage

```python
import torch
from diffusers import MarigoldDepthPipeline
from PIL import Image

# Load pipeline
pipe = MarigoldDepthPipeline.from_pretrained(
    "prs-eth/marigold-depth-lcm-v1-0",
    torch_dtype=torch.float16
).to("cuda")

# Predict
image = Image.open("image.jpg")
depth = pipe(
    image,
    num_inference_steps=4,  # LCM is fast
    ensemble_size=1
)

depth_image = depth.prediction[0]  # PIL Image
depth_array = depth.depth_np[0]    # Numpy array
```

### Marigold Variants

| Variant | Steps | Quality | Speed |
|---------|-------|---------|-------|
| Marigold (full) | 50 | Best | Slow |
| Marigold-LCM | 4 | Very Good | Fast |

---

## UniDepth (Metric + Camera)

### Installation

```bash
pip install git+https://github.com/lpiccinelli-eth/UniDepth
```

### Usage

```python
import torch
from unidepth.models import UniDepthV2
from PIL import Image
import numpy as np

# Load model
model = UniDepthV2.from_pretrained("lpiccinelli/unidepth-v2-vitl14")
model.eval().cuda()

# Predict (returns metric depth + camera intrinsics)
image = Image.open("image.jpg")
rgb = torch.from_numpy(np.array(image)).permute(2, 0, 1).float() / 255.0
rgb = rgb.unsqueeze(0).cuda()

with torch.no_grad():
    predictions = model.infer(rgb)

depth = predictions["depth"]  # Metric depth in meters
intrinsics = predictions["intrinsics"]  # Camera parameters
```

---

## Performance Benchmarks

### Speed Comparison (A100)

| Model | Resolution | Time | VRAM |
|-------|------------|------|------|
| Depth Anything V2-S | 518x518 | 15ms | 1GB |
| Depth Anything V2-L | 518x518 | 45ms | 3GB |
| MiDaS DPT-Large | 384x384 | 35ms | 2GB |
| Marigold-LCM | 768x768 | 200ms | 4GB |
| ZoeDepth-NK | 384x512 | 50ms | 2GB |

### 3090 Performance

| Model | Batch 1 | Batch 8 | VRAM |
|-------|---------|---------|------|
| Depth Anything V2-S | 20ms | 60ms | 2GB |
| Depth Anything V2-L | 60ms | 250ms | 4GB |
| Depth Anything V2-G | 200ms | OOM | 12GB |

---

## Use Cases

### When to Use Depth Estimation

- **3D reconstruction**: Create 3D models from images
- **Augmented reality**: Place virtual objects on surfaces
- **Autonomous navigation**: Understand scene geometry
- **Image editing**: Depth-based effects (blur, fog)
- **Robotics**: Obstacle avoidance
- **Video effects**: Depth-of-field, 3D photos

### Choosing the Right Model

| Use Case | Recommended Model |
|----------|-------------------|
| General purpose | Depth Anything V2 |
| Need actual distances | ZoeDepth or DA-V2 Metric |
| Best quality (slow OK) | Marigold |
| Edge/mobile | Depth Anything V2-S |
| Indoor scenes | ZoeDepth-N |
| Driving/outdoor | ZoeDepth-K |
| Need camera intrinsics | UniDepth |

---

## Integration Examples

### Depth-Based Image Editing

```python
import numpy as np
from PIL import Image, ImageFilter

def apply_depth_blur(image, depth, focus_distance, blur_amount=10):
    """Apply depth-of-field blur based on depth map."""
    # Normalize depth
    depth_norm = (depth - depth.min()) / (depth.max() - depth.min())

    # Calculate blur map
    blur_map = np.abs(depth_norm - focus_distance) * blur_amount

    # Apply varying blur (simplified - real implementation would be more complex)
    blurred = image.filter(ImageFilter.GaussianBlur(blur_amount))

    # Blend based on depth
    result = Image.blend(image, blurred, alpha=0.5)
    return result
```

### 3D Point Cloud

```python
import numpy as np
import open3d as o3d

def depth_to_pointcloud(depth, image, fx, fy, cx, cy):
    """Convert depth map to 3D point cloud."""
    h, w = depth.shape
    i, j = np.meshgrid(np.arange(w), np.arange(h))

    # Back-project to 3D
    z = depth
    x = (i - cx) * z / fx
    y = (j - cy) * z / fy

    points = np.stack([x, y, z], axis=-1).reshape(-1, 3)
    colors = np.array(image).reshape(-1, 3) / 255.0

    # Create Open3D point cloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.colors = o3d.utility.Vector3dVector(colors)

    return pcd
```

### FastAPI Service

```python
from fastapi import FastAPI, UploadFile
from transformers import pipeline
from PIL import Image
import io
import base64
import numpy as np

app = FastAPI()
depth_pipe = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")

@app.post("/depth")
async def estimate_depth(file: UploadFile):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    depth = depth_pipe(image)["depth"]

    # Convert to base64 for response
    buffer = io.BytesIO()
    depth.save(buffer, format="PNG")
    depth_b64 = base64.b64encode(buffer.getvalue()).decode()

    return {"depth_image": depth_b64}
```

---

## Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Relative vs metric** | Most output relative depth | Use ZoeDepth/UniDepth for metric |
| **Scale ambiguity** | Can't determine absolute size | Need reference or metric model |
| **Reflective surfaces** | Poor depth on mirrors/glass | Manual correction needed |
| **Transparent objects** | Depth through transparent surfaces | Dataset limitation |
| **Textureless regions** | Less accurate on blank walls | Use stereo or structured light |

---

## Source Appendix

| # | Source | Date | Type |
|---|--------|------|------|
| 1 | [Depth Anything V2 Paper](https://arxiv.org/abs/2406.09414) | Jun 2024 | Primary |
| 2 | [Depth Anything GitHub](https://github.com/LiheYoung/Depth-Anything) | 2024 | Primary |
| 3 | [MiDaS GitHub](https://github.com/isl-org/MiDaS) | 2020-24 | Primary |
| 4 | [ZoeDepth Paper](https://arxiv.org/abs/2302.12288) | Feb 2023 | Primary |
| 5 | [Marigold Paper](https://arxiv.org/abs/2312.02145) | Dec 2023 | Primary |
| 6 | [UniDepth Paper](https://arxiv.org/abs/2403.18913) | Mar 2024 | Primary |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-21 | Initial version |
