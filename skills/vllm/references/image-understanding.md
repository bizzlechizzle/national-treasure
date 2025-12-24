# Image Understanding

Generate descriptions and analyze visual content in images.

---

## What is Image Understanding?

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Image     │────▶│    VLM      │────▶│ Description │
│             │     │             │     │  Analysis   │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Core task**: Convert visual information into natural language.

---

## Use Cases

| Use Case | Description | Output Type |
|----------|-------------|-------------|
| **Image captioning** | Alt text, accessibility | Short text |
| **Scene description** | Detailed scene analysis | Paragraph |
| **Content tagging** | Keywords from images | List |
| **Product description** | E-commerce listings | Structured |
| **Medical image notes** | Describe (not diagnose) | Clinical text |
| **Surveillance summary** | Activity description | Brief text |

---

## Prompting Patterns

### Basic Description

```python
# Minimal prompt
prompt = "Describe this image."

# Better: Specify detail level
prompt = "Describe this image in 2-3 sentences."

# Best: Specify purpose
prompt = """Describe this image for use as alt text.
Focus on the main subject and key visual elements.
Keep under 125 characters."""
```

### Detailed Analysis

```python
prompt = """Analyze this image in detail.

Describe:
1. Main subject(s)
2. Setting/environment
3. Colors and lighting
4. Notable details
5. Overall mood/atmosphere

Be specific and objective."""
```

### Structured Output

```python
prompt = """Analyze this image and return JSON:

{
  "main_subject": "string",
  "scene_type": "indoor|outdoor|abstract|portrait|etc",
  "objects": ["list", "of", "objects"],
  "colors": ["dominant", "colors"],
  "text_visible": "any text in image or null",
  "people_count": number,
  "description": "2-3 sentence summary"
}"""
```

### E-commerce Product

```python
prompt = """Create a product description from this image.

Include:
- Product type
- Key features visible
- Colors/materials
- Condition (new, used, if apparent)
- Any brand/labels visible

Format as:
{
  "title": "short product title",
  "category": "product category",
  "features": ["feature1", "feature2"],
  "colors": ["color1", "color2"],
  "description": "marketing-style description"
}"""
```

---

## Output Formats

### Alt Text (Accessibility)

```python
prompt = """Write alt text for this image.

Requirements:
- Describe the essential information
- Under 125 characters
- Don't start with "Image of" or "Picture of"
- Focus on what matters for context
- Be specific but concise"""

# Good: "Golden retriever catching a red frisbee on a sunny beach"
# Bad: "A picture of a dog outside"
```

### Social Media Caption

```python
prompt = """Write a social media caption for this image.

Style: {casual|professional|humorous}
Include: {emoji_count} emojis
Hashtags: {yes|no}
Tone: {brand_voice}
Max length: 280 characters"""
```

### SEO Description

```python
prompt = """Write an SEO-optimized description for this image.

Requirements:
- Include relevant keywords naturally
- 150-160 characters for meta description
- Descriptive but not keyword-stuffed
- Would make sense in search results"""
```

---

## Multi-Image Analysis

### Comparison

```python
prompt = """Compare these two images.

Describe:
1. Similarities
2. Differences
3. Which image is better for [purpose]
4. Key distinguishing features"""

# Send both images in the message
```

### Sequence/Story

```python
prompt = """These images are in sequence.

Describe:
1. What's happening in each image
2. The overall narrative
3. Changes between images
4. Timeline if apparent"""
```

### Batch Processing

```python
async def describe_images(image_paths: list, prompt: str):
    """Process multiple images with same prompt."""
    results = []
    for path in image_paths:
        image = load_image(path)
        response = await generate(prompt, image)
        results.append({
            "path": path,
            "description": response
        })
    return results
```

---

## Quality Guidelines

### Good Descriptions

| Quality | Example |
|---------|---------|
| **Specific** | "A tabby cat sleeping on a red velvet couch" |
| **Objective** | "Three people standing" not "Friends hanging out" |
| **Relevant** | Focus on what matters for the use case |
| **Accurate** | Only describe what's visible |

### Avoid

| Issue | Why |
|-------|-----|
| Assumptions | Don't infer relationships, emotions beyond obvious |
| Over-description | Match detail level to purpose |
| Hallucination | If unsure, say "appears to be" |
| Bias | Don't make assumptions about people |

---

## Handling Edge Cases

### Low Quality Images

```python
prompt = """Describe this image to the best of your ability.

If the image is:
- Blurry: Describe what's discernible
- Dark: Note limited visibility
- Partially visible: Describe visible portions

Indicate confidence level in your description."""
```

### Abstract/Artistic Images

```python
prompt = """Describe this image.

If the image is abstract or artistic:
- Describe visual elements (shapes, colors, patterns)
- Note the style (abstract, surreal, etc.)
- Describe the overall impression
- Avoid over-interpretation"""
```

