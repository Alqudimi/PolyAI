"""
Advanced Example: Agentic Loop with Tool Orchestration

This example demonstrates a complete agentic loop where an AI model
orchestrates multiple tool calls to answer complex questions.

Features demonstrated:
- Function calling with multiple tools
- Multi-turn tool call loop
- Tool dispatcher pattern
- Error handling in agents

Usage:
    python examples/advanced/agentic_loop.py

No API key required (uses OVHcloud anonymous tier, 2 req/min).
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone

from polyai import Client, ClientConfig
from polyai.exceptions import UniversalAIError
from polyai.types import Tool, FunctionDefinition

# ──────────────────────────────────────────────────────────────────────────────
# Tool implementations (these are your real functions)
# ──────────────────────────────────────────────────────────────────────────────

def calculate(expression: str) -> dict:
    """Safely evaluate a mathematical expression."""
    # Only allow safe math expressions
    allowed = set("0123456789 +-*/().eE")
    if not all(c in allowed for c in expression):
        return {"error": f"Unsafe expression: {expression!r}"}
    try:
        result = eval(expression, {"__builtins__": {}, "math": math})  # noqa: S307
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": str(e)}


def get_datetime(timezone_name: str = "UTC") -> dict:
    """Get current date and time."""
    # Simplified: just return UTC time with offset info
    now = datetime.now(timezone.utc)
    return {
        "timezone": timezone_name,
        "utc_time": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "note": "Timezone conversion not implemented in this demo.",
    }


def search_wikipedia(query: str) -> dict:
    """Search Wikipedia (simulated for demo)."""
    # In a real app, call the Wikipedia API
    knowledge_base = {
        "python programming language": "Python is a high-level, interpreted programming language created by Guido van Rossum in 1991.",
        "machine learning": "Machine learning is a subset of artificial intelligence that enables systems to learn from data without explicit programming.",
        "fastapi": "FastAPI is a modern, fast Python web framework for building APIs, created by Sebastián Ramírez.",
        "ovhcloud": "OVHcloud is a French cloud computing company, one of Europe's largest cloud providers.",
    }
    query_lower = query.lower()
    for key, value in knowledge_base.items():
        if any(word in query_lower for word in key.split()):
            return {"query": query, "result": value, "source": "Wikipedia (simulated)"}
    return {"query": query, "result": "No results found for this query.", "source": "Wikipedia (simulated)"}


def unit_convert(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert between common units."""
    conversions = {
        ("celsius", "fahrenheit"): lambda x: x * 9/5 + 32,
        ("fahrenheit", "celsius"): lambda x: (x - 32) * 5/9,
        ("km", "miles"): lambda x: x * 0.621371,
        ("miles", "km"): lambda x: x * 1.60934,
        ("kg", "pounds"): lambda x: x * 2.20462,
        ("pounds", "kg"): lambda x: x * 0.453592,
        ("meters", "feet"): lambda x: x * 3.28084,
        ("feet", "meters"): lambda x: x * 0.3048,
    }
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        result = conversions[key](value)
        return {"value": value, "from": from_unit, "to": to_unit, "result": round(result, 4)}
    return {"error": f"Conversion from {from_unit!r} to {to_unit!r} not supported"}


# ──────────────────────────────────────────────────────────────────────────────
# Tool definitions
# ──────────────────────────────────────────────────────────────────────────────

TOOLS = [
    Tool(function=FunctionDefinition(
        name="calculate",
        description="Evaluate a mathematical expression. Use for arithmetic, percentages, powers.",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A mathematical expression, e.g. '(15 + 7) * 2' or '100 * 0.15'",
                },
            },
            "required": ["expression"],
        },
    )),
    Tool(function=FunctionDefinition(
        name="get_datetime",
        description="Get the current date and time",
        parameters={
            "type": "object",
            "properties": {
                "timezone_name": {
                    "type": "string",
                    "description": "Timezone name, e.g. 'UTC', 'US/Eastern'",
                    "default": "UTC",
                },
            },
        },
    )),
    Tool(function=FunctionDefinition(
        name="search_wikipedia",
        description="Search for information about a topic",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
            },
            "required": ["query"],
        },
    )),
    Tool(function=FunctionDefinition(
        name="unit_convert",
        description="Convert between units (temperature, distance, weight)",
        parameters={
            "type": "object",
            "properties": {
                "value": {"type": "number", "description": "The value to convert"},
                "from_unit": {"type": "string", "description": "Source unit"},
                "to_unit": {"type": "string", "description": "Target unit"},
            },
            "required": ["value", "from_unit", "to_unit"],
        },
    )),
]

# Function dispatcher
FUNCTIONS = {
    "calculate": calculate,
    "get_datetime": get_datetime,
    "search_wikipedia": search_wikipedia,
    "unit_convert": unit_convert,
}


def dispatch(name: str, args: dict) -> dict:
    """Execute a tool function safely."""
    if name not in FUNCTIONS:
        return {"error": f"Unknown function: {name!r}"}
    try:
        return FUNCTIONS[name](**args)
    except TypeError as e:
        return {"error": f"Invalid arguments for {name}: {e}"}
    except Exception as e:
        return {"error": str(e)}


# ──────────────────────────────────────────────────────────────────────────────
# Agent loop
# ──────────────────────────────────────────────────────────────────────────────

def run_agent(user_query: str, client: Client, max_turns: int = 10) -> str:
    """Run the agentic loop until the model produces a final text response."""

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant with access to tools. "
                "Use the tools when needed to answer questions accurately. "
                "Always verify calculations and conversions with the calculate tool."
            ),
        },
        {"role": "user", "content": user_query},
    ]

    print(f"\nUser: {user_query}\n")

    for turn in range(max_turns):
        response = client.chat(
            provider="ovhcloud",
            model="meta-llama-3_3-70b-instruct",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.0,
            max_tokens=500,
        )

        if not response.tool_calls:
            # Model finished — return the text
            print(f"Agent: {response.text}")
            return response.text

        # Model wants to call tools
        print(f"[Turn {turn + 1}] Model wants to call {len(response.tool_calls)} tool(s):")

        # Add assistant's tool-request message
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

        # Execute each tool and add results
        for tc in response.tool_calls:
            args = tc.parse_arguments()
            print(f"  → Calling {tc.name}({args})")
            result = dispatch(tc.name, args)
            print(f"  ← Result: {result}")

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result),
            })

    return "Agent loop exceeded maximum turns without a final response."


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    config = ClientConfig(max_retries=1)
    client = Client(config=config)

    questions = [
        "What is 15% of 234 + the square root of 144?",
        "Convert 100°F to Celsius and 5 miles to km.",
        "What is the current UTC time, and what is Python?",
    ]

    for question in questions:
        print("=" * 60)
        try:
            run_agent(question, client)
        except UniversalAIError as e:
            print(f"Error: {e}")
        print()


if __name__ == "__main__":
    main()
