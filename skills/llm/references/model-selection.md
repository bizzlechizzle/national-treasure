# Model Selection

Choose the right LLM for your use case and hardware.

---

## Hardware Context: RTX 3090

You have **24GB VRAM**. This guide is optimized for that constraint.

```
24GB VRAM Budget:
├── Model weights: ~20-22GB max
├── KV cache: 1-3GB (context dependent)
└── Overhead: 1-2GB
```

---

## Decision Framework

### Step 1: Local or API?

| Choose Local If | Choose API If |
|-----------------|---------------|
| Data privacy required | Need best quality (GPT-4, Claude) |
| High volume (>1M tokens/day) | Unpredictable volume |
| Need offline capability | Quick prototyping |
| Predictable costs preferred | Don't want to manage infrastructure |
| Latency critical | Budget for simplicity |

### Step 2: Quality vs Speed Tradeoff

```
Quality
   ↑
   │  ┌─────────────────┐
   │  │ Claude 3.5      │  API
   │  │ GPT-4o          │
   │  └─────────────────┘
   │  ┌─────────────────┐
   │  │ Llama 3.1 70B   │  Local (Q4, slow)
   │  │ Qwen 2.5 72B    │
   │  └─────────────────┘
   │  ┌─────────────────┐
   │  │ Qwen 2.5 14B    │  Local (fast)
   │  │ Llama 3.1 8B    │
   │  └─────────────────┘
   └──────────────────────────► Speed
```

---

## Local Models (3090 Compatible)

### General Purpose

| Model | Params | VRAM (Q4) | Quality | Speed | Best For |
|-------|--------|-----------|---------|-------|----------|
| **Llama 3.1 8B** | 8B | 5GB | Good | Very Fast | General, chat |
| **Llama 3.1 70B** | 70B | 22GB | Excellent | Slow | Quality-critical |
| **Mistral 7B v0.3** | 7B | 4GB | Good | Very Fast | General, efficient |
| **Mixtral 8x7B** | 47B (MoE) | 22GB | Very Good | Medium | Balance |
| **Qwen 2.5 7B** | 7B | 4GB | Good | Very Fast | Multilingual |
| **Qwen 2.5 14B** | 14B | 8GB | Very Good | Fast | Sweet spot |
| **Qwen 2.5 72B** | 72B | 24GB | Excellent | Slow | Quality-critical |
| **Phi-3 Medium 14B** | 14B | 8GB | Very Good | Fast | Reasoning |

### Code Specialized

| Model | Params | VRAM (Q4) | Quality | Best For |
|-------|--------|-----------|---------|----------|
| **DeepSeek-Coder-V2-Lite** | 16B | 9GB | Excellent | Code generation |
| **Qwen 2.5-Coder 14B** | 14B | 8GB | Excellent | Code + explanation |
| **CodeLlama 34B** | 34B | 18GB | Very Good | Code completion |
| **StarCoder2 15B** | 15B | 9GB | Very Good | Multi-language |

### Long Context

| Model | Context | VRAM (Q4) | Notes |
|-------|---------|-----------|-------|
| **Llama 3.1 8B** | 128K | 5GB + KV | Native long context |
| **Qwen 2.5 7B** | 128K | 4GB + KV | Native long context |
| **Mistral 7B** | 32K | 4GB + KV | Sliding window |
| **Yi-34B-200K** | 200K | 18GB + KV | Extreme context |

**Note**: Long context = more KV cache = more VRAM. 128K context on 7B model can use 4-8GB extra.

### Embedding Models

| Model | Dimensions | VRAM | Quality | Speed |
|-------|------------|------|---------|-------|
| **bge-large-en-v1.5** | 1024 | 2GB | Excellent | Fast |
| **bge-m3** | 1024 | 2GB | Excellent | Fast |
| **nomic-embed-text** | 768 | 1GB | Very Good | Very Fast |
| **mxbai-embed-large** | 1024 | 2GB | Excellent | Fast |

---

## API Models

### Top Tier