### Sensitive Content

```python
prompt = """Describe this image appropriately.

Guidelines:
- Maintain professional, objective tone
- Avoid graphic descriptions
- Note if content may be sensitive
- Focus on factual description"""
```

---

## Model Selection for Image Understanding

### Local (3090)

| Model | Description Quality | Speed | VRAM |
|-------|---------------------|-------|------|
| **Qwen2-VL 7B** | Excellent | Fast | 16GB |
| **LLaVA 7B** | Very Good | Fast | 14GB |
| **Phi-3 Vision** | Good | Very Fast | 8GB |
| **MiniCPM-V 2.6** | Very Good | Fast | 16GB |

### API

| Model | Description Quality | Cost |
|-------|---------------------|------|
| **GPT-4o** | Excellent | ~$0.02/image |
| **Claude 3.5 Sonnet** | Excellent | ~$0.02/image |
| **Gemini 1.5 Pro** | Excellent | ~$0.01/image |
| **GPT-4o-mini** | Good | ~$0.005/image |

### Recommendation

| Use Case | Model |
|----------|-------|
| High volume | Qwen2-VL 7B (local) |
| Best quality | GPT-4o or Claude 3.5 |
| Fast iteration | Phi-3 Vision (local) |
| Budget API | Gemini 1.5 Flash |

---

## Implementation Examples

### Basic Description (OpenAI)

```python
from openai import OpenAI
import base64

client = OpenAI()

def describe_image(image_path: str, detail_level: str = "medium") -> str:
    """Generate description for an image."""

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    prompts = {
        "brief": "Describe this image in one sentence.",
        "medium": "Describe this image in 2-3 sentences.",
        "detailed": "Provide a detailed description of this image."
    }

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompts.get(detail_level, prompts["medium"])},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{image_data}",
                    "detail": "high" if detail_level == "detailed" else "low"
                }}
            ]
        }]
    )

    return response.choices[0].message.content
```

### Structured Analysis (Local)

```python
import ollama
import base64
import json

def analyze_image(image_path: str) -> dict:
    """Get structured analysis of an image."""

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    prompt = """Analyze this image and return JSON only:
{
    "main_subject": "string",
    "scene_type": "string",
    "objects": ["list"],
    "colors": ["list"],
    "description": "2-3 sentences"
}"""

    response = ollama.chat(
        model='llava:7b',
        messages=[{
            'role': 'user',
            'content': prompt,
            'images': [image_data]
        }]
    )

    # Parse JSON from response
    content = response['message']['content']
    # Extract JSON if wrapped in markdown
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]

    return json.loads(content)
```

### Batch Alt Text Generation

```python
import asyncio
from pathlib import Path

async def generate_alt_texts(image_dir: str) -> dict:
    """Generate alt text for all images in a directory."""

    results = {}
    image_files = list(Path(image_dir).glob("*.{jpg,jpeg,png,webp}"))

    for image_path in image_files:
        alt_text = await describe_image_async(
            str(image_path),
            prompt="Write alt text under 125 characters. Don't start with 'Image of'."
        )
        results[image_path.name] = alt_text

    return results
```

---

## Evaluation

### Quality Metrics

| Metric | How to Measure |
|--------|----------------|
| **Accuracy** | Human review of factual correctness |
| **Completeness** | Are key elements mentioned? |
| **Relevance** | Is description useful for the purpose? |
| **Conciseness** | Is length appropriate? |
| **Consistency** | Similar images get similar descriptions |

### A/B Testing

```python
def evaluate_descriptions(image_path: str, prompts: list) -> dict:
    """Compare different prompting approaches."""
    results = {}

    for i, prompt in enumerate(prompts):
        response = generate(prompt, load_image(image_path))
        results[f"prompt_{i}"] = {
            "prompt": prompt,
            "response": response,
            "length": len(response),
            "tokens": count_tokens(response)
        }

    return results
```

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Too verbose | No length constraint | Add "in X sentences" |
| Too generic | Vague prompt | Add specific requirements |
| Hallucination | Model invention | Add "only describe visible" |
| Inconsistent | Variable prompting | Use templates |
| Misses text | OCR not triggered | Ask to "read any text" |

---

## Checklist

- [ ] Purpose defined (alt text, marketing, etc.)
- [ ] Output format specified
- [ ] Length constraints set
- [ ] Edge cases handled
- [ ] Consistency tested across similar images
- [ ] Accuracy validated on sample
- [ ] Bias reviewed
- [ ] Processing pipeline built

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| Alt Text Best Practices | Guide | https://www.w3.org/WAI/tutorials/images/ |
| WebAIM Alt Text | Guide | https://webaim.org/techniques/alttext/ |
| LLaVA Project | GitHub | https://github.com/haotian-liu/LLaVA |
| Qwen2-VL | HuggingFace | https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct |
