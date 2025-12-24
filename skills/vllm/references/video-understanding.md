# Video Understanding

Analyze video content using VLMs.

---

## What is Video Understanding?

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Video     │────▶│  Processing │────▶│    VLM      │────▶│  Analysis   │
│             │     │  (Frames/   │     │             │     │             │
│             │     │   Native)   │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**Two approaches**:
1. **Native video input** — Gemini 1.5 only
2. **Frame sampling** — Works with any VLM

---

## Approach Comparison

| Aspect | Frame Sampling | Native (Gemini) |
|--------|----------------|-----------------|
| **Model support** | Any VLM | Gemini 1.5 only |
| **Motion capture** | Limited | Good |
| **Cost** | Per-frame | Token-based |
| **Max length** | Unlimited | ~1 hour |
| **Audio** | Separate | Included |
| **Setup** | More code | Simple |

### When to Use Each

| Scenario | Approach |
|----------|----------|
| Long videos (>1hr) | Frame sampling |
| Need motion understanding | Gemini native |
| Privacy-critical | Frame sampling (local) |
| Audio important | Gemini native |
| High volume | Frame sampling (local) |
| Quick prototype | Gemini native |

---

## Frame Sampling Strategies

### Uniform Sampling

```python
import cv2
import numpy as np

def sample_uniform(video_path: str, n_frames: int = 10) -> list:
    """Sample n frames uniformly across video."""
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    indices = np.linspace(0, total_frames - 1, n_frames, dtype=int)
    frames = []

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    cap.release()
    return frames
```

### Time-Based Sampling

```python
def sample_by_time(video_path: str, interval_seconds: float = 5.0) -> list:
    """Sample one frame every N seconds."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    interval_frames = int(fps * interval_seconds)

    frames = []
    frame_idx = 0

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        frame_idx += interval_frames

    cap.release()
    return frames
```

### Scene Change Detection

```python
def sample_scene_changes(video_path: str, threshold: float = 30.0) -> list:
    """Sample frames at scene changes."""
    cap = cv2.VideoCapture(video_path)
    frames = []
    prev_frame = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_frame is None:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        else:
            diff = cv2.absdiff(prev_frame, gray).mean()
            if diff > threshold:
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        prev_frame = gray

    cap.release()
    return frames
```

### Keyframe Extraction (Motion)

```python
def sample_keyframes(video_path: str, max_frames: int = 20) -> list:
    """Extract keyframes based on motion."""
    import decord
    from decord import VideoReader

    vr = VideoReader(video_path)

    # Calculate frame differences
    diffs = []
    prev = None
    for i in range(len(vr)):
        frame = vr[i].asnumpy()
        if prev is not None:
            diff = np.abs(frame.astype(float) - prev.astype(float)).mean()
            diffs.append((i, diff))
        prev = frame

    # Sort by motion and take top frames
    diffs.sort(key=lambda x: x[1], reverse=True)
    keyframe_indices = sorted([d[0] for d in diffs[:max_frames]])

    return [vr[i].asnumpy() for i in keyframe_indices]
```

---

## Sampling Guidelines

| Video Type | Recommended Strategy | Frame Count |
|------------|----------------------|-------------|
| Static scene | Uniform, sparse | 3-5 |
| Talking head | Uniform, medium | 5-10 |
| Action/sports | Dense or keyframe | 15-30 |
| Tutorial | Scene change | 10-20 |
| Surveillance | Time-based | 1/10 sec |

### Calculating Frame Count

```python
def calculate_frame_count(duration_seconds: int, video_type: str) -> int:
    """Estimate needed frames based on video type."""
    rates = {
        "static": 0.1,      # 1 frame per 10 seconds
        "normal": 0.2,      # 1 frame per 5 seconds
        "action": 1.0,      # 1 frame per second
        "dense": 2.0        # 2 frames per second
    }
    rate = rates.get(video_type, 0.2)
    return max(3, min(30, int(duration_seconds * rate)))
```

---

## Video Analysis Patterns

### Summarization

```python
prompt = """Analyze these frames from a video and provide:

1. **Summary**: What is happening in this video? (2-3 sentences)
2. **Key moments**: List the main events/scenes
3. **Setting**: Where does this take place?
4. **People/Objects**: Who/what is featured?

The frames are in chronological order."""
```

