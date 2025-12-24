# Prompting Guide

Get better outputs through better prompts.

---

## Core Principles

1. **Be specific** — Vague prompts get vague outputs
2. **Show, don't tell** — Examples beat instructions
3. **Structure helps** — Clear formatting improves output
4. **Iterate** — First prompt rarely optimal

---

## Prompt Structure

### Basic Template

```
[System message: Role, constraints, style]

[Context: Background information the model needs]

[Examples: Few-shot demonstrations]

[Task: What to do - be specific]

[Format: How to structure the response]
```

### Example

```
You are a technical writer who creates clear, concise documentation.
Write in active voice. Use simple words. Target a developer audience.

---

Context: Our API uses REST with JSON. Authentication is via Bearer tokens.

---

Examples:

Input: "GET /users - returns all users"
Output:
## Get All Users
Retrieves a list of all users in the system.

**Endpoint:** `GET /users`

**Authentication:** Required

**Response:**
- `200 OK` - Array of user objects

---

Now document this endpoint:
POST /users - creates a new user with name and email fields

Respond in markdown format matching the example above.
```

---

## Techniques

### Zero-Shot

No examples. Direct instruction.

```
Summarize this article in 3 bullet points:

[article text]
```

**When to use**: Simple tasks, clear instructions.

### Few-Shot

Include examples before the task.

```
Classify the sentiment of these reviews:

Review: "This product is amazing!"
Sentiment: Positive

Review: "Worst purchase ever."
Sentiment: Negative

Review: "It works, nothing special."
Sentiment: Neutral

Review: "I can't believe how well this works!"
Sentiment:
```

**When to use**: Need specific format, style, or behavior.

### Chain-of-Thought (CoT)

Ask model to reason step by step.

```
Solve this problem step by step:

A store has 50 apples. They sell 30% in the morning and
half of the remaining in the afternoon. How many are left?

Let's think through this step by step:
```

**When to use**: Math, logic, multi-step reasoning.

### Self-Consistency

Generate multiple answers, take majority.

```python
answers = []
for _ in range(5):
    response = llm.generate(prompt, temperature=0.7)
    answers.append(extract_answer(response))

final_answer = most_common(answers)
```

**When to use**: Improve reliability on reasoning tasks.

### Reflection / Critique

Ask model to check its work.

```
[Initial response]

Now review your answer:
1. Are there any errors?
2. Is anything missing?
3. Could it be clearer?

Provide an improved version.
```

**When to use**: Quality-critical outputs.

---

## System Prompts

### Purpose

- Set persona/role
- Define constraints
- Establish style
- Prevent unwanted behavior

### Template

```
You are [ROLE].

Your goal is to [PRIMARY OBJECTIVE].

Guidelines:
- [BEHAVIOR 1]
- [BEHAVIOR 2]
- [BEHAVIOR 3]

You must NOT:
- [CONSTRAINT 1]
- [CONSTRAINT 2]

Output format: [FORMAT DESCRIPTION]
```

### Examples

**Technical Assistant**
```
You are a senior software engineer helping junior developers.

Your goal is to teach, not just give answers.

Guidelines:
- Explain your reasoning
- Suggest best practices
- Point out potential issues
- Keep explanations concise

You must NOT:
- Write insecure code
- Recommend deprecated patterns
- Assume knowledge level without asking

Output format: Explanation first, then code block if applicable.
```

**Customer Support**
```
You are a helpful customer support agent for [Company].

Your goal is to resolve customer issues efficiently and kindly.

Guidelines:
- Be empathetic and patient
- Provide accurate information only
- Escalate if you can't help
- Keep responses concise

You must NOT:
- Make promises about refunds without approval
- Share internal information
- Argue with customers
- Make up policies

If unsure, say: "Let me connect you with a specialist who can help."
```

---

## Structured Output

### JSON Mode

```
Extract information as JSON:

Text: "John Smith, age 32, works at Acme Corp as a software engineer."

Respond with ONLY valid JSON:
{
  "name": string,
  "age": number,
  "company": string,
  "title": string
}
```

### Schema Specification

```
Extract entities from this text. Use this exact schema:

{
  "people": [
    {
      "name": "string (full name)",
      "role": "string (job title or relationship)",
      "mentioned_in": "string (quote from text)"
    }
  ],
  "organizations": [
    {
      "name": "string",
      "type": "company|nonprofit|government|other"
    }
  ],
  "dates": [
    {
      "date": "YYYY-MM-DD or null if unclear",
      "event": "string (what happened)"
    }
  ]
}

Text:
"""
[document text]
"""

JSON:
```

### With OpenAI Structured Output

```python
from openai import OpenAI
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    occupation: str

client = OpenAI()
response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Extract: John is 25 and works as a nurse."}],
    response_format=Person
)

person = response.choices[0].message.parsed
```

---

## Common Patterns

### Q&A from Context

```
Answer the question based ONLY on the context below.
If the answer is not in the context, say "I cannot find this information."

Context:
"""
[context text]
"""

Question: [question]

Answer:
```

### Translation

```
Translate the following text to [TARGET LANGUAGE].
Maintain the original tone and style.
Preserve formatting and technical terms.

Text:
"""
[source text]
"""

Translation:
```

### Code Generation

