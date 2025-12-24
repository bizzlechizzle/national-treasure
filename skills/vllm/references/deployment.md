# VLM Deployment

Serve vision-language models locally or via API in production.

---

## Deployment Options

| Option | Best For | Latency | Cost |
|--------|----------|---------|------|
| **API (OpenAI, etc.)** | Quick start, best quality | Medium | Per-image |
| **Local (Ollama)** | Simple self-host | Low | Fixed |
| **Local (vLLM)** | High throughput | Low | Fixed |
| **Local (transformers)** | Full control | Medium | Fixed |

---

## Local Deployment (3090)

### Ollama (Simplest)

```bash
# Install
curl -fsSL https://ollama.com/install.sh | sh

# Pull vision model
ollama pull llava:7b
ollama pull llava:13b

# Run with image
ollama run llava:7b "Describe this image" ./photo.jpg

# Serve API
ollama serve  # Default: http://localhost:11434
```

**API usage:**

```python
import ollama
import base64

def analyze_image(image_path: str, prompt: str) -> str:
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    response = ollama.chat(
        model='llava:7b',
        messages=[{
            'role': 'user',
            'content': prompt,
            'images': [image_data]
        }]
    )
    return response['message']['content']
```

### vLLM (High Throughput)

```bash
# Install
pip install vllm

# Serve Qwen2-VL (OpenAI-compatible API)
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2-VL-7B-Instruct \
    --dtype float16 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9 \
    --trust-remote-code
```

**Use with OpenAI client:**

```python
from openai import OpenAI
import base64

client = OpenAI(
    api_key="not-needed",
    base_url="http://localhost:8000/v1"
)

with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="Qwen/Qwen2-VL-7B-Instruct",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this image"},
            {"type": "image_url", "image_url": {
                "url": f"data:image/jpeg;base64,{image_data}"
            }}
        ]
    }]
)
```

### Transformers (Full Control)

```python
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from PIL import Image
import torch

class VLMServer:
    def __init__(self, model_name: str = "Qwen/Qwen2-VL-7B-Instruct"):
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        self.processor = AutoProcessor.from_pretrained(model_name)

    def generate(self, image_path: str, prompt: str, max_tokens: int = 256) -> str:
        image = Image.open(image_path)

        messages = [
            {"role": "user", "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt}
            ]}
        ]

        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.processor(
            text=[text], images=[image], return_tensors="pt"
        ).to("cuda")

        output = self.model.generate(**inputs, max_new_tokens=max_tokens)
        return self.processor.decode(output[0], skip_special_tokens=True)

# Usage
server = VLMServer()
result = server.generate("photo.jpg", "Describe this image")
```

### llama.cpp (GGUF Models)

```bash
# Build with CUDA
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make LLAMA_CUDA=1

# Run with image
./llava-cli \
    -m models/llava-v1.6-7b.Q5_K_M.gguf \
    --mmproj models/llava-v1.6-7b-mmproj.gguf \
    --image photo.jpg \
    -p "Describe this image"

# Serve as API
./server \
    -m models/llava-v1.6-7b.Q5_K_M.gguf \
    --mmproj models/llava-v1.6-7b-mmproj.gguf \
    --host 0.0.0.0 \
    --port 8080
```

---

## Production API Service

### FastAPI Implementation

```python
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from PIL import Image
import io
import base64

app = FastAPI()

# Initialize VLM (choose one)
# Option 1: Ollama
import ollama

# Option 2: Local model
# vlm = VLMServer("Qwen/Qwen2-VL-7B-Instruct")

class AnalyzeRequest(BaseModel):
    prompt: str
    image_base64: str

class AnalyzeResponse(BaseModel):
    result: str

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(request: AnalyzeRequest):
    try:
        response = ollama.chat(
            model='llava:7b',
            messages=[{
                'role': 'user',
                'content': request.prompt,
                'images': [request.image_base64]
            }]
        )
        return AnalyzeResponse(result=response['message']['content'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/upload", response_model=AnalyzeResponse)
async def analyze_uploaded_image(
    prompt: str,
    file: UploadFile = File(...)
):
    try:
        contents = await file.read()
        image_data = base64.b64encode(contents).decode()

        response = ollama.chat(
            model='llava:7b',
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [image_data]
            }]
        )
        return AnalyzeResponse(result=response['message']['content'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
```

