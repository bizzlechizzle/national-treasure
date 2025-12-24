# VLM Model Selection

Choose the right vision model for your use case and hardware.

---

## Hardware Context: RTX 3090

You have **24GB VRAM**. This determines which models fit.

---

## Local Models (3090 Compatible)

### General Purpose

| Model | Size | VRAM (FP16) | VRAM (Q4) | Quality | Speed |
|-------|------|-------------|-----------|---------|-------|
| **Qwen2-VL 7B** | 8B | 16GB | 6GB | Excellent | Fast |
| **LLaVA 1.6 7B** | 7B | 14GB | 5GB | Very Good | Fast |
| **Phi-3 Vision** | 4B | 8GB | 3GB | Good | Very Fast |
| **InternVL2 8B** | 8B | 18GB | 7GB | Very Good | Fast |
| **MiniCPM-V 2.6** | 8B | 16GB | 6GB | Very Good | Fast |
| **Idefics2 8B** | 8B | 18GB | 7GB | Good | Fast |

### Larger Models (Quantized)

| Model | Size | VRAM (Q4) | Quality | Speed |
|-------|------|-----------|---------|-------|
| **Qwen2-VL 72B** | 72B | 24GB | Excellent | Slow |
| **LLaVA 1.6 34B** | 34B | 18GB | Excellent | Medium |
| **InternVL2 26B** | 26B | 14GB | Excellent | Medium |

### Document/OCR Focused

| Model | Size | VRAM | OCR Quality | Structure |
|-------|------|------|-------------|-----------|
| **Qwen2-VL 7B** | 8B | 16GB | Excellent | Excellent |
| **DocOwl 1.5** | 8B | 16GB | Excellent | Very Good |
| **Nougat** | 350M | 2GB | Good (academic) | PDF focused |

---

## API Models

### Comparison

| Provider | Model | Quality | Cost/Image | Notes |
|----------|-------|---------|------------|-------|
| **OpenAI** | GPT-4o | Excellent | ~$0.02 | Best general |
| **OpenAI** | GPT-4o-mini | Good | ~$0.005 | Budget option |
| **Anthropic** | Claude 3.5 Sonnet | Excellent | ~$0.02 | Strong reasoning |
| **Anthropic** | Claude 3 Haiku | Good | ~$0.005 | Fast, cheap |
| **Google** | Gemini 1.5 Pro | Excellent | ~$0.01 | Video support |
| **Google** | Gemini 1.5 Flash | Good | ~$0.001 | Very cheap |

### Video Support

Only **Gemini 1.5** natively supports video input. Others require frame sampling.

---

## Selection by Use Case

### General Image Understanding

| Requirement | Local | API |
|-------------|-------|-----|
| Fast + good | Qwen2-VL 7B | GPT-4o-mini |
| Best quality | Qwen2-VL 72B (Q4) | GPT-4o |
| Cheapest | Phi-3 Vision | Gemini Flash |

### Document/OCR

| Requirement | Local | API |
|-------------|-------|-----|
| Invoice parsing | Qwen2-VL 7B | GPT-4o |
| Screenshot text | Qwen2-VL 7B | Claude 3.5 |
| Academic PDFs | Nougat | GPT-4o |
| High accuracy | Qwen2-VL 72B | GPT-4o |

### Visual QA

| Requirement | Local | API |
|-------------|-------|-----|
| Simple questions | LLaVA 7B | GPT-4o-mini |
| Complex reasoning | Qwen2-VL 72B | Claude 3.5 |
| Grounding (coords) | Qwen2-VL | — |

### Video

| Requirement | Local | API |
|-------------|-------|-----|
| Basic understanding | Sample frames + VLM | Gemini 1.5 Pro |
| Action recognition | LLaVA-Video (if fits) | Gemini 1.5 Pro |
| Long video | Sample frames | Gemini 1.5 (1hr limit) |

---

## Running Local Models

### Ollama (Simplest)

```bash
# Install
curl -fsSL https://ollama.com/install.sh | sh

# Pull vision model
ollama pull llava:7b
ollama pull llava:13b

# Run
ollama run llava:7b "Describe this image" ./photo.jpg
```

**API usage:**

```python
import ollama
import base64

with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

response = ollama.chat(
    model='llava:7b',
    messages=[{
        'role': 'user',
        'content': 'Describe this image',
        'images': [image_data]
    }]
)
print(response['message']['content'])
```

### Transformers (Full Control)