```
Write a [LANGUAGE] function that [DESCRIPTION].

Requirements:
- [Requirement 1]
- [Requirement 2]
- Include error handling
- Add docstring/comments

Example usage:
[example if helpful]

Function:
```

### Summarization

```
Summarize the following text.

Length: [X sentences / X words / X bullet points]
Style: [formal/casual/technical]
Focus on: [key aspects to emphasize]

Text:
"""
[text to summarize]
"""

Summary:
```

### Classification

```
Classify the following text into exactly one category.

Categories:
- Technical Issue: Problems with software/hardware
- Billing: Payment, invoices, subscriptions
- Feature Request: Suggestions for improvements
- General Inquiry: Other questions

Text: "[text to classify]"

Category:
```

---

## Anti-Patterns

### Too Vague

```
❌ "Write something about AI."
✓ "Write a 500-word blog post explaining how RAG works,
   targeting software developers who are new to LLMs."
```

### No Format Specification

```
❌ "List the key points."
✓ "List the key points as a numbered list with brief explanations."
```

### Conflicting Instructions

```
❌ "Be concise. Provide detailed explanations with examples."
✓ "Be concise. Limit to 3 sentences per point."
```

### Assuming Knowledge

```
❌ "Use the standard format."
✓ "Use this format: [specific format example]"
```

### No Escape Hatch

```
❌ "Answer the question from the context."
   (What if answer isn't there? Model will hallucinate.)

✓ "Answer from the context. If not found, say 'Not in context.'"
```

---

## Temperature and Parameters

### Temperature

| Value | Behavior | Use For |
|-------|----------|---------|
| 0.0 | Deterministic, focused | Facts, code, classification |
| 0.3-0.5 | Balanced | General use |
| 0.7-1.0 | Creative, varied | Writing, brainstorming |
| >1.0 | Chaotic | Rarely useful |

### Other Parameters

| Parameter | Effect |
|-----------|--------|
| `top_p` | Nucleus sampling (alternative to temp) |
| `max_tokens` | Limit response length |
| `stop` | Stop sequences |
| `presence_penalty` | Discourage repetition of topics |
| `frequency_penalty` | Discourage repetition of words |

### Recommendations

```python
# Factual/code
response = llm.generate(
    prompt,
    temperature=0,
    max_tokens=2000
)

# Creative writing
response = llm.generate(
    prompt,
    temperature=0.8,
    max_tokens=4000,
    presence_penalty=0.1
)

# Classification
response = llm.generate(
    prompt,
    temperature=0,
    max_tokens=50
)
```

---

## Prompt Chaining

### Sequential Processing

```python
# Step 1: Extract key points
extract_prompt = f"Extract key points from:\n{document}"
key_points = llm.generate(extract_prompt)

# Step 2: Generate summary from key points
summary_prompt = f"Write a summary based on:\n{key_points}"
summary = llm.generate(summary_prompt)

# Step 3: Create title from summary
title_prompt = f"Create a title for:\n{summary}"
title = llm.generate(title_prompt)
```

### Parallel Processing

```python
import asyncio

async def process_sections(document):
    sections = split_document(document)

    # Process all sections in parallel
    tasks = [
        llm.agenerate(f"Summarize:\n{section}")
        for section in sections
    ]
    summaries = await asyncio.gather(*tasks)

    # Combine
    combined = "\n\n".join(summaries)
    return llm.generate(f"Create final summary:\n{combined}")
```

### Validation Loop

```python
def generate_with_validation(prompt, max_attempts=3):
    for attempt in range(max_attempts):
        response = llm.generate(prompt)

        # Validate output
        if validate(response):
            return response

        # Add feedback for retry
        prompt = f"""
Previous attempt had issues: {get_issues(response)}

{prompt}

Please fix these issues in your response.
"""

    raise Exception("Failed to generate valid response")
```

---

## Debugging Prompts

### Symptoms and Fixes

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Too short | No length guidance | Specify length |
| Wrong format | No format example | Add examples |
| Hallucinations | No grounding | Add context, "if unknown say so" |
| Off-topic | Vague task | Be more specific |
| Repetitive | High temperature | Lower temperature |
| Too verbose | No constraints | Add "be concise" |

### Prompt Debugging Process

1. **Test with simple case** — Does it work at all?
2. **Add examples** — Show what you want
3. **Constrain** — Add boundaries
4. **Adjust temperature** — 0 for deterministic tests
5. **Check context** — Is relevant info included?
6. **Simplify** — Remove unnecessary complexity

---

## Checklist

Before finalizing a prompt:

- [ ] Task is clearly stated
- [ ] Format is specified (or shown by example)
- [ ] Context is provided if needed
- [ ] Edge cases are handled ("if not found...")
- [ ] Length/scope is constrained
- [ ] Temperature matches task type
- [ ] Tested on multiple inputs
- [ ] Examples added for complex tasks

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| Anthropic Prompt Engineering | Guide | https://docs.anthropic.com/claude/docs/prompt-engineering |
| OpenAI Prompt Engineering | Guide | https://platform.openai.com/docs/guides/prompt-engineering |
| Learn Prompting | Course | https://learnprompting.org/ |
| Prompt Engineering Guide | Repo | https://github.com/dair-ai/Prompt-Engineering-Guide |
