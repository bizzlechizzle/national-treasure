# CLIP: Contrastive Language-Image Pre-Training

> **Generated**: 2025-12-21
> **Sources current as of**: December 2024
> **Version**: 1.0

---

## Executive Summary / TLDR

**CLIP (Contrastive Language-Image Pre-Training)** is OpenAI's foundational vision-language model released in January 2021. It learns visual concepts from natural language supervision by training on 400M image-text pairs from the web, enabling remarkable zero-shot transfer to downstream tasks without task-specific training.

**Key capabilities:**
- **Zero-shot classification**: Classify images into arbitrary categories using text descriptions
- **Image-text similarity**: Compute similarity between images and text for retrieval
- **Embedding extraction**: Generate 512/768-dimensional embeddings for images and text
- **Foundation for other models**: Serves as backbone for Stable Diffusion, LLaVA, and many others

**Performance highlights:**
- 76.2% zero-shot ImageNet accuracy (ViT-L/14@336)
- Matches supervised ResNet-50 with zero training on ImageNet
- Strong robustness to distribution shift

---

## Model Architecture

### Overview

CLIP consists of two encoders trained jointly with contrastive learning:

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│   Image     │────▶│  Image Encoder  │────▶│  Image      │
│             │     │  (ViT or RN)    │     │  Embedding  │
└─────────────┘     └─────────────────┘     └─────────────┘
                                                  │
                                                  ▼
                                            [Contrastive]
                                            [  Loss     ]
                                                  ▲
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│   Text      │────▶│  Text Encoder   │────▶│  Text       │
│             │     │  (Transformer)  │     │  Embedding  │
└─────────────┘     └─────────────────┘     └─────────────┘
```

### Image Encoder Variants

| Variant | Architecture | Resolution | Embedding Dim | Parameters |
|---------|--------------|------------|---------------|------------|
| RN50 | ResNet-50 | 224 | 1024 | 102M |
| RN101 | ResNet-101 | 224 | 512 | 120M |
| RN50x4 | ResNet-50 (4x width) | 288 | 640 | 178M |
| RN50x16 | ResNet-50 (16x width) | 384 | 768 | 420M |
| RN50x64 | ResNet-50 (64x width) | 448 | 1024 | 623M |
| ViT-B/32 | ViT-Base, patch 32 | 224 | 512 | 151M |
| ViT-B/16 | ViT-Base, patch 16 | 224 | 512 | 150M |
| ViT-L/14 | ViT-Large, patch 14 | 224 | 768 | 428M |
| ViT-L/14@336 | ViT-Large, patch 14 | 336 | 768 | 428M |

### Text Encoder

- **Architecture**: 12-layer Transformer with 512-width, 8 attention heads
- **Tokenizer**: Byte-pair encoding (BPE) with 49,152 vocab size
- **Max sequence length**: 77 tokens
- **Output**: [EOS] token embedding as text representation

### Contrastive Loss

CLIP uses **InfoNCE loss** (softmax-based contrastive):

```
L = -log(exp(sim(i,t) / τ) / Σ_j exp(sim(i,t_j) / τ))
```

Where τ is a learned temperature parameter.

---

## Installation & Usage

### Installation

```bash
# OpenAI CLIP
pip install git+https://github.com/openai/CLIP.git

# OpenCLIP (recommended for more variants)
pip install open-clip-torch

# Hugging Face Transformers
pip install transformers
```

### Basic Usage (OpenAI CLIP)

```python
import torch
import clip
from PIL import Image

# Load model
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Prepare inputs
image = preprocess(Image.open("image.jpg")).unsqueeze(0).to(device)
text = clip.tokenize(["a cat", "a dog", "a bird"]).to(device)

# Get predictions
with torch.no_grad():
    image_features = model.encode_image(image)
    text_features = model.encode_text(text)

    # Normalize
    image_features /= image_features.norm(dim=-1, keepdim=True)
    text_features /= text_features.norm(dim=-1, keepdim=True)

    # Compute similarity
    similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)

print(f"Probabilities: {similarity[0]}")
```

### Using OpenCLIP (More Models)

```python
import open_clip
import torch
from PIL import Image

# List available models
print(open_clip.list_pretrained())

# Load model
model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-L-14',
    pretrained='laion2b_s32b_b82k'
)
tokenizer = open_clip.get_tokenizer('ViT-L-14')

