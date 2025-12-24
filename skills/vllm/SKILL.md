---
name: vllm
description: Vision Language Model integration guide for adding visual AI capabilities to applications. Problem-first guidance for image understanding, visual Q&A, document AI, OCR, and multimodal reasoning. Covers local deployment (optimized for RTX 3090/24GB VRAM), API usage, and multimodal prompting. Focuses on practical application.
---

# Vision Language Model Integration Guide v0.1.0

Add visual AI capabilities to your applications—locally or via API.

## Hardware Context

This guide is optimized for **RTX 3090 (24GB VRAM)**.

| VRAM | What Fits (FP16) | What Fits (Quantized) |
|------|------------------|----------------------|
| 24GB | 7-13B VLMs | 30B+ VLMs (4-bit) |
| 24GB | LLaVA 13B | Qwen2-VL 72B (4-bit) |

---

## Purpose

This skill helps you:

1. **Decide IF** a VLM is the right approach
2. **Choose HOW** to access VLMs (local vs API)
3. **Select WHICH** model fits your constraints
4. **Implement WHAT** pattern solves your problem
5. **Optimize FOR** cost, latency, and quality

---

## Quick Start

```
┌─────────────────────────────────────────────────────────────────┐
│                    VLM DECISION WORKFLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. FEASIBILITY   →  Is a VLM the right tool?                   │
│     └─► See: Feasibility Checklist (below)                      │
│                                                                 │
│  2. PROBLEM TYPE  →  What are you trying to do?                 │
│     └─► See: references/decision-tree.md                        │
│                                                                 │
│  3. ACCESS MODE   →  Local or API?                              │
│     └─► See: references/model-selection.md                      │
│                                                                 │
│  4. MODEL         →  Which model fits?                          │
│     └─► See: references/model-selection.md                      │
│                                                                 │
│  5. PROMPTING     →  How to structure image+text?               │
│     └─► See: references/multimodal-prompting.md                 │
│                                                                 │
│  6. DEPLOYMENT    →  How to serve in production?                │
│     └─► See: references/deployment.md                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feasibility Checklist

### Hard Requirements (Must Have ALL)

- [ ] **Task involves images** — Have images/screenshots/photos to analyze
- [ ] **Need understanding, not just detection** — If object detection suffices, use YOLO
- [ ] **Acceptable latency** — Can tolerate 500ms-30s response times
- [ ] **Error tolerance** — Some wrong outputs are acceptable

### Soft Requirements (Need MOST)

- [ ] **Diverse image types** — Not the same image template repeated
- [ ] **Task is hard to specify with rules** — Can't just check pixel colors
- [ ] **Need natural language output** — Not just bounding boxes
- [ ] **Have examples for evaluation** — Can measure quality

### Red Flags (Any = Reconsider)

- [ ] Pure object detection (use YOLO instead)
- [ ] Just need OCR text (use Tesseract/EasyOCR)
- [ ] Image classification only (use ResNet/EfficientNet)
- [ ] Face recognition (use specialized models)
- [ ] Need real-time video (<100ms per frame)
- [ ] Sub-pixel accuracy required

### Feasibility Verdict

| Checkboxes | Verdict |
|------------|---------|
| All Hard + Most Soft + No Red Flags | **Proceed with VLM** |
| Missing Hard requirements | **Use specialized CV models** |
| Red Flags present | **Use task-specific models** |

---

## Problem Type Quick Reference

| You want to... | Problem Type | Reference |
|----------------|--------------|-----------|
| Describe what's in an image | Image Understanding | `references/image-understanding.md` |
| Answer questions about images | Visual QA | `references/visual-qa.md` |
| Extract text/data from documents | Document AI | `references/document-ai.md` |
| Understand charts/diagrams | Document AI | `references/document-ai.md` |
| Process screenshots | Document AI | `references/document-ai.md` |
| Analyze video content | Video Understanding | `references/video-understanding.md` |

---

## VLM vs Traditional CV

### When to Use VLM

| Task | VLM | Traditional CV |
|------|-----|----------------|
| "What's happening in this photo?" | ✓ | ✗ |
| "Extract data from this invoice" | ✓ | Sometimes |
| "Is there a cat?" | Overkill | ✓ (classifier) |
| "Where are the faces?" | Overkill | ✓ (detector) |
| "Explain this chart" | ✓ | ✗ |
| "Count red cars" | ✓ | ✓ (detector + color) |
| "What's the mood of this image?" | ✓ | ✗ |
| Real-time object tracking | ✗ | ✓ |

### Decision

```
Need natural language understanding of images? → VLM
Need bounding boxes only? → YOLO/Detectron
Need classification only? → ResNet/EfficientNet
Need OCR only? → Tesseract/EasyOCR
Need face recognition? → InsightFace
Need segmentation? → SAM
```

---

## Local vs API Decision

### Quick Selector

| Factor | Local (3090) | API (GPT-4V, Claude) |
|--------|--------------|----------------------|
| **Privacy** | Data stays local | Sent to provider |
| **Cost at scale** | Fixed | Per-image |
| **Quality** | Good-Excellent | Best |
| **Latency** | Lower | Higher |
| **Video support** | Limited | Gemini 1.5 |
| **Document understanding** | Good | Excellent |

### Recommendation

| Scenario | Recommendation |
|----------|----------------|
| Privacy-critical | Local (LLaVA, Qwen2-VL) |
| Best quality needed | API (GPT-4o, Claude 3.5) |
| High volume | Local |
| Quick prototype | API |
| Video analysis | Gemini 1.5 API |

---

## Model Selection Overview (3090)

### Local VLMs

| Model | Size | VRAM (FP16) | VRAM (Q4) | Quality | Speed |
|-------|------|-------------|-----------|---------|-------|
| **LLaVA 1.6 7B** | 7B | 14GB | 5GB | Good | Fast |
| **LLaVA 1.6 13B** | 13B | 26GB | 8GB | Very Good | Medium |
| **Qwen2-VL 7B** | 7B | 16GB | 6GB | Very Good | Fast |
| **Qwen2-VL 72B** | 72B | — | 24GB | Excellent | Slow |
| **InternVL2 8B** | 8B | 18GB | 7GB | Very Good | Fast |
| **Phi-3 Vision** | 4B | 8GB | 3GB | Good | Very Fast |
| **MiniCPM-V 2.6** | 8B | 16GB | 6GB | Very Good | Fast |
| **Idefics2 8B** | 8B | 18GB | 7GB | Good | Fast |

### Best Choices for 3090

| Use Case | Model | Why |
|----------|-------|-----|
| **General purpose** | Qwen2-VL 7B | Best quality at size |
| **Best quality** | Qwen2-VL 72B (Q4) | SOTA local |
| **Fast inference** | Phi-3 Vision | Smallest |
| **Document understanding** | Qwen2-VL 7B | Strong OCR |
| **Multi-image** | LLaVA-NeXT | Handles multiple |

### API Models

| Provider | Model | Quality | Cost/Image | Video |
|----------|-------|---------|------------|-------|
| **OpenAI** | GPT-4o | Excellent | ~$0.01-0.03 | No |
| **Anthropic** | Claude 3.5 Sonnet | Excellent | ~$0.01-0.03 | No |
| **Google** | Gemini 1.5 Pro | Excellent | ~$0.01 | Yes |
| **Google** | Gemini 1.5 Flash | Good | ~$0.001 | Yes |

---

## Capabilities Matrix

| Capability | LLaVA | Qwen2-VL | GPT-4o | Claude 3.5 | Gemini 1.5 |
|------------|-------|----------|--------|------------|------------|
| Image understanding | ✓ | ✓ | ✓ | ✓ | ✓ |
| Multi-image | ✓ | ✓ | ✓ | ✓ | ✓ |
| OCR/text extraction | ○ | ✓ | ✓ | ✓ | ✓ |
| Document parsing | ○ | ✓ | ✓ | ✓ | ✓ |
| Chart understanding | ○ | ✓ | ✓ | ✓ | ✓ |
| Video | ✗ | Limited | ✗ | ✗ | ✓ |
| Grounding (coords) | ✗ | ✓ | ✗ | ✗ | ✗ |

Legend: ✓ Good | ○ Basic | ✗ No

---

## Reference Documents

### Decision Support
| Document | Purpose |
|----------|---------|
| `decision-tree.md` | Problem type selector |

### Problem Types
| Document | Purpose |
|----------|---------|
| `image-understanding.md` | General image analysis |
| `visual-qa.md` | Question answering about images |
| `document-ai.md` | Documents, screenshots, OCR |
| `video-understanding.md` | Video analysis |

### Cross-Cutting
| Document | Purpose |
|----------|---------|
| `model-selection.md` | Choosing the right model |
| `multimodal-prompting.md` | Image + text prompts |
| `deployment.md` | Local and API deployment |

---

## Usage Examples

### Example 1: "Analyze product photos"

**Situation**: E-commerce needs product descriptions from images.

**Approach**:
1. Problem type: Image Understanding
2. Local viable: Yes (not privacy critical)
3. Volume: High → Local preferred
4. Model: Qwen2-VL 7B

**Implementation**:
```python
prompt = """Describe this product for an e-commerce listing.
Include:
- Product type
- Key features
- Colors/materials visible
- Condition (if apparent)

Keep description under 100 words."""
```

### Example 2: "Extract data from invoices"

**Situation**: Parse invoices to structured data.

**Approach**:
1. Problem type: Document AI
2. Structured output needed: Yes
3. Quality critical: Yes → API or best local
4. Model: GPT-4o or Qwen2-VL 72B

**Implementation**:
```python
prompt = """Extract invoice data as JSON:
{
  "invoice_number": "string",
  "date": "YYYY-MM-DD",
  "vendor": "string",
  "total": number,
  "line_items": [{"description": "string", "amount": number}]
}

Only extract what's visible. Use null for missing fields."""
```

### Example 3: "Answer questions about diagrams"

**Situation**: Technical support bot that understands diagrams.

**Approach**:
1. Problem type: Visual QA
2. Diverse diagram types: Yes
3. Need reasoning: Yes
4. Model: GPT-4o or Claude 3.5 Sonnet

---

## Quality Standards

### What Makes Good VLM Integration

| Quality | Indicator |
|---------|-----------|
| **Task-appropriate** | VLM is right tool for job |
| **Well-prompted** | Clear instructions, examples |
| **Validated** | Outputs checked/verified |
| **Fallback-ready** | Handles failures gracefully |
| **Cost-aware** | Tracking image processing costs |

### Red Flags

- Using VLM for simple classification
- No image preprocessing
- Unbounded resolution (memory explosion)
- No output validation
- Missing fallback for failures

---

## 3090 Quick Reference

### What Fits

```
FP16 (full precision):
├── Phi-3 Vision 4B    ✓ (8GB)
├── LLaVA 1.6 7B       ✓ (14GB)
├── Qwen2-VL 7B        ✓ (16GB)
├── InternVL2 8B       ✓ (18GB)
├── LLaVA 1.6 13B      ✗ (26GB)
└── Qwen2-VL 72B       ✗ (150GB+)

Q4 Quantized:
├── LLaVA 1.6 13B      ✓ (8GB)
├── Qwen2-VL 72B       ✓ (24GB, tight)
└── InternVL2 40B      ✓ (20GB)
```

### Recommended Stack

```
Inference: Ollama, llama.cpp, or transformers
Quantization: GGUF or bitsandbytes
Image handling: PIL/Pillow
API wrapper: LiteLLM
```

---

## Image Preprocessing

### Resolution Guidelines

| Model | Max Resolution | Recommendation |
|-------|----------------|----------------|
| LLaVA | 672x672 | Resize if larger |
| Qwen2-VL | Dynamic | 1280 max dimension |
| GPT-4o | 2048x2048 | Compress if huge |
| Claude | 1568x1568 | Resize if larger |

### Preprocessing Code

```python
from PIL import Image
import io
import base64

def preprocess_image(image_path, max_size=1024):
    """Resize and encode image for VLM."""
    img = Image.open(image_path)

    # Resize if too large
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = tuple(int(d * ratio) for d in img.size)
        img = img.resize(new_size, Image.LANCZOS)

    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Encode to base64
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return base64.b64encode(buffer.getvalue()).decode()
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-01 | Initial version — 3090 optimized |
