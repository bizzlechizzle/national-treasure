# Agents

LLMs that use tools and take actions.

---

## What is an Agent?

```
┌─────────────────────────────────────────────────────────────┐
│                      AGENT LOOP                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Goal ──► Think ──► Act ──► Observe ──► Think ──► ...     │
│               │         │         │                         │
│               ▼         ▼         ▼                         │
│            Reason    Use Tool   Get Result                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Agent = LLM + Tools + Loop**

---

## When to Use Agents

**Good for:**
- Multi-step tasks
- Tasks requiring external data
- Dynamic decision-making
- Combining multiple capabilities

**Not good for:**
- Simple one-shot tasks (overkill)
- Deterministic workflows (use code)
- High-stakes without human oversight
- Real-time requirements (too slow)

---

## Agent Types

### ReAct (Reasoning + Acting)

```
Thought: I need to find the weather in Tokyo
Action: weather_api(location="Tokyo")
Observation: 72°F, sunny
Thought: Now I can answer
Answer: It's 72°F and sunny in Tokyo.
```

### Function Calling (OpenAI/Anthropic)

```python
# Model decides to call function
response = {
    "tool_calls": [{
        "function": {
            "name": "get_weather",
            "arguments": '{"location": "Tokyo"}'
        }
    }]
}
```

### Plan-and-Execute

```
1. Make plan: [step1, step2, step3]
2. Execute each step
3. Revise plan if needed
4. Continue until done
```

---

## Tool Definition

### OpenAI Format

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "default": "celsius"
                }
            },
            "required": ["location"]
        }
    }
}]
```

### Anthropic Format

```python
tools = [{
    "name": "get_weather",
    "description": "Get current weather for a location",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"}
        },
        "required": ["location"]
    }
}]
```

---

## Basic Agent Loop

```python
from openai import OpenAI

client = OpenAI()

def run_agent(user_message, tools, max_iterations=10):
    messages = [{"role": "user", "content": user_message}]

    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools
        )

        message = response.choices[0].message

        # If no tool calls, we're done
        if not message.tool_calls:
            return message.content

        # Execute tool calls
        messages.append(message)
        for tool_call in message.tool_calls:
            result = execute_tool(
                tool_call.function.name,
                json.loads(tool_call.function.arguments)
            )
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })

    return "Max iterations reached"

def execute_tool(name, args):
    if name == "get_weather":
        return get_weather(**args)
    elif name == "search":
        return search(**args)
    # ... more tools
```

---

## Common Tools

### Web Search

```python
def web_search(query: str) -> str:
    """Search the web for information."""
    # Use SerpAPI, Tavily, or similar
    from tavily import TavilyClient
    client = TavilyClient(api_key="...")
    result = client.search(query)
    return result['results']
```

### Code Execution

```python
def run_python(code: str) -> str:
    """Execute Python code and return output."""
    import subprocess
    result = subprocess.run(
        ['python', '-c', code],
        capture_output=True,
        text=True,
        timeout=30
    )
    return result.stdout or result.stderr
```

### File Operations

```python
def read_file(path: str) -> str:
    """Read a file's contents."""
    with open(path, 'r') as f:
        return f.read()

def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    with open(path, 'w') as f:
        f.write(content)
    return f"Written to {path}"
```

### API Calls

```python
def call_api(url: str, method: str = "GET", body: dict = None) -> str:
    """Make an HTTP request."""
    import requests
    response = requests.request(method, url, json=body)
    return response.json()
```

### Database

```python
def query_database(sql: str) -> str:
    """Execute a SQL query (SELECT only)."""
    if not sql.strip().upper().startswith("SELECT"):
        return "Error: Only SELECT queries allowed"
    # Execute safely
    result = db.execute(sql)
    return str(result.fetchall())
```

---

## Safety Considerations

### Tool Sandboxing

```python
# Restrict code execution
def safe_run_python(code: str) -> str:
    """Execute Python in restricted environment."""
    # Use RestrictedPython or Docker
    import docker
    client = docker.from_env()
    result = client.containers.run(
        "python:3.11-slim",
        f"python -c '{code}'",
        remove=True,
        mem_limit="256m",
        network_disabled=True
    )
    return result.decode()
```

### Human-in-the-Loop

```python
def execute_with_approval(tool_name, args):
    """Require human approval for dangerous actions."""
    dangerous = ["delete", "write", "execute", "send"]

    if any(d in tool_name.lower() for d in dangerous):
        print(f"Agent wants to: {tool_name}({args})")
        if input("Approve? (y/n): ").lower() != 'y':
            return "Action denied by user"

    return execute_tool(tool_name, args)
```

### Rate Limiting