model.eval()

# Zero-shot classification
image = preprocess(Image.open("image.jpg")).unsqueeze(0)
text = tokenizer(["a cat", "a dog", "a bird"])

with torch.no_grad():
    image_features = model.encode_image(image)
    text_features = model.encode_text(text)

    image_features /= image_features.norm(dim=-1, keepdim=True)
    text_features /= text_features.norm(dim=-1, keepdim=True)

    probs = (100.0 * image_features @ text_features.T).softmax(dim=-1)
```

### Using Hugging Face Transformers

```python
from transformers import CLIPProcessor, CLIPModel
import torch
from PIL import Image

model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")

image = Image.open("image.jpg")
texts = ["a cat", "a dog", "a bird"]

inputs = processor(text=texts, images=image, return_tensors="pt", padding=True)

with torch.no_grad():
    outputs = model(**inputs)
    logits_per_image = outputs.logits_per_image
    probs = logits_per_image.softmax(dim=1)

for text, prob in zip(texts, probs[0]):
    print(f"{text}: {prob:.1%}")
```

---

## Zero-Shot Classification

### Prompt Engineering

The text prompt significantly affects performance:

```python
# Basic (worse)
labels = ["cat", "dog", "bird"]

# With template (better)
labels = ["a photo of a cat", "a photo of a dog", "a photo of a bird"]

# Domain-specific (best for specific domains)
labels = [
    "a photo of a cat, a type of pet",
    "a photo of a dog, a type of pet",
    "a photo of a bird, a type of animal"
]
```

### Prompt Ensembling

```python
# Multiple templates improve robustness
templates = [
    "a photo of a {}.",
    "a photograph of a {}.",
    "an image of a {}.",
    "a picture of a {}.",
    "a {} in a photo.",
]

def get_ensemble_text_features(model, tokenizer, class_names, templates):
    """Ensemble text features across templates."""
    all_features = []

    for class_name in class_names:
        class_features = []
        for template in templates:
            text = template.format(class_name)
            tokens = tokenizer([text])
            with torch.no_grad():
                features = model.encode_text(tokens)
                features /= features.norm(dim=-1, keepdim=True)
            class_features.append(features)

        # Average across templates
        class_features = torch.stack(class_features).mean(dim=0)
        class_features /= class_features.norm(dim=-1, keepdim=True)
        all_features.append(class_features)

    return torch.cat(all_features)
```

---

## Image-Text Retrieval

### Image-to-Text Retrieval

```python
import numpy as np

def retrieve_texts(image_embedding, text_embeddings, texts, top_k=5):
    """Find most similar texts to an image."""
    similarities = (image_embedding @ text_embeddings.T).squeeze()
    top_indices = similarities.argsort(descending=True)[:top_k]
    return [(texts[i], similarities[i].item()) for i in top_indices]
```

### Text-to-Image Retrieval

```python
def retrieve_images(text_embedding, image_embeddings, image_paths, top_k=5):
    """Find most similar images to a text query."""
    similarities = (text_embedding @ image_embeddings.T).squeeze()
    top_indices = similarities.argsort(descending=True)[:top_k]
    return [(image_paths[i], similarities[i].item()) for i in top_indices]
```

### Building an Index with FAISS

```python
import faiss
import numpy as np

def build_image_index(model, preprocess, image_paths, batch_size=32):
    """Build FAISS index from images."""
    embeddings = []

    for i in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[i:i+batch_size]
        images = torch.stack([preprocess(Image.open(p)) for p in batch_paths])

        with torch.no_grad():
            features = model.encode_image(images.to(device))
            features /= features.norm(dim=-1, keepdim=True)

        embeddings.append(features.cpu().numpy())

    embeddings = np.vstack(embeddings).astype('float32')

    # Build FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return index, embeddings