```python
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from PIL import Image
import torch

# Load model
model = Qwen2VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2-VL-7B-Instruct",
    torch_dtype=torch.float16,
    device_map="auto"
)
processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-7B-Instruct")

# Process image
image = Image.open("photo.jpg")
messages = [
    {"role": "user", "content": [
        {"type": "image", "image": image},
        {"type": "text", "text": "Describe this image in detail."}
    ]}
]

# Generate
text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = processor(text=[text], images=[image], return_tensors="pt").to("cuda")

output = model.generate(**inputs, max_new_tokens=256)
result = processor.decode(output[0], skip_special_tokens=True)
```

### llama.cpp (GGUF)

```bash
# Build with vision support
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make LLAMA_CUDA=1

# Run with image
./llava-cli \
    -m models/llava-v1.6-7b.Q5_K_M.gguf \
    --mmproj models/llava-v1.6-7b-mmproj.gguf \
    --image photo.jpg \
    -p "Describe this image"
```

---

## API Usage

### OpenAI

```python
from openai import OpenAI
import base64

client = OpenAI()

with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this image"},
            {"type": "image_url", "image_url": {
                "url": f"data:image/jpeg;base64,{image_data}",
                "detail": "high"  # or "low" for cheaper
            }}
        ]
    }]
)
```

### Anthropic

```python
from anthropic import Anthropic
import base64

client = Anthropic()

with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": image_data
            }},
            {"type": "text", "text": "Describe this image"}
        ]
    }]
)
```

### Google Gemini

```python
import google.generativeai as genai
from PIL import Image

genai.configure(api_key="...")

model = genai.GenerativeModel('gemini-1.5-flash')
image = Image.open("image.jpg")

response = model.generate_content([
    "Describe this image",
    image
])
print(response.text)

# Video
video = genai.upload_file("video.mp4")
response = model.generate_content([
    "Summarize this video",
    video
])
```

---

## Model Capabilities

| Capability | Qwen2-VL | LLaVA | GPT-4o | Claude 3.5 | Gemini |
|------------|----------|-------|--------|------------|--------|
| Single image | ✓ | ✓ | ✓ | ✓ | ✓ |
| Multi-image | ✓ | ✓ | ✓ | ✓ | ✓ |
| OCR/text | ✓✓ | ✓ | ✓✓ | ✓✓ | ✓✓ |
| Documents | ✓✓ | ✓ | ✓✓ | ✓✓ | ✓✓ |
| Charts | ✓✓ | ○ | ✓✓ | ✓✓ | ✓✓ |
| Grounding | ✓ | ✗ | ✗ | ✗ | ✗ |
| Video | ○ | ✗ | ✗ | ✗ | ✓✓ |

Legend: ✓✓ Excellent | ✓ Good | ○ Basic | ✗ No

---

## Image Resolution

### Limits

| Model | Max Resolution | Best Practice |
|-------|----------------|---------------|
| LLaVA 7B | 672x672 | Resize larger |
| Qwen2-VL | Dynamic (tiles) | 1280 max dim |
| GPT-4o | 2048x2048 | Use "detail: low/high" |
| Claude | 1568x1568 | Resize if larger |
| Gemini | 3072x3072 | Very flexible |

### Resolution vs Cost (API)

```
GPT-4o detail settings:
- "low": 512x512, fixed cost (~$0.005)
- "high": up to 2048x2048, scales with size (~$0.02+)
- "auto": API decides

Recommendation: Use "low" for simple tasks, "high" for detail-critical
```

---

## Performance Benchmarks (3090)

| Model | Tokens/sec | Time per Image |
|-------|------------|----------------|
| Phi-3 Vision (FP16) | 60-80 | 1-2s |
| LLaVA 7B (FP16) | 40-60 | 2-4s |
| Qwen2-VL 7B (FP16) | 35-50 | 3-5s |
| Qwen2-VL 72B (Q4) | 10-15 | 10-20s |

---

## Recommendation Summary

| Need | Local Choice | API Choice |
|------|--------------|------------|
| **Start simple** | LLaVA 7B via Ollama | GPT-4o-mini |
| **Best quality** | Qwen2-VL 72B (Q4) | GPT-4o or Claude 3.5 |
| **Documents/OCR** | Qwen2-VL 7B | GPT-4o |
| **Speed** | Phi-3 Vision | Gemini Flash |
| **Video** | Frame sampling | Gemini 1.5 Pro |
| **Grounding** | Qwen2-VL | None (use detector) |

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| Qwen2-VL | HuggingFace | https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct |
| LLaVA | GitHub | https://github.com/haotian-liu/LLaVA |
| Ollama Vision | Docs | https://ollama.com/blog/vision-models |
| OpenAI Vision | Docs | https://platform.openai.com/docs/guides/vision |