### Action Recognition

```python
prompt = """These frames are from a video. What actions occur?

List each distinct action:
- Action name
- Approximate timing (beginning/middle/end)
- People involved

Focus on observable actions, not interpretations."""
```

### Content Moderation

```python
prompt = """Review these video frames for content issues.

Check for:
- Violence or dangerous activities
- Inappropriate content
- Policy violations

For each frame, indicate:
- Frame number (1-based)
- Issue type (if any)
- Severity (none/low/medium/high)

Return as JSON."""
```

### Tutorial Understanding

```python
prompt = """These frames are from a tutorial video.

Extract:
1. What is being taught?
2. Step-by-step instructions shown
3. Tools/materials visible
4. Key tips or warnings

Format as a how-to guide."""
```

### Video QA

```python
prompt = """Watch these video frames and answer: {question}

Base your answer only on what's visible in the frames.
If information isn't shown, say "Cannot determine from video"."""
```

---

## Native Video (Gemini)

### Basic Usage

```python
import google.generativeai as genai

genai.configure(api_key="...")
model = genai.GenerativeModel('gemini-1.5-pro')

# Upload video
video_file = genai.upload_file("video.mp4")

# Wait for processing
import time
while video_file.state.name == "PROCESSING":
    time.sleep(10)
    video_file = genai.get_file(video_file.name)

# Analyze
response = model.generate_content([
    "Summarize this video in detail.",
    video_file
])
print(response.text)
```

### Video QA with Timestamps

```python
response = model.generate_content([
    """Answer these questions about the video:

    1. What happens at the beginning?
    2. What is the main topic?
    3. At what timestamp does [event] occur?

    Include timestamps (MM:SS) in your answers.""",
    video_file
])
```

### Long Video Processing

```python
# Gemini 1.5 Pro supports ~1 hour of video
# For longer videos, split into chunks

def process_long_video(video_path: str, chunk_minutes: int = 30):
    """Process video in chunks."""
    import ffmpeg

    # Get duration
    probe = ffmpeg.probe(video_path)
    duration = float(probe['format']['duration'])

    summaries = []
    for start in range(0, int(duration), chunk_minutes * 60):
        # Extract chunk
        chunk_path = f"chunk_{start}.mp4"
        ffmpeg.input(video_path, ss=start, t=chunk_minutes*60).output(chunk_path).run()

        # Process chunk
        video_file = genai.upload_file(chunk_path)
        response = model.generate_content([
            f"Summarize this video segment (starts at {start//60} minutes):",
            video_file
        ])
        summaries.append(response.text)

    # Combine summaries
    final = model.generate_content([
        "Combine these video segment summaries into one coherent summary:",
        "\n\n".join(summaries)
    ])
    return final.text
```

---

## Frame Sampling + VLM

### Multi-Frame Analysis (OpenAI)

```python
from openai import OpenAI
import base64

client = OpenAI()

def analyze_video_frames(frames: list, prompt: str) -> str:
    """Analyze multiple video frames with GPT-4o."""

    content = [{"type": "text", "text": prompt}]

    for i, frame in enumerate(frames):
        # Convert numpy array to base64
        from PIL import Image
        import io

        img = Image.fromarray(frame)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        img_data = base64.b64encode(buffer.getvalue()).decode()

        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}
        })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        max_tokens=1000
    )

    return response.choices[0].message.content
```

### Full Pipeline

```python
def analyze_video(video_path: str, task: str = "summarize") -> str:
    """Complete video analysis pipeline."""

    # 1. Get video info
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    cap.release()

    # 2. Choose sampling strategy
    if duration < 30:
        frames = sample_uniform(video_path, n_frames=5)
    elif duration < 300:
        frames = sample_uniform(video_path, n_frames=10)
    else:
        frames = sample_scene_changes(video_path)[:20]

    # 3. Build prompt
    prompts = {
        "summarize": "Summarize what happens in this video based on these frames.",
        "describe": "Describe each scene shown in these video frames.",
        "action": "What actions are being performed in this video?"
    }
    prompt = prompts.get(task, task)
    prompt += f"\n\nVideo duration: {duration:.0f} seconds. {len(frames)} frames shown."

    # 4. Analyze
    return analyze_video_frames(frames, prompt)
```