### With Image Preprocessing

```python
from PIL import Image
import io

def preprocess_image(image_bytes: bytes, max_size: int = 1024) -> bytes:
    """Resize and optimize image for VLM."""
    img = Image.open(io.BytesIO(image_bytes))

    # Convert to RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Resize if too large
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = tuple(int(d * ratio) for d in img.size)
        img = img.resize(new_size, Image.LANCZOS)

    # Compress
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return buffer.getvalue()

@app.post("/analyze/optimized")
async def analyze_optimized(request: AnalyzeRequest):
    # Decode, preprocess, re-encode
    raw_bytes = base64.b64decode(request.image_base64)
    processed = preprocess_image(raw_bytes)
    processed_b64 = base64.b64encode(processed).decode()

    response = ollama.chat(
        model='llava:7b',
        messages=[{
            'role': 'user',
            'content': request.prompt,
            'images': [processed_b64]
        }]
    )
    return AnalyzeResponse(result=response['message']['content'])
```

---

## Batch Processing

### Async Batch Processor

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class VLMBatchProcessor:
    def __init__(self, model: str = 'llava:7b', max_workers: int = 2):
        self.model = model
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def _process_single(self, image_data: str, prompt: str) -> str:
        response = ollama.chat(
            model=self.model,
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [image_data]
            }]
        )
        return response['message']['content']

    async def process_batch(
        self,
        items: list[tuple[str, str]]  # (image_data, prompt)
    ) -> list[str]:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(
                self.executor,
                self._process_single,
                image_data,
                prompt
            )
            for image_data, prompt in items
        ]
        return await asyncio.gather(*tasks)

# Usage
processor = VLMBatchProcessor()
results = await processor.process_batch([
    (image1_b64, "Describe this"),
    (image2_b64, "Describe this"),
    (image3_b64, "Describe this"),
])
```

### Queue-Based Processing

```python
import redis
import json
from rq import Queue

redis_conn = redis.Redis()
queue = Queue(connection=redis_conn)

def process_image_job(image_data: str, prompt: str) -> dict:
    """Worker function for background processing."""
    response = ollama.chat(
        model='llava:7b',
        messages=[{
            'role': 'user',
            'content': prompt,
            'images': [image_data]
        }]
    )
    return {"result": response['message']['content']}

@app.post("/analyze/async")
async def analyze_async(request: AnalyzeRequest):
    job = queue.enqueue(
        process_image_job,
        request.image_base64,
        request.prompt
    )
    return {"job_id": job.id}

@app.get("/job/{job_id}")
async def get_job_result(job_id: str):
    job = queue.fetch_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.is_finished:
        return {"status": "complete", "result": job.result}
    elif job.is_failed:
        return {"status": "failed", "error": str(job.exc_info)}
    else:
        return {"status": "pending"}
```

---

## Docker Deployment

### Ollama Container

```yaml
# docker-compose.yml
version: '3.8'
services:
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama

volumes:
  ollama_data:
```

### Application Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Model Initialization Script

```bash
#!/bin/bash
# init-models.sh

# Wait for Ollama to be ready
until curl -s http://localhost:11434/api/tags > /dev/null; do
    echo "Waiting for Ollama..."
    sleep 5
done

# Pull models
ollama pull llava:7b
ollama pull llava:13b

echo "Models ready"
```

---

## API Providers

### LiteLLM Unified Interface

```python
# config.yaml
model_list:
  - model_name: vision-gpt4
    litellm_params:
      model: gpt-4o
      api_key: os.environ/OPENAI_API_KEY

  - model_name: vision-claude
    litellm_params:
      model: claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY

  - model_name: vision-local
    litellm_params:
      model: ollama/llava:7b
      api_base: http://localhost:11434