```python
from functools import wraps
import time

def rate_limit(max_calls: int, period: int):
    """Limit tool calls."""
    calls = []

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [c for c in calls if now - c < period]
            if len(calls) >= max_calls:
                raise Exception(f"Rate limit: {max_calls} calls per {period}s")
            calls.append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(10, 60)  # 10 calls per minute
def web_search(query):
    ...
```

---

## Frameworks

### LangChain Agents

```python
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.tools import Tool

tools = [
    Tool(
        name="search",
        func=search_function,
        description="Search the web"
    ),
    Tool(
        name="calculator",
        func=calculate,
        description="Do math calculations"
    )
]

llm = ChatOpenAI(model="gpt-4o")
agent = create_openai_functions_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

result = executor.invoke({"input": "What's 15% of Tesla's stock price?"})
```

### LlamaIndex Agents

```python
from llama_index.agent import OpenAIAgent
from llama_index.tools import FunctionTool

def search(query: str) -> str:
    """Search for information."""
    return do_search(query)

tools = [FunctionTool.from_defaults(fn=search)]
agent = OpenAIAgent.from_tools(tools, verbose=True)

response = agent.chat("Find the population of France")
```

### Anthropic Tool Use

```python
from anthropic import Anthropic

client = Anthropic()

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather in Paris?"}]
)

# Handle tool use
for block in response.content:
    if block.type == "tool_use":
        result = execute_tool(block.name, block.input)
        # Continue conversation with result
```

---

## Local Agents (3090)

### With Ollama

```python
import ollama

def local_agent(query, tools):
    messages = [{"role": "user", "content": query}]

    # Describe tools in system prompt
    tool_desc = "\n".join([
        f"- {t['name']}: {t['description']}"
        for t in tools
    ])

    system = f"""You are an assistant with tools:
{tool_desc}

To use a tool, respond with:
TOOL: tool_name
ARGS: {{"arg": "value"}}

After seeing the result, provide your answer."""

    response = ollama.chat(
        model='llama3.1:8b',
        messages=[{"role": "system", "content": system}] + messages
    )
    # Parse and execute tools...
```

### Recommended Models

| Model | VRAM | Agent Capability |
|-------|------|------------------|
| Llama 3.1 8B | 5GB | Basic tool use |
| Qwen 2.5 14B | 8GB | Good tool use |
| Llama 3.1 70B Q4 | 22GB | Excellent |
| Mistral Large (API) | — | Excellent |

---

## Common Patterns

### Research Agent

```python
tools = [
    search_web,
    read_url,
    summarize_text
]

prompt = """Research the topic and provide a comprehensive summary.
Use search to find information, read relevant pages, and summarize."""
```

### Data Analysis Agent

```python
tools = [
    read_csv,
    run_pandas_code,
    create_chart
]

prompt = """Analyze the data in {file} and answer: {question}
Write pandas code to analyze, then summarize findings."""
```

### Coding Agent

```python
tools = [
    read_file,
    write_file,
    run_tests,
    search_codebase
]

prompt = """Implement {feature} in the codebase.
Read existing code, implement the feature, and verify with tests."""
```

---

## Debugging Agents

| Issue | Cause | Fix |
|-------|-------|-----|
| Loops infinitely | No stop condition | Add max iterations |
| Wrong tool | Poor descriptions | Improve tool descriptions |
| Ignores results | Not in context | Include observation in messages |
| Makes up tools | Hallucination | List available tools in prompt |
| Too many calls | Over-reasoning | Simpler prompt, direct instructions |

---

## Evaluation

### Metrics

| Metric | What It Measures |
|--------|------------------|
| **Task Success Rate** | % of tasks completed correctly |
| **Tool Accuracy** | % of correct tool selections |
| **Efficiency** | Steps to complete task |
| **Safety** | Dangerous actions prevented |

### Testing

```python
test_cases = [
    {
        "query": "What's the weather in NYC?",
        "expected_tool": "get_weather",
        "expected_contains": ["temperature", "NYC"]
    },
    # ...
]

for case in test_cases:
    result = agent.run(case["query"])
    assert case["expected_tool"] in tools_called
    assert all(s in result for s in case["expected_contains"])
```

---

## Checklist

- [ ] Tools have clear descriptions
- [ ] Dangerous tools require approval
- [ ] Rate limiting implemented
- [ ] Max iterations set
- [ ] Error handling for tool failures
- [ ] Logging of all tool calls
- [ ] Testing with diverse queries
- [ ] Fallback when stuck

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| OpenAI Function Calling | Docs | https://platform.openai.com/docs/guides/function-calling |
| Anthropic Tool Use | Docs | https://docs.anthropic.com/claude/docs/tool-use |
| LangChain Agents | Docs | https://python.langchain.com/docs/modules/agents/ |
| ReAct Paper | Paper | https://arxiv.org/abs/2210.03629 |
