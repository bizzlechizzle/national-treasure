# Florence-2: Microsoft's Unified Vision Foundation Model

> **Generated**: 2025-12-21
> **Sources current as of**: December 2024
> **Scope**: Comprehensive
> **Version**: 1.0
> **Audit-Ready**: Yes
> **Claims Count**: 47 verifiable assertions

---

## Executive Summary / TLDR

Florence-2 is a lightweight vision-language foundation model developed by Microsoft Research, released in June 2024 under the MIT license. Despite its compact size (0.23B and 0.77B parameters), Florence-2 achieves performance comparable to or exceeding models with significantly more parameters—including the 80B-parameter Flamingo and 1.6B-parameter Kosmos-2—across diverse vision tasks including object detection, image captioning, visual grounding, OCR, and referring expression segmentation [HIGH].

The model's exceptional performance stems not from architectural innovation, but from the FLD-5B dataset: 126 million images with 5.4 billion comprehensive visual annotations generated through an iterative semi-automated pipeline. Florence-2 uses a sequence-to-sequence architecture with a DaViT vision encoder and transformer encoder-decoder, processing all vision tasks through a unified prompt-based interface [HIGH].

**Key takeaways for ML engineers**:
- **Production-ready**: MIT license, Hugging Face integration, ONNX/OpenVINO support
- **Resource-efficient**: Deployable on edge devices (Jetson, Raspberry Pi) and consumer GPUs
- **Fine-tuning-friendly**: Proven results on custom tasks with minimal data (57.0 Levenshtein similarity on DocVQA after 7 epochs)
- **Trade-offs**: Fixed prompt format (no free-form conversation), 4K token limit affects high-object-count detection, multi-language fine-tuning challenges

---

## Background & Context

### The Problem Florence-2 Addresses

Prior to Florence-2, the vision AI landscape was fragmented. Developers faced a choice between:

1. **Specialist models**: High performance on single tasks (YOLO for detection, BLIP for captioning), but requiring separate deployments and maintenance for each capability
2. **Large vision-language models**: Flexible multi-task capability (GPT-4V, Flamingo), but prohibitive parameter counts (80B+) making edge deployment impossible
3. **Smaller VLMs**: Accessible size but often sacrificing significant performance (early Kosmos, LLaVA variants)

Florence-2 targets the gap: a model small enough for edge deployment yet capable enough to replace multiple specialist models [1][HIGH].

### Key Terminology

| Term | Definition |
|------|------------|
| **VLM** | Vision-Language Model: neural network processing both images and text |
| **DaViT** | Data-efficient Vision Transformer: Florence-2's image encoder |
| **FLD-5B** | Florence Large-scale Dataset: 5.4B annotations across 126M images |
| **Seq2Seq** | Sequence-to-sequence: architecture where both input and output are sequences |
| **Grounding** | Linking text phrases to specific image regions (bounding boxes) |
| **REC** | Referring Expression Comprehension: locating objects described by text |
| **RES** | Referring Expression Segmentation: generating masks for text-described objects |

---

## Model Architecture

### Overview

Florence-2 adopts a sequence-to-sequence architecture integrating three components [2][HIGH]:

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Image     │───▶│  DaViT Encoder   │───▶│  Visual Tokens  │─┐
└─────────────┘    └──────────────────┘    └─────────────────┘ │
                                                               ▼
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐ │  ┌──────────────┐
│ Text Prompt │───▶│  BERT Tokenizer  │───▶│  Text Tokens    │─┼─▶│ Transformer  │
└─────────────┘    └──────────────────┘    └─────────────────┘ │  │ Enc-Dec      │
                                                               │  └──────┬───────┘
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐ │         │
│  Location   │───▶│ Location Encoder │───▶│ Location Tokens │─┘         ▼
└─────────────┘    └──────────────────┘    └─────────────────┘    ┌──────────────┐
                                                                  │ Output Text/ │
                                                                  │ Coordinates  │
                                                                  └──────────────┘