```

```python
import litellm

def analyze_with_fallback(image_b64: str, prompt: str) -> str:
    """Try local first, fall back to API."""
    try:
        return litellm.completion(
            model="ollama/llava:7b",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_b64}"}
                ]
            }]
        ).choices[0].message.content
    except Exception as e:
        print(f"Local failed: {e}, trying API")
        return litellm.completion(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }]
        ).choices[0].message.content
```

---

## Monitoring

### Logging

```python
import logging
import time

logger = logging.getLogger(__name__)

@app.post("/analyze")
async def analyze_image(request: AnalyzeRequest):
    request_id = generate_id()
    start = time.time()

    logger.info(f"[{request_id}] Processing image, prompt: {request.prompt[:50]}...")

    try:
        result = await process_image(request)
        duration = time.time() - start
        logger.info(f"[{request_id}] Complete in {duration:.2f}s, {len(result)} chars")
        return result
    except Exception as e:
        logger.error(f"[{request_id}] Failed: {e}")
        raise
```

### Metrics (Prometheus)

```python
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('vlm_requests_total', 'Total VLM requests')
REQUEST_LATENCY = Histogram('vlm_request_latency_seconds', 'Request latency')
IMAGE_SIZE = Histogram('vlm_image_size_bytes', 'Image sizes')

@app.post("/analyze")
async def analyze_image(request: AnalyzeRequest):
    REQUEST_COUNT.inc()
    IMAGE_SIZE.observe(len(request.image_base64))

    with REQUEST_LATENCY.time():
        result = await process_image(request)

    return result

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## Performance Tuning (3090)

### Memory Optimization

```bash
# vLLM settings for 3090
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2-VL-7B-Instruct \
    --dtype float16 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.85 \
    --max-num-seqs 4
```

### Quantized Models

```python
# Load 4-bit quantized model
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)

model = Qwen2VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2-VL-7B-Instruct",
    quantization_config=quantization_config,
    device_map="auto"
)
```

### Image Size Limits

```python
MAX_IMAGE_SIZE = 1024  # pixels
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5MB

def validate_image(image_bytes: bytes) -> bytes:
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError(f"Image too large: {len(image_bytes)} bytes")

    img = Image.open(io.BytesIO(image_bytes))
    if max(img.size) > MAX_IMAGE_SIZE:
        ratio = MAX_IMAGE_SIZE / max(img.size)
        new_size = tuple(int(d * ratio) for d in img.size)
        img = img.resize(new_size, Image.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()

    return image_bytes
```

---

## Error Handling

```python
import tenacity

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(min=1, max=10),
    retry=tenacity.retry_if_exception_type(Exception)
)
async def analyze_with_retry(image_data: str, prompt: str) -> str:
    response = ollama.chat(
        model='llava:7b',
        messages=[{
            'role': 'user',
            'content': prompt,
            'images': [image_data]
        }]
    )
    return response['message']['content']

@app.post("/analyze")
async def analyze_image(request: AnalyzeRequest):
    try:
        result = await analyze_with_retry(request.image_base64, request.prompt)
        return AnalyzeResponse(result=result)
    except tenacity.RetryError:
        raise HTTPException(status_code=503, detail="VLM service unavailable")
```

---

## Checklist

- [ ] Model selected and downloaded/accessible
- [ ] Inference engine chosen (Ollama/vLLM/transformers)
- [ ] API endpoints implemented
- [ ] Image preprocessing configured
- [ ] Error handling with retries
- [ ] Rate limiting (if public)
- [ ] Logging implemented
- [ ] Metrics exposed
- [ ] Health check endpoint
- [ ] Docker deployment configured
- [ ] GPU memory optimized
- [ ] Load tested

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| Ollama Vision | Docs | https://ollama.com/blog/vision-models |
| vLLM Docs | Docs | https://docs.vllm.ai/ |
| LiteLLM | Docs | https://docs.litellm.ai/ |
| FastAPI | Docs | https://fastapi.tiangolo.com/ |