```

---

## OpenCLIP Extended Models

OpenCLIP provides CLIP models trained on larger datasets:

| Model | Dataset | ImageNet 0-shot | Notes |
|-------|---------|-----------------|-------|
| ViT-B/32 | LAION-2B | 66.6% | Good baseline |
| ViT-L/14 | LAION-2B | 75.3% | Strong performer |
| ViT-H/14 | LAION-2B | 78.0% | High quality |
| ViT-G/14 | LAION-2B | 80.1% | Near SOTA |
| ViT-bigG/14 | LAION-2B | **80.5%** | Best OpenCLIP |
| EVA-CLIP-8B | Merged | **82.0%** | Largest |

### Domain-Specific CLIP Models

| Model | Domain | Training Data |
|-------|--------|---------------|
| BiomedCLIP | Biomedical | PMC-15M |
| Fashion-CLIP | Fashion | LAION + fashion |
| RemoteCLIP | Satellite | Remote sensing images |
| GeoRSCLIP | Geography | Geo-tagged images |

---

## Comparison with SigLIP

| Aspect | CLIP | SigLIP |
|--------|------|--------|
| **Loss function** | Softmax (InfoNCE) | Sigmoid (binary) |
| **Batch size sensitivity** | Better at large batch | Better at small batch |
| **Memory efficiency** | Baseline | ~10-100% better |
| **Small batch (<16k)** | Worse | Better |
| **Large batch (32k+)** | Optimal | Optimal |
| **Ecosystem** | Massive, mature | Growing |
| **Output interpretation** | Softmax probs | Independent probs |

**Recommendation**: Use SigLIP for new projects, CLIP for existing pipelines or domain-specific variants.

---

## Performance Benchmarks

### ImageNet Zero-Shot

| Model | Top-1 Accuracy | Top-5 Accuracy |
|-------|----------------|----------------|
| CLIP ViT-B/32 | 63.4% | 87.2% |
| CLIP ViT-B/16 | 68.3% | 89.4% |
| CLIP ViT-L/14 | 75.5% | 92.8% |
| CLIP ViT-L/14@336 | **76.2%** | **93.3%** |

### Robustness to Distribution Shift

CLIP shows remarkable robustness compared to supervised models:

| Dataset | ResNet-50 (ImageNet trained) | CLIP ViT-B/32 |
|---------|------------------------------|---------------|
| ImageNet-V2 | 63.3% | 55.0% |
| ImageNet-R | 17.5% | 56.0% |
| ImageNet-A | 2.5% | 23.8% |
| ImageNet-Sketch | 24.1% | 35.4% |

---

## Hardware Requirements

| Model | VRAM (FP16) | Inference Speed (A100) |
|-------|-------------|------------------------|
| ViT-B/32 | 2GB | ~3000 img/s |
| ViT-B/16 | 2GB | ~1500 img/s |
| ViT-L/14 | 4GB | ~500 img/s |
| ViT-L/14@336 | 6GB | ~300 img/s |
| ViT-H/14 | 8GB | ~200 img/s |

For 3090 (24GB VRAM): All models fit comfortably with room for batch processing.

---

## Use Cases

### When to Use CLIP

- **Zero-shot classification**: Classify images into arbitrary categories
- **Image search**: Build semantic image search systems
- **Content moderation**: Detect specific content types
- **Multimodal embeddings**: Joint image-text representations
- **Foundation for other models**: Backbone for VLMs, diffusion models

### When NOT to Use CLIP

- **Object detection**: Use YOLO, Florence-2
- **Segmentation**: Use SAM
- **Dense tagging**: Use RAM++
- **Conversational VLM**: Use LLaVA, Qwen2-VL
- **Need confidence scores**: Consider SigLIP (sigmoid outputs)

---

## Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Softmax normalization** | Probabilities sum to 1, can't say "none of the above" | Use SigLIP for independent probabilities |
| **77 token limit** | Long text descriptions truncated | Chunk long texts |
| **No localization** | Can't point to objects in image | Combine with detection model |
| **Prompt sensitivity** | Results vary with prompt phrasing | Use prompt ensembling |
| **Bias from web data** | May reflect internet biases | Evaluate on domain-specific data |

---

## Source Appendix

| # | Source | Date | Type |
|---|--------|------|------|
| 1 | [CLIP Paper - Learning Transferable Visual Models](https://arxiv.org/abs/2103.00020) | Mar 2021 | Primary |
| 2 | [OpenAI CLIP GitHub](https://github.com/openai/CLIP) | 2021 | Primary |
| 3 | [OpenCLIP GitHub](https://github.com/mlfoundations/open_clip) | 2022+ | Primary |
| 4 | [Hugging Face CLIP Docs](https://huggingface.co/docs/transformers/model_doc/clip) | 2024 | Primary |
| 5 | [CLIP Model Card](https://github.com/openai/CLIP/blob/main/model-card.md) | 2021 | Primary |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-21 | Initial version |