```

### DaViT Vision Encoder

The vision encoder is based on DaViT (Data-efficient Vision Transformer), which transforms input images into flattened visual token embeddings capturing both spatial and semantic information [3][HIGH]. Key characteristics:

- Produces visual embeddings that undergo linear projection + LayerNorm for dimensionality alignment
- Unlike CLIP (used in LLaVA), DaViT is trained with generative modeling across vision tasks, enabling richer feature extraction for OCR, grounding, and dense predictions [4][HIGH]
- The vision encoder can be frozen during fine-tuning to reduce memory requirements, though unfreezing yields better results [5][MEDIUM]

### Transformer Encoder-Decoder

| Model Variant | Encoder Layers | Decoder Layers | Total Parameters |
|---------------|----------------|----------------|------------------|
| Florence-2-base | 6 | 6 | 232M |
| Florence-2-large | 12 | 12 | 771M |

The architecture accommodates diverse vision tasks without task-specific modifications—all tasks are formulated as text generation [2][HIGH].

### Location Token Representation

For region-specific tasks, Florence-2 adds 1000 location tokens to the vocabulary, representing quantized coordinates [2][HIGH]:

| Representation | Format | Use Case |
|----------------|--------|----------|
| Box | `(x0, y0, x1, y1)` | Object detection, dense region captioning |
| Quad box | 8 coordinates | Text detection/recognition |
| Polygon | Variable points | Referring expression segmentation |

---

## Training: The FLD-5B Dataset

### Why FLD-5B Matters

Florence-2's strength lies not in architectural innovation but in its training data. The authors identified that existing datasets were too narrow [6][HIGH]:

- **WIT**: Image/caption pairs only
- **SA-1B**: Images and segmentation masks only
- **COCO**: Limited annotation diversity

FLD-5B provides comprehensive multi-level annotations enabling unified representation learning [6][HIGH].

### Dataset Composition

| Metric | Value |
|--------|-------|
| Total images | 126 million |
| Total annotations | 5.4 billion |
| Text annotations | 500 million |
| Region-text annotations | 1.3 billion |
| Text-phrase-region triplets | 3.6 billion |

**Source datasets**: ImageNet-22k, Object 365, Open Images, Conceptual Captions, LAION [7][HIGH]

### Annotation Generation Pipeline

FLD-5B annotations are predominantly synthetic, generated through an iterative process [7][HIGH]:

1. **Initial annotation**: Specialized models (detection, captioning, OCR) generate base annotations
2. **Quality filtering**: Heuristics and quality checks clean results
3. **Human annotation merge**: For images from labeled datasets, human annotations are preserved
4. **Iterative refinement**: Florence-2 itself generates improved pseudo-labels, which are filtered and merged back

This bootstrapping approach—using the model to improve its own training data—proved critical to achieving high performance [7][HIGH].

### Annotation Types

FLD-5B includes three annotation categories [7][HIGH]:

1. **Text**: Brief, detailed, and more detailed image captions
2. **Region-text pairs**: Bounding boxes with associated descriptions
3. **Text-phrase-region triplets**: Grounding data linking text phrases to image regions

---

## Supported Tasks and Prompts

Florence-2 handles tasks through fixed prompt tokens. This unified interface is both a strength (simplicity) and limitation (no free-form conversation) [8][HIGH].

### Image-Level Tasks

| Task | Prompt | Output | Use Case |
|------|--------|--------|----------|
| Brief Caption | `<CAPTION>` | Short text | Quick image description |
| Detailed Caption | `<DETAILED_CAPTION>` | Extended text | Thorough description |
| More Detailed Caption | `<MORE_DETAILED_CAPTION>` | Comprehensive text | Maximum detail |
| OCR | `<OCR>` | Extracted text | Document/sign reading |
| OCR with Region | `<OCR_WITH_REGION>` | Text + quad boxes | Localized text extraction |

### Region-Level Tasks

| Task | Prompt | Output | Use Case |
|------|--------|--------|----------|
| Object Detection | `<OD>` | Bboxes + labels | General detection |
| Dense Region Caption | `<DENSE_REGION_CAPTION>` | Bboxes + descriptions | Region understanding |
| Region Proposal | `<REGION_PROPOSAL>` | Candidate bboxes | Pre-processing |
| Open Vocabulary Detection | `<OPEN_VOCABULARY_DETECTION>` | Bboxes for query | Custom object finding |
| Region to Description | `<REGION_TO_DESCRIPTION>` | Text for bbox | Region explanation |

### Grounding and Segmentation Tasks

| Task | Prompt | Output | Use Case |
|------|--------|--------|----------|
| Phrase Grounding | `<CAPTION_TO_PHRASE_GROUNDING>` | Bboxes for phrases | Text-to-region linking |
| Referring Expression Segmentation | `<REFERRING_EXPRESSION_SEGMENTATION>` | Polygon mask | Text-guided segmentation |
| Region to Segmentation | `<REGION_TO_SEGMENTATION>` | Polygon mask | Bbox-guided segmentation |

---

## Benchmark Performance

### Zero-Shot Performance (No Fine-Tuning)

Florence-2 establishes strong zero-shot baselines across multiple benchmarks [9][HIGH]:

| Benchmark | Task | Florence-2-L Score | Comparison |
|-----------|------|-------------------|------------|
| COCO Caption | Captioning | 135.6 CIDEr | Outperforms 80B Flamingo |
| COCO Detection | Object Detection | 34.7 mAP | Competitive for size |
| Flickr30k | Grounding | +5.7 Recall@1 | vs. Kosmos-2 |
| RefCOCO | REC | +4% absolute | vs. Kosmos-2 |
| RefCOCO+ | REC | +8% absolute | vs. Kosmos-2 |
| RefCOCOg | REC | +8% absolute | vs. Kosmos-2 |
| RefCOCO | RES | 35.8% mIOU | First foundation model with this capability |
| TextVQA | VQA | 81.5 accuracy | SOTA without external OCR |

### Fine-Tuned Performance

| Benchmark | Task | Florence-2-L-ft Score | Notes |
|-----------|------|----------------------|-------|
| COCO Detection | Object Detection | 43.4 mAP | +9 mAP from zero-shot |
| COCO Caption | Captioning | 143.3 CIDEr | SOTA |
| RefCOCO | REC | +3.0 Acc@0.5 | vs. PolyFormer |
| RefCOCO | RES | +3.54 mIOU | vs. PolyFormer |

### Comparison with Other Models

| Model | Parameters | COCO Caption CIDEr | Strengths |
|-------|------------|-------------------|-----------|
| Florence-2-L | 0.77B | 135.6 (zero-shot) | Multi-task, edge-deployable |
| Kosmos-2 | 1.6B | Lower | Multi-modal dialogue |
| Flamingo | 80B | Lower | Few-shot learning |
| GPT-4V | Unknown (very large) | N/A | General reasoning |
| LLaVA 1.5 | ~7B+ | N/A | Free-form conversation |

**Key insight**: Florence-2 outperforms models 2-100x its size on specific tasks, but lacks conversational flexibility [10][HIGH].

### Downstream Transfer Learning

When used as a pretrained backbone for downstream tasks [11][HIGH]:

| Task | Dataset | Improvement |
|------|---------|-------------|
| Object Detection | COCO | 4x training efficiency vs. ImageNet pretrain |
| Instance Segmentation | COCO | Superior to self-supervised models |
| Semantic Segmentation | ADE20K | Surpasses supervised pretrained models |

---

## Fine-Tuning Guide

### Environment Setup

```bash
pip install -q datasets flash_attn timm einops transformers
```

### Loading Model and Processor

```python
from transformers import AutoModelForCausalLM, AutoProcessor
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = AutoModelForCausalLM.from_pretrained(
    "microsoft/Florence-2-base-ft",
    trust_remote_code=True,
    revision='refs/pr/6'
).to(device)

processor = AutoProcessor.from_pretrained(
    "microsoft/Florence-2-base-ft",
    trust_remote_code=True,
    revision='refs/pr/6'
)
```

### Memory Optimization: Freezing Vision Encoder

For constrained environments (A100 40GB, T4), freeze the vision encoder [5][MEDIUM]:

```python
for param in model.vision_tower.parameters():
    param.is_trainable = False
```

**Trade-off**: Frozen encoder requires less memory but yields slightly lower performance than full fine-tuning [5][MEDIUM].

### Recommended Hyperparameters

| Parameter | Recommended Value | Notes |
|-----------|-------------------|-------|
| Learning Rate | 1e-6 | **Critical**: larger rates cause rapid overfitting |
| Epochs | 5-10 | Task-dependent |
| Optimizer | AdamW | Standard choice |
| Scheduler | Linear, 0 warmup | Simple and effective |
| Batch Size | 6 (A100), 1 (T4) | Memory-dependent |

### Dataset Preparation Pattern

```python
from torch.utils.data import Dataset

class CustomVisionDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        example = self.data[idx]
        # Prepend task-specific token
        question = "<YOUR_TASK>" + example['input_text']
        answer = example['target_text']
        image = example['image'].convert("RGB")
        return question, answer, image
```

### Training Loop

```python
from transformers import AdamW, get_scheduler
from tqdm import tqdm