---

## Audio Processing

### Extract and Transcribe

```python
import whisper
import ffmpeg

def extract_audio(video_path: str) -> str:
    """Extract audio from video."""
    audio_path = video_path.rsplit('.', 1)[0] + '.wav'
    ffmpeg.input(video_path).output(audio_path, acodec='pcm_s16le', ac=1, ar='16k').run(overwrite=True)
    return audio_path

def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio with Whisper."""
    model = whisper.load_model("base")  # or "small", "medium", "large"
    result = model.transcribe(audio_path)
    return result["text"]

def analyze_video_with_audio(video_path: str, prompt: str) -> str:
    """Analyze video with both visual and audio content."""

    # Get transcript
    audio_path = extract_audio(video_path)
    transcript = transcribe_audio(audio_path)

    # Get frames
    frames = sample_uniform(video_path, n_frames=10)

    # Combined prompt
    full_prompt = f"""{prompt}

Video transcript:
{transcript}

Visual frames are provided below."""

    return analyze_video_frames(frames, full_prompt)
```

---

## Model Selection for Video

### Native Video Support

| Model | Video Support | Max Length | Audio |
|-------|---------------|------------|-------|
| **Gemini 1.5 Pro** | Yes | ~1 hour | Yes |
| **Gemini 1.5 Flash** | Yes | ~1 hour | Yes |
| **GPT-4o** | No (frames only) | N/A | No |
| **Claude 3.5** | No (frames only) | N/A | No |

### Frame-Based Analysis

| Model | Multi-Image | Max Images | Quality |
|-------|-------------|------------|---------|
| **GPT-4o** | Yes | ~20 | Excellent |
| **Claude 3.5** | Yes | ~20 | Excellent |
| **Qwen2-VL** | Yes | ~10 | Very Good |
| **LLaVA** | Yes | ~5 | Good |

### Recommendation

| Use Case | Approach |
|----------|----------|
| Quick video summary | Gemini 1.5 Flash |
| Best quality | Gemini 1.5 Pro |
| Privacy-critical | Frame sampling + local VLM |
| High volume | Frame sampling + local VLM |
| Audio important | Gemini 1.5 or Whisper + VLM |

---

## Performance Optimization

### Efficient Frame Extraction

```python
# Use decord for faster extraction than OpenCV
from decord import VideoReader, cpu

def fast_sample(video_path: str, n_frames: int = 10) -> list:
    """Fast frame extraction with decord."""
    vr = VideoReader(video_path, ctx=cpu(0))
    indices = np.linspace(0, len(vr) - 1, n_frames, dtype=int)
    frames = vr.get_batch(indices).asnumpy()
    return [frames[i] for i in range(len(frames))]
```

### Batch Processing

```python
async def process_videos_batch(video_paths: list, prompt: str, concurrency: int = 5):
    """Process multiple videos in parallel."""
    semaphore = asyncio.Semaphore(concurrency)

    async def process_one(path):
        async with semaphore:
            frames = sample_uniform(path, n_frames=10)
            result = await analyze_video_frames_async(frames, prompt)
            return {"path": path, "result": result}

    results = await asyncio.gather(*[process_one(p) for p in video_paths])
    return results
```

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Misses key moments | Sparse sampling | Use scene detection |
| Temporal confusion | Frame order unclear | Add frame numbers |
| Action missed | Static sampling | Sample during motion |
| High cost | Too many frames | Reduce frame count |
| Slow processing | Large frames | Resize to 720p |

---

## Checklist

- [ ] Video type identified
- [ ] Sampling strategy chosen
- [ ] Frame count determined
- [ ] Audio handling decided
- [ ] Prompt designed for task
- [ ] Temporal context included
- [ ] Cost estimated
- [ ] Edge cases tested (long videos, low quality)

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| Gemini Video | Docs | https://ai.google.dev/gemini-api/docs/vision |
| Decord | GitHub | https://github.com/dmlc/decord |
| Whisper | GitHub | https://github.com/openai/whisper |
| Video-LLaVA | Paper | https://arxiv.org/abs/2311.10122 |
