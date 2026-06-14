# Tutorial 3: Function Calling

> **Level:** Intermediate | **Time:** 20 minutes
> **Repository:** https://github.com/Alqudimi/PolyAI

---

## Goals

- Define tools (functions) the AI can call
- Build a complete agentic loop
- Parse tool call arguments
- Chain multiple tool calls

---

## Prerequisites

- Completed [Tutorial 1](01-first-chat.md)
- Basic Python knowledge

---

## What is Function Calling?

Function calling lets you tell the AI: "here are some tools you can use." When the AI decides a tool is needed to answer the user's question, it responds with a **tool call** instead of text.

Your code then:
1. Receives the tool call
2. Runs the actual function
3. Sends the result back to the AI
4. Gets the final text response

This is the foundation of AI agents.

---

## Step 1: Define a Tool

```python
from polyai import Client
from polyai.types import Tool, FunctionDefinition

client = Client()

# Define what the AI can call
weather_tool = Tool(function=FunctionDefinition(
    name="get_weather",
    description="Get the current weather for a city",
    parameters={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name, e.g. 'London, UK'",
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "Temperature unit",
                "default": "celsius",
            },
        },
        "required": ["city"],
    },
))
```

---

## Step 2: Send a Request with Tools

```python
response = client.chat(
    provider="ovhcloud",
    model="meta-llama-3_3-70b-instruct",  # larger model handles tools better
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=[weather_tool],
    tool_choice="auto",  # let the model decide when to use tools
)

if response.tool_calls:
    print(f"The model wants to call: {response.tool_calls[0].name}")
    print(f"With arguments: {response.tool_calls[0].parse_arguments()}")
else:
    print(f"Direct answer: {response.text}")
```

Output:
```
The model wants to call: get_weather
With arguments: {'city': 'Paris', 'unit': 'celsius'}
```

---

## Step 3: Complete Agentic Loop

A full loop: user asks → AI calls tool → you run function → AI answers.

```python
import json
from polyai import Client
from polyai.types import Tool, FunctionDefinition

client = Client()

# ──────────────────────────────────────────────────────────────
# 1. Define real functions

def get_weather(city: str, unit: str = "celsius") -> dict:
    """Simulated weather function."""
    # In a real app, call a weather API here
    data = {
        "London, UK": {"temp": 15, "condition": "Cloudy"},
        "Paris": {"temp": 22, "condition": "Sunny"},
        "Tokyo": {"temp": 28, "condition": "Humid"},
    }
    info = data.get(city, {"temp": 20, "condition": "Unknown"})
    unit_str = "°C" if unit == "celsius" else "°F"
    temp = info["temp"] if unit == "celsius" else info["temp"] * 9/5 + 32
    return {"city": city, "temperature": f"{temp:.0f}{unit_str}", "condition": info["condition"]}


def get_time(timezone: str = "UTC") -> dict:
    """Get current time in a timezone."""
    from datetime import datetime
    import pytz  # pip install pytz
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return {"timezone": timezone, "time": now.strftime("%H:%M %Z")}
    except Exception:
        return {"timezone": timezone, "time": "Unknown"}

# ──────────────────────────────────────────────────────────────
# 2. Define tools

tools = [
    Tool(function=FunctionDefinition(
        name="get_weather",
        description="Get current weather for a city",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["city"],
        },
    )),
    Tool(function=FunctionDefinition(
        name="get_time",
        description="Get current time in a timezone",
        parameters={
            "type": "object",
            "properties": {
                "timezone": {"type": "string", "description": "e.g. 'Europe/London', 'Asia/Tokyo'"},
            },
            "required": ["timezone"],
        },
    )),
]

# ──────────────────────────────────────────────────────────────
# 3. Function dispatcher

FUNCTIONS = {
    "get_weather": get_weather,
    "get_time": get_time,
}

def call_function(name: str, args: dict):
    if name not in FUNCTIONS:
        return {"error": f"Unknown function: {name}"}
    try:
        return FUNCTIONS[name](**args)
    except Exception as e:
        return {"error": str(e)}

# ──────────────────────────────────────────────────────────────
# 4. Agentic loop

def agent_chat(user_input: str) -> str:
    messages = [{"role": "user", "content": user_input}]

    while True:
        response = client.chat(
            provider="ovhcloud",
            model="meta-llama-3_3-70b-instruct",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        if not response.tool_calls:
            # Model responded with text — we're done
            return response.text

        # Model wants to call functions
        # 1. Add assistant's tool-call message
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": tc.arguments},
                }
                for tc in response.tool_calls
            ],
        })

        # 2. Execute each function and add results
        for tc in response.tool_calls:
            args = tc.parse_arguments()
            result = call_function(tc.name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result),
            })

        # 3. Loop — let the model generate a response using tool results

# ──────────────────────────────────────────────────────────────
# 5. Test it

if __name__ == "__main__":
    answer = agent_chat("What's the weather in Paris and what time is it in Tokyo?")
    print(f"AI: {answer}")
```

---

## Step 4: Controlling Tool Choice

```python
# Let the model decide (default)
response = client.chat(..., tool_choice="auto")

# Never use tools — always respond with text
response = client.chat(..., tool_choice="none")

# Always use a specific tool
response = client.chat(
    ...,
    tool_choice={"type": "function", "function": {"name": "get_weather"}},
)
```

---

## Step 5: Parsing Complex Arguments

```python
response = client.chat(
    provider="ovhcloud",
    model="meta-llama-3_3-70b-instruct",
    messages=[{"role": "user", "content": "Create a calendar event for lunch with Alice at 12:30 next Monday"}],
    tools=[calendar_tool],
)

if response.tool_calls:
    tc = response.tool_calls[0]
    args = tc.parse_arguments()  # safely returns dict (handles JSON parse errors)
    print(args)
    # {'title': 'Lunch with Alice', 'time': '12:30', 'day': 'next Monday', 'participants': ['Alice']}
```

---

## Expected Results

After this tutorial:
- You can define tools with JSON Schema
- You understand the tool call → run → send result → respond loop
- You can build simple AI agents

---

## Next Steps

- [Tutorial 4: Vision](04-vision.md) — send images to the AI
- [Tutorial 6: Production Deployment](06-production.md) — deploy agents
