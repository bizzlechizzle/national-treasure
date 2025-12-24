# VLM Problem Type Decision Tree

Navigate from your goal to the right approach.

---

## Quick Decision Flow

```
What do you want to do with images?
│
├─► UNDERSTAND/DESCRIBE images
│   └─► image-understanding.md
│
├─► ANSWER QUESTIONS about images
│   └─► visual-qa.md
│
├─► EXTRACT DATA from documents
│   ├─► Invoices, receipts, forms
│   ├─► Screenshots, diagrams
│   ├─► Charts and graphs
│   └─► document-ai.md
│
├─► ANALYZE VIDEO content
│   └─► video-understanding.md
│
└─► DETECT/LOCATE objects
    └─► Use YOLO/Detectron (not VLM)
```

---

## Detailed Decision Matrix

### By Task

| I want to... | Problem Type | Best Approach |
|--------------|--------------|---------------|
| Describe what's in a photo | Image Understanding | VLM |
| Caption images for accessibility | Image Understanding | VLM |
| Understand scene context | Image Understanding | VLM |
| Answer "what color is the car?" | Visual QA | VLM |
| Count objects in image | Visual QA | VLM (or detector) |
| Compare two images | Visual QA | VLM (multi-image) |
| Extract text from documents | Document AI | VLM or OCR |
| Parse invoice/receipt data | Document AI | VLM |
| Understand flowcharts | Document AI | VLM |
| Read charts/graphs | Document AI | VLM |
| Summarize a video | Video | Gemini or frame sampling |
| Find moment in video | Video | Frame sampling + VLM |
| Detect faces | Face Detection | InsightFace (not VLM) |
| Find bounding boxes | Object Detection | YOLO (not VLM) |
| Segment objects | Segmentation | SAM (not VLM) |

### By Input Type

| Input | Problem Type | Notes |
|-------|--------------|-------|
| Photos | Image Understanding | General VLM |
| Screenshots | Document AI | Strong OCR needed |
| Scanned documents | Document AI | OCR-focused model |
| Charts/graphs | Document AI | Chart understanding |
| Diagrams | Document AI/Visual QA | Reasoning needed |
| Multi-image sets | Visual QA | Need multi-image support |
| Video | Video Understanding | Gemini or sample frames |

---

## VLM vs Specialized Models

### Use VLM When

- Need natural language output
- Task requires reasoning
- Multiple skills combined (OCR + understanding)
- Diverse image types
- Can't train custom model

### Use Specialized Models When

| Task | Specialized Model | Why Not VLM |
|------|-------------------|-------------|
| Object detection | YOLO, Detectron | Faster, bounding boxes |
| Face recognition | InsightFace | Privacy, accuracy |
| Image classification | EfficientNet | Faster, cheaper |
| OCR only | Tesseract, EasyOCR | Simpler, faster |
| Segmentation | SAM | Pixel-level masks |
| Real-time video | YOLO + tracking | Speed requirement |

### Hybrid Approaches

```
OCR + VLM: Extract text first, then reason with VLM
Detector + VLM: Detect objects, then describe with VLM
SAM + VLM: Segment first, then understand each segment
```

---

## Common Confusion Points

### Image Understanding vs Visual QA

| | Image Understanding | Visual QA |
|---|---------------------|-----------|
| Input | Image only | Image + question |
| Output | Description | Specific answer |
| Example | "Describe this image" | "How many people?" |
| Open/Closed | Open-ended | Often closed |

### Document AI vs OCR

| | Document AI | Pure OCR |
|---|-------------|----------|
| Output | Structured data | Raw text |
| Understanding | Yes | No |
| Layout | Understands | Just extracts |
| Tables | Parses structure | Text only |
| When | Need structure | Just need text |

### When to Sample Video vs Process Video

| | Frame Sampling + VLM | Native Video (Gemini) |
|---|----------------------|----------------------|
| Available | Any VLM | Gemini only |
| Motion | Missed | Captured |
| Cost | Image-based | Token-based |
| When | Scene understanding | Action understanding |

---

## By Use Case Domain

### E-commerce

| Task | Approach |
|------|----------|
| Product descriptions | Image Understanding |
| Condition assessment | Visual QA |
| Category classification | VLM or Classifier |
| Counterfeit detection | Visual QA |

### Finance

| Task | Approach |
|------|----------|
| Invoice parsing | Document AI |
| Receipt extraction | Document AI |
| Check reading | Document AI |
| Chart analysis | Document AI |

### Healthcare (Non-diagnostic)

| Task | Approach |
|------|----------|
| Medical form digitization | Document AI |
| Insurance card reading | Document AI |
| Appointment scheduling from fax | Document AI |

### Manufacturing

| Task | Approach |
|------|----------|
| Defect description | Visual QA |
| Assembly verification | Visual QA |
| Label reading | Document AI |
| Safety checklist | Visual QA |

### Media/Content

| Task | Approach |
|------|----------|
| Image captioning | Image Understanding |
| Content moderation | Visual QA |
| Video summarization | Video Understanding |
| Thumbnail selection | Visual QA |

---

## Decision Checklist

Before choosing approach:

- [ ] I know if I need text output or structured data
- [ ] I've considered if specialized models work
- [ ] I understand latency requirements
- [ ] I know if multi-image or video is needed
- [ ] I've considered privacy requirements

---

## Next Steps by Problem Type

| Problem Type | Next Document | Key Questions |
|--------------|---------------|---------------|
| Image Understanding | `image-understanding.md` | Detail level? Output format? |
| Visual QA | `visual-qa.md` | Open or closed questions? Grounding? |
| Document AI | `document-ai.md` | Document types? Structure needed? |
| Video | `video-understanding.md` | Gemini or sampling? Length? |