| Provider | Model | Quality | Cost/1M tokens | Speed | Best For |
|----------|-------|---------|----------------|-------|----------|
| **Anthropic** | Claude 3.5 Sonnet | Excellent | $15 in / $75 out | Fast | General, coding |
| **OpenAI** | GPT-4o | Excellent | $5 in / $15 out | Fast | General, vision |
| **Google** | Gemini 1.5 Pro | Excellent | $3.50 in / $10.50 out | Medium | Long context |
| **Anthropic** | Claude 3 Opus | Best | $15 in / $75 out | Slow | Complex reasoning |

### Value Tier

| Provider | Model | Quality | Cost/1M tokens | Speed | Best For |
|----------|-------|---------|----------------|-------|----------|
| **OpenAI** | GPT-4o-mini | Very Good | $0.15 in / $0.60 out | Very Fast | Volume |
| **Anthropic** | Claude 3 Haiku | Good | $0.25 in / $1.25 out | Very Fast | Volume |
| **Google** | Gemini 1.5 Flash | Good | $0.075 in / $0.30 out | Very Fast | Volume |
| **DeepSeek** | DeepSeek-V2 | Good | $0.14 in / $0.28 out | Fast | Budget |

### Specialized

| Provider | Model | Specialty | Notes |
|----------|-------|-----------|-------|
| **OpenAI** | o1 | Reasoning | Chain-of-thought built in |
| **Anthropic** | Claude | Long context | 200K native |
| **Google** | Gemini | Multimodal | Good at vision |
| **Cohere** | Command R+ | RAG | Built-in retrieval |

---

## Selection by Use Case

### Chat/Assistant

| Requirement | Local | API |
|-------------|-------|-----|
| Basic chat | Llama 3.1 8B | GPT-4o-mini |
| Quality chat | Qwen 2.5 14B | Claude 3.5 Sonnet |
| Best quality | Llama 3.1 70B (Q4) | GPT-4o / Claude 3.5 |

### Code Generation

| Requirement | Local | API |
|-------------|-------|-----|
| Fast completion | DeepSeek-Coder-V2-Lite | GPT-4o-mini |
| Best quality | Qwen 2.5-Coder 14B | Claude 3.5 Sonnet |
| Multi-file | Qwen 2.5 72B (Q4) | GPT-4o |

### RAG / Knowledge Base

| Requirement | Local | API |
|-------------|-------|-----|
| Basic QA | Llama 3.1 8B + bge-large | GPT-4o-mini |
| Long documents | Llama 3.1 8B (128K) | Gemini 1.5 Pro (1M) |
| Best accuracy | Qwen 2.5 14B + bge-m3 | Claude 3.5 Sonnet |

### Classification / Extraction

| Requirement | Local | API |
|-------------|-------|-----|
| Simple categories | Llama 3.1 8B | GPT-4o-mini |
| Complex schemas | Qwen 2.5 14B | GPT-4o (structured) |
| High volume | Llama 3.1 8B | Claude 3 Haiku |

### Summarization

| Requirement | Local | API |
|-------------|-------|-----|
| Short docs | Any 7-8B | GPT-4o-mini |
| Long docs | Qwen 2.5 7B (128K) | Gemini 1.5 Flash |
| High quality | Qwen 2.5 14B | Claude 3.5 Sonnet |

---

## Quantization Guide

### Formats

| Format | Tool | Compatibility |
|--------|------|---------------|
| **GGUF** | llama.cpp, Ollama | Best for CPU/GPU hybrid |
| **AWQ** | vLLM, TGI | GPU optimized |
| **GPTQ** | vLLM, AutoGPTQ | GPU optimized |
| **bitsandbytes** | Transformers | Easy, on-the-fly |

### Quality vs Size

| Quantization | Bits | Size vs FP16 | Quality | When to Use |
|--------------|------|--------------|---------|-------------|
| FP16 | 16 | 100% | Best | Fits in VRAM |
| Q8_0 | 8 | 50% | Excellent | Slight squeeze |
| Q6_K | 6 | 40% | Very Good | Good balance |
| Q5_K_M | 5 | 35% | Good | Most common |
| Q4_K_M | 4 | 25% | Acceptable | Larger models |
| Q3_K_M | 3 | 20% | Degraded | Last resort |