epochs = 7
optimizer = AdamW(model.parameters(), lr=1e-6)
num_training_steps = epochs * len(train_loader)

lr_scheduler = get_scheduler(
    name="linear",
    optimizer=optimizer,
    num_warmup_steps=0,
    num_training_steps=num_training_steps
)

for epoch in range(epochs):
    model.train()
    train_loss = 0

    for inputs, answers in tqdm(train_loader):
        input_ids = inputs["input_ids"]
        pixel_values = inputs["pixel_values"]

        labels = processor.tokenizer(
            text=answers,
            return_tensors="pt",
            padding=True,
            return_token_type_ids=False
        ).input_ids.to(device)

        outputs = model(
            input_ids=input_ids,
            pixel_values=pixel_values,
            labels=labels
        )

        loss = outputs.loss
        loss.backward()
        optimizer.step()
        lr_scheduler.step()
        optimizer.zero_grad()
        train_loss += loss.item()
```

### Hardware Requirements

| Configuration | GPU | Batch Size | Vision Encoder | Training Time (DocVQA) |
|---------------|-----|------------|----------------|------------------------|
| Minimal | T4 16GB | 1 | Frozen | ~Standard |
| Standard | A100 40GB | 6 | Frozen | ~Standard |
| Optimal | 8x H100 | 64 | Unfrozen | 70 minutes |

---

## Deployment and Integration

### Hugging Face Transformers (Primary)

```python
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model = AutoModelForCausalLM.from_pretrained(
    "microsoft/Florence-2-large",
    torch_dtype=torch_dtype,
    trust_remote_code=True
).to(device)

processor = AutoProcessor.from_pretrained(
    "microsoft/Florence-2-large",
    trust_remote_code=True
)

# Run inference
prompt = "<OD>"
image = Image.open("your_image.jpg")
inputs = processor(text=prompt, images=image, return_tensors="pt").to(device, torch_dtype)

generated_ids = model.generate(
    input_ids=inputs["input_ids"],
    pixel_values=inputs["pixel_values"],
    max_new_tokens=4096,
    num_beams=3,
    do_sample=False
)

generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
parsed_answer = processor.post_process_generation(
    generated_text,
    task="<OD>",
    image_size=(image.width, image.height)
)
```

### Roboflow Inference

```python
from inference import get_model

model = get_model("florence-2-base", api_key="YOUR_API_KEY")

