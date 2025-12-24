# LLM Deployment

Serve LLMs locally or via API in production.

---

## Deployment Options

| Option | Best For | Latency | Cost |
|--------|----------|---------|------|
| **API (OpenAI, etc.)** | Quick start, best models | Medium | Per-token |
| **Local (Ollama)** | Simple self-host | Low | Fixed |
| **Local (vLLM)** | High throughput | Low | Fixed |
| **Hybrid** | Best of both | Varies | Mixed |

---

## Local Deployment (3090)

### Ollama (Simplest)

```bash
# Install
curl -fsSL https://ollama.com/install.sh | sh

# Run model
ollama run llama3.1:8b

# Serve API
ollama serve  # Default: http://localhost:11434

# API usage
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.1:8b",
  "messages": [{"role": "user", "content": "Hello"}]
}'
```

**Python client:**

```python
import ollama

response = ollama.chat(
    model='llama3.1:8b',
    messages=[{'role': 'user', 'content': 'Hello!'}]
)
print(response['message']['content'])
```

### vLLM (High Throughput)

```bash
# Install
pip install vllm

# Serve (OpenAI-compatible API)
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --dtype float16 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.9
```

**Use with OpenAI client:**

```python
from openai import OpenAI

client = OpenAI(
    api_key="not-needed",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### llama.cpp Server

```bash
# Build with CUDA
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make LLAMA_CUDA=1

# Serve
./server \
    -m models/llama-3.1-8b.Q5_K_M.gguf \
    -c 4096 \
    -ngl 99 \
    --host 0.0.0.0 \
    --port 8080
```

---

## LiteLLM Proxy (Unified Interface)

Route to any model with one API.

```python
# Install
pip install litellm[proxy]

# Config: config.yaml
"""
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: gpt-4o
      api_key: os.environ/OPENAI_API_KEY

  - model_name: claude
    litellm_params:
      model: claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY

  - model_name: local
    litellm_params:
      model: ollama/llama3.1:8b
      api_base: http://localhost:11434
"""

# Run proxy
litellm --config config.yaml --port 4000

# Use (switch models without code changes)
curl http://localhost:4000/v1/chat/completions \
  -d '{"model": "local", "messages": [{"role": "user", "content": "Hello"}]}'
```

---

## Production API Patterns

### Basic Service

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os

app = FastAPI()
client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
    api_key=os.getenv("LLM_API_KEY", "not-needed")
)

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 1000

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "llama3.1:8b"),
            messages=[{"role": "user", "content": request.message}],
            max_tokens=request.max_tokens
        )
        return ChatResponse(response=response.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
```

### With Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: ChatRequest):
    ...
```

### With Caching

```python
import hashlib
from functools import lru_cache
import redis

redis_client = redis.Redis()

def cache_key(message: str) -> str:
    return hashlib.sha256(message.encode()).hexdigest()

@app.post("/chat")
async def chat(request: ChatRequest):
    key = cache_key(request.message)

    # Check cache
    cached = redis_client.get(key)
    if cached:
        return ChatResponse(response=cached.decode())

    # Generate
    response = generate(request.message)

    # Cache (1 hour TTL)
    redis_client.setex(key, 3600, response)

    return ChatResponse(response=response)
```

---

## Streaming

### Server

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        response = client.chat.completions.create(
            model="llama3.1:8b",
            messages=[{"role": "user", "content": request.message}],
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield f"data: {chunk.choices[0].delta.content}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Client

```python
import httpx

async with httpx.AsyncClient() as client:
    async with client.stream(
        "POST",
        "http://localhost:8000/chat/stream",
        json={"message": "Hello"}
    ) as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                content = line[6:]
                if content != "[DONE]":
                    print(content, end="", flush=True)
```

---

## Docker Deployment

### Ollama

```dockerfile
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

volumes:
  ollama_data:
```

### vLLM

```dockerfile
# Dockerfile
FROM vllm/vllm-openai:latest

ENV MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct

CMD ["python", "-m", "vllm.entrypoints.openai.api_server", \
     "--model", "${MODEL_NAME}", \
     "--dtype", "float16", \
     "--max-model-len", "8192"]
```

### Application + Model

```dockerfile
# docker-compose.yml
version: '3.8'
services:
  llm:
    image: ollama/ollama
    ports:
      - "11434:11434"
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
      - LLM_BASE_URL=http://llm:11434/v1
    depends_on:
      - llm
```

---

## Monitoring

### Logging

```python
import logging
import time

logger = logging.getLogger(__name__)

@app.post("/chat")
async def chat(request: ChatRequest):
    start = time.time()
    request_id = generate_id()

    logger.info(f"[{request_id}] Request: {request.message[:100]}...")

    response = generate(request.message)

    duration = time.time() - start
    logger.info(f"[{request_id}] Response in {duration:.2f}s, {len(response)} chars")

    return ChatResponse(response=response)
```

### Metrics (Prometheus)

```python
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

REQUEST_COUNT = Counter('llm_requests_total', 'Total LLM requests')
REQUEST_LATENCY = Histogram('llm_request_latency_seconds', 'Request latency')
TOKEN_COUNT = Counter('llm_tokens_total', 'Total tokens generated', ['type'])

@app.post("/chat")
async def chat(request: ChatRequest):
    REQUEST_COUNT.inc()
    with REQUEST_LATENCY.time():
        response = generate(request.message)
    TOKEN_COUNT.labels(type='output').inc(len(response.split()))
    return ChatResponse(response=response)

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
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
async def generate_with_retry(message: str) -> str:
    response = client.chat.completions.create(
        model="llama3.1:8b",
        messages=[{"role": "user", "content": message}]
    )
    return response.choices[0].message.content

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        response = await generate_with_retry(request.message)
        return ChatResponse(response=response)
    except tenacity.RetryError:
        raise HTTPException(status_code=503, detail="LLM unavailable")
```

---

## Hybrid Deployment

Use local for privacy/cost, API for quality fallback.

```python
async def generate_hybrid(message: str, prefer_local: bool = True):
    if prefer_local:
        try:
            return await generate_local(message)
        except Exception as e:
            logger.warning(f"Local failed: {e}, falling back to API")

    return await generate_api(message)

# Route based on content
async def smart_route(message: str):
    # Complex/critical → API
    if is_complex(message) or is_critical():
        return await generate_api(message)

    # Simple/high-volume → Local
    return await generate_local(message)
```

---

## Performance Tuning

### 3090 Optimization

```bash
# vLLM settings for 3090
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --dtype float16 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.9 \
    --max-num-seqs 8  # Concurrent requests
```

### Benchmarking

```python
import time
import asyncio

async def benchmark(n_requests=100, concurrency=10):
    semaphore = asyncio.Semaphore(concurrency)

    async def single_request():
        async with semaphore:
            start = time.time()
            await generate("Test prompt")
            return time.time() - start

    times = await asyncio.gather(*[single_request() for _ in range(n_requests)])

    print(f"Total: {sum(times):.2f}s")
    print(f"Avg: {sum(times)/len(times):.2f}s")
    print(f"Throughput: {n_requests/sum(times):.2f} req/s")
```

---

## Checklist

- [ ] Model selected and downloaded
- [ ] Inference engine chosen (Ollama/vLLM)
- [ ] API wrapper implemented
- [ ] Error handling with retries
- [ ] Rate limiting configured
- [ ] Caching for repeated queries
- [ ] Logging implemented
- [ ] Metrics exposed
- [ ] Health check endpoint
- [ ] Docker/deployment configured
- [ ] Load tested

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| Ollama Docs | Docs | https://ollama.com/docs |
| vLLM Docs | Docs | https://docs.vllm.ai/ |
| LiteLLM | Docs | https://docs.litellm.ai/ |
| FastAPI | Docs | https://fastapi.tiangolo.com/ |