### 3090 Model Fitting Guide

```python
# Rule of thumb for GGUF
def estimate_vram_gguf(params_billions, quant_bits):
    """Estimate VRAM in GB."""
    bytes_per_param = quant_bits / 8
    model_size_gb = params_billions * bytes_per_param
    overhead = 2  # GB for KV cache, etc.
    return model_size_gb + overhead

# Examples
print(estimate_vram_gguf(7, 4))   # 7B Q4 → ~5.5GB
print(estimate_vram_gguf(70, 4))  # 70B Q4 → ~22GB
print(estimate_vram_gguf(14, 5))  # 14B Q5 → ~10.75GB
```

---

## Inference Engines

### Local Inference

| Engine | Best For | Pros | Cons |
|--------|----------|------|------|
| **Ollama** | Easy setup | Simple, batteries included | Less control |
| **llama.cpp** | GGUF models | CPU+GPU, efficient | CLI focused |
| **vLLM** | High throughput | Fast, batching | GPU memory hungry |
| **TGI** | Production | Robust, batching | Complex setup |
| **Transformers** | Flexibility | Full control | Slower |

### Ollama Quick Start

```bash
# Install
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull llama3.1:8b

# Run
ollama run llama3.1:8b

# API (default port 11434)
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Hello!"
}'
```

### vLLM Quick Start

```bash
# Install
pip install vllm

# Serve
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --dtype float16 \
    --max-model-len 8192

# Use OpenAI-compatible API
curl http://localhost:8000/v1/completions -d '{
  "model": "meta-llama/Llama-3.1-8B-Instruct",
  "prompt": "Hello!",
  "max_tokens": 100
}'
```

### llama.cpp Quick Start

```bash
# Build
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make LLAMA_CUDA=1

# Run
./main -m models/llama-3.1-8b.Q5_K_M.gguf \
    -p "Hello!" \
    -n 100 \
    -ngl 99  # Offload all layers to GPU
```

---

## API Client Setup

### LiteLLM (Unified Interface)

```python
# pip install litellm

from litellm import completion

# Works with any provider
response = completion(
    model="gpt-4o-mini",  # or "claude-3-sonnet-20240229", "ollama/llama3.1"
    messages=[{"role": "user", "content": "Hello!"}]
)

# Switch models without code changes
import os
os.environ["OPENAI_API_KEY"] = "..."
os.environ["ANTHROPIC_API_KEY"] = "..."

# Use local Ollama
response = completion(
    model="ollama/llama3.1:8b",
    messages=[{"role": "user", "content": "Hello!"}],
    api_base="http://localhost:11434"
)
```

### Direct SDK Usage

```python
# OpenAI
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Anthropic
from anthropic import Anthropic
client = Anthropic()
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## Model Comparison Checklist

Before choosing:

- [ ] VRAM requirement fits 24GB (with headroom)
- [ ] Quality sufficient for task (test on examples)
- [ ] Speed acceptable (tokens/sec)
- [ ] Context length sufficient
- [ ] Cost within budget (API) or one-time (local)
- [ ] License permits commercial use
- [ ] Community/support available

---

## Quick Recommendations

### "Just tell me what to use"

| Scenario | Recommendation |
|----------|----------------|
| **Starting out** | Ollama + Llama 3.1 8B |
| **Need better quality** | Ollama + Qwen 2.5 14B |
| **Best local quality** | vLLM + Llama 3.1 70B (Q4) |
| **Code focused** | Ollama + DeepSeek-Coder-V2-Lite |
| **Need best possible** | Claude 3.5 Sonnet API |
| **High volume, budget** | GPT-4o-mini or Gemini Flash API |

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| Ollama Model Library | Library | https://ollama.com/library |
| HuggingFace Models | Library | https://huggingface.co/models |
| vLLM Docs | Docs | https://docs.vllm.ai/ |
| LiteLLM Docs | Docs | https://docs.litellm.ai/ |
| LocalLLaMA Reddit | Community | https://reddit.com/r/LocalLLaMA |