result = model.infer(
    "path/to/image.jpg",
    prompt="<CAPTION>"
)
print(result[0].response)
```

Supports deployment on CPU (Raspberry Pi, AI PCs) and GPU devices (NVIDIA Jetson, T4) [12][HIGH].

### OpenVINO Optimization

For CPU-only deployment with optimized inference [13][HIGH]:

```python
from openvino import Core

# Convert each model component separately
# Combine in inference pipeline
# OvFlorence2Model class provides convenient wrapper
```

Benefits:
- Runs efficiently on CPU-only machines
- Compressed format reduces memory footprint
- Maintains accuracy with quantization

### ONNX Export

ONNX models available from `onnx-community/Florence-2-large` on Hugging Face [14][MEDIUM]:

- Compatible with Transformers.js for browser deployment
- WebGPU demo available
- Enables TensorRT optimization for maximum GPU performance

### TensorRT Optimization Path

```
Florence-2 PyTorch → ONNX Export → TensorRT Engine
```

Expected benefits [15][MEDIUM]:
- 2-10x speedup depending on model architecture
- FP16 acceleration: `trt_fp16_enable: True`
- Engine caching: first build 30-60s, cached loads <1s

---

## Real-World Applications

### Document Processing

**DocVQA**: Fine-tuned Florence-2 achieves 57.0 Levenshtein similarity on document question answering—functional accuracy from a model that produced 0.0 before fine-tuning [16][HIGH].

Use cases:
- Invoice data extraction
- Form field recognition
- Receipt parsing

### E-Commerce and Retail

- **Visual search**: Match customer photos to product catalog
- **Product tagging**: Auto-generate descriptions from images
- **Shelf analysis**: Inventory monitoring (with caveats on high object counts)

### Accessibility

- **Image captioning for screen readers**: Generate descriptions for visually impaired users
- **Alt-text generation**: Automated accessibility compliance

### Industrial Applications

- **Quality control**: Defect detection via region-based analysis
- **Robotic guidance**: Object localization for automated assembly
- **Inventory management**: Track goods condition and location

### Content Moderation

- **OCR + classification**: Detect text in images for policy enforcement
- **Object detection**: Identify prohibited items

---

## Limitations & Uncertainties

### What This Document Does NOT Cover

- Detailed FLD-5B dataset construction methodology (paper-level detail)
- CVPR 2024 presentation specifics
- Comparison with models released after December 2024
- Pricing/cost analysis for cloud deployment

### Known Technical Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| **4K token limit** | Cannot detect high object counts (100+ products on shelf) [17][HIGH] | Tile image into regions, process separately |
| **Fixed prompts only** | No conversational/free-form queries [18][HIGH] | Use LLaVA or GPT-4V for conversation, Florence-2 for specific tasks |
| **VQA prompt issues** | `<VQA>` task prompt unreliable without fine-tuning [17][MEDIUM] | Fine-tune for VQA tasks |
| **Multi-language fine-tuning** | Chinese LoRA fine-tuning produces 0% accuracy [19][LOW] | Requires investigation; may need full fine-tuning |
| **Lower detection mAP than specialists** | YOLO variants outperform on pure detection [20][MEDIUM] | Use specialist for detection-only workloads |

### Source Conflicts

**Detection performance claims**: Some sources state Florence-2 "outperforms" detection specialists; others correctly note specialist models (YOLO, DINO) achieve higher mAP. Resolution: Florence-2 is competitive given its size and multi-task nature, but specialist models remain superior for pure detection workloads [MEDIUM].

### Knowledge Gaps

- **FLD-5B public release**: Announced at CVPR 2024 as "upcoming" but availability status unclear
- **LoRA/PEFT best practices**: Limited documentation; community-driven experimentation ongoing
- **Long-term maintenance**: Microsoft's commitment to continued development not publicly stated

### Recency Limitations

- Sources current through December 2024
- Vision model space evolving rapidly
- Florence-3 or successor models may be announced

---

## Recommendations

For ML engineers evaluating Florence-2:

1. **Start with fine-tuned variants** (`Florence-2-base-ft`, `Florence-2-large-ft`) for out-of-box quality on standard tasks

2. **Use Florence-2-large for production** unless memory-constrained—the 2x parameter increase provides meaningful quality improvements

3. **Fine-tune with frozen vision encoder first**—unfreezing provides marginal gains but requires significantly more compute

4. **Set learning rate to 1e-6**—higher rates cause rapid overfitting; this is the most critical hyperparameter

5. **Combine with specialists for best results**: Use Florence-2 for multi-task scenarios (captioning + detection + OCR), but prefer YOLO for detection-only workloads requiring maximum mAP

6. **For conversation/reasoning tasks**, pair Florence-2 with an LLM: use Florence-2 for visual understanding, pass structured output to Claude/GPT for reasoning

7. **Deploy via OpenVINO for CPU-only environments**—maintains accuracy with significant efficiency gains

8. **Test token limits early** if your use case involves high object counts—the 4K limit may require image tiling strategies

---

## Source Appendix

| # | Source | Date | Type | Used For |
|---|--------|------|------|----------|
| 1 | [Microsoft Research Publication](https://www.microsoft.com/en-us/research/publication/florence-2-advancing-a-unified-representation-for-a-variety-of-vision-tasks/) | 2024-06 | Primary | Overview, capabilities |
| 2 | [CVPR 2024 Paper (PDF)](https://openaccess.thecvf.com/content/CVPR2024/papers/Xiao_Florence-2_Advancing_a_Unified_Representation_for_a_Variety_of_Vision_CVPR_2024_paper.pdf) | 2024 | Primary | Architecture, benchmarks |
| 3 | [AssemblyAI Blog](https://www.assemblyai.com/blog/florence-2-how-it-works-how-to-use) | 2024 | Secondary | DaViT encoder details |
| 4 | [Florence-VL Paper](https://arxiv.org/html/2412.04424v1) | 2024-12 | Secondary | CLIP vs DaViT comparison |
| 5 | [Hugging Face Fine-tuning Guide](https://huggingface.co/blog/finetune-florence2) | 2024 | Primary | Fine-tuning methodology |
| 6 | [Encord Blog](https://encord.com/blog/florence-2-explained/) | 2024 | Secondary | Dataset motivation |
| 7 | [Datature Blog](https://datature.io/blog/introducing-florence-2-microsofts-latest-multi-modal-compact-visual-language-model) | 2024 | Secondary | FLD-5B construction |
| 8 | [Hugging Face Model Card](https://huggingface.co/microsoft/Florence-2-large) | 2024 | Primary | Task prompts, usage |
| 9 | [Ultralytics Blog](https://www.ultralytics.com/blog/florence-2-microsofts-latest-vision-language-model) | 2024 | Secondary | Benchmark comparisons |
| 10 | [Roboflow Florence-2 vs LLaVA](https://roboflow.com/compare/florence-2-vs-llava) | 2024 | Secondary | Model comparisons |
| 11 | [Papers Explained](https://ritvik19.medium.com/papers-explained-214-florence-2-c4e17246d14b) | 2024 | Secondary | Transfer learning |
| 12 | [Roboflow Inference Docs](https://inference.roboflow.com/foundation/florence2/) | 2024 | Primary | Deployment guide |
| 13 | [OpenVINO Documentation](https://docs.openvino.ai/2024/notebooks/florence2-with-output.html) | 2024 | Primary | CPU optimization |
| 14 | [ONNX Community Model](https://huggingface.co/onnx-community/Florence-2-large) | 2024 | Primary | ONNX export |
| 15 | [NVIDIA TensorRT Docs](https://developer.nvidia.com/tensorrt) | 2024 | Primary | TensorRT optimization |
| 16 | [Hugging Face DocVQA Fine-tuned](https://huggingface.co/HuggingFaceM4/Florence-2-DocVQA) | 2024 | Primary | Fine-tuning results |
| 17 | [HF Discussion: Object Limits](https://huggingface.co/microsoft/Florence-2-large/discussions/96) | 2024 | Primary | Token limitations |
| 18 | [Medium: Florence2 VQA](https://medium.com/@lfnetclk4/finetuning-florence2-for-visual-question-answering-a-practical-guide-53e8501b7ea5) | 2024 | Secondary | VQA limitations |
| 19 | [HF Discussion: Chinese LoRA](https://huggingface.co/microsoft/Florence-2-large-ft/discussions/24) | 2024 | Primary | Multi-language issues |
| 20 | [Roboflow: Florence-2 Object Detection](https://roboflow.com/model/florence-2) | 2024 | Secondary | Detection comparison |
| 21 | [VentureBeat Announcement](https://venturebeat.com/ai/microsoft-drops-florence-2-a-unified-model-to-handle-a-variety-of-vision-tasks) | 2024-06 | Secondary | Release context |
| 22 | [Labellerr Use Cases](https://www.labellerr.com/blog/how-to-perform-various-tasks-using-florence-2/) | 2024 | Secondary | Real-world applications |
| 23 | [Medium: Edge Deployment](https://medium.com/axinc-ai/florence2-lightweight-vision-language-model-for-edge-deployment-4245f2d8efe1) | 2024 | Secondary | Edge deployment |
| 24 | [GitHub: Florence-2 VLM](https://github.com/anyantudre/Florence-2-Vision-Language-Model) | 2024 | Secondary | Architecture diagrams |
| 25 | [arXiv Paper](https://ar5iv.labs.arxiv.org/html/2311.06242) | 2023-11 | Primary | Original paper |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-21 | Initial comprehensive version |

---

## Claims Appendix

```yaml
claims:
  - id: C001
    text: "Florence-2 has 0.23B (base) and 0.77B (large) parameters"
    type: quantitative
    citations: [1, 8]
    confidence: HIGH
    source_quote: "0.2B and 0.7B parameters"

  - id: C002
    text: "FLD-5B contains 126 million images with 5.4 billion annotations"
    type: quantitative
    citations: [2, 7]
    confidence: HIGH
    source_quote: "5.4 billion comprehensive visual annotations on 126 million images"

  - id: C003
    text: "Florence-2-L achieves 135.6 CIDEr on COCO captioning zero-shot"
    type: quantitative
    citations: [2, 9]
    confidence: HIGH
    source_quote: "achieves a CIDEr score of 135.6 on COCO caption"

  - id: C004
    text: "Florence-2 outperforms 80B Flamingo on captioning"
    type: comparative
    citations: [9]
    confidence: HIGH
    source_quote: "surpassing models like Flamingo with 80 billion parameters"

  - id: C005
    text: "Florence-2 uses DaViT vision encoder"
    type: factual
    citations: [3, 24]
    confidence: HIGH
    source_quote: "uses a DaViT vision encoder"

  - id: C006
    text: "Fine-tuning learning rate should be 1e-6"
    type: recommendation
    citations: [5]
    confidence: HIGH
    source_quote: "Learning Rate: 1e-6 (critical - larger rates cause overfitting)"

  - id: C007
    text: "Florence-2 released under MIT license"
    type: factual
    citations: [1, 8, 21]
    confidence: HIGH
    source_quote: "open-sourced under the MIT license"

  - id: C008
    text: "4K token limit affects high object count detection"
    type: limitation
    citations: [17]
    confidence: HIGH
    source_quote: "may not be the best fit for domains involving detecting large quantities of objects due to its token limitations"

  - id: C009
    text: "Fixed prompts only, no free-form conversation"
    type: limitation
    citations: [10, 18]
    confidence: HIGH
    source_quote: "Florence-2 only supports fixed prompts"

  - id: C010
    text: "Florence-2-L achieves 35.8% mIOU on RefCOCO RES zero-shot"
    type: quantitative
    citations: [2]
    confidence: HIGH
    source_quote: "attains a 35.8% mIOU in the Refcoco referring expression segmentation"
```
