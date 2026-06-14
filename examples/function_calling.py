"""
function_calling.py — Tool use / function calling with OVHcloud.

Demonstrates defining tools, having the model request a call, executing it,
and feeding the result back for a final answer.
"""

import json
from polyai import Client
from polyai.types import FunctionDefinition, Tool

client = Client()

# ── Define tools ──────────────────────────────────────────────────────────

get_weather_tool = Tool(
    function=FunctionDefinition(
        name="get_weather",
        description="Get the current weather for a given location.",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name, e.g. 'Paris' or 'New York'",
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit",
                },
            },
            "required": ["location"],
        },
    )
)

get_population_tool = Tool(
    function=FunctionDefinition(
        name="get_population",
        description="Get the population of a city.",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
            },
            "required": ["city"],
        },
    )
)


# ── Simulated tool executor ───────────────────────────────────────────────

def execute_tool(name: str, args: dict) -> str:
    """Simulate tool execution with fake data."""
    if name == "get_weather":
        city = args.get("location", "Unknown")
        unit = args.get("unit", "celsius")
        temp = "22°C" if unit == "celsius" else "72°F"
        return json.dumps({"city": city, "temperature": temp, "condition": "Partly cloudy"})
    if name == "get_population":
        populations = {"Paris": 2_161_000, "London": 8_900_000, "New York": 8_336_000}
        city = args.get("city", "Unknown")
        pop = populations.get(city, 1_000_000)
        return json.dumps({"city": city, "population": pop})
    return json.dumps({"error": f"Unknown tool: {name}"})


# ── Agentic loop ──────────────────────────────────────────────────────────

messages = [
    {"role": "user", "content": "What's the weather in Paris and what is Paris's population?"},
]

print("=== Function Calling Loop ===")
print(f"User: {messages[0]['content']}\n")

while True:
    response = client.chat(
        provider="ovhcloud",
        model="meta-llama-3_3-70b-instruct",
        messages=messages,
        tools=[get_weather_tool, get_population_tool],
        tool_choice="auto",
        max_tokens=500,
    )

    if response.finish_reason == "tool_calls" and response.tool_calls:
        print(f"Model requested {len(response.tool_calls)} tool call(s):")
        for tc in response.tool_calls:
            args = tc.parse_arguments()
            print(f"  → {tc.name}({args})")
            result = execute_tool(tc.name, args)
            print(f"  ← {result}")

        messages.append({
            "role": "assistant",
            "content": response.text or "",
            "tool_calls": [tc.to_dict() for tc in response.tool_calls],
        })
        for tc in response.tool_calls:
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": execute_tool(tc.name, tc.parse_arguments()),
            })
    else:
        print(f"\nFinal answer:\n{response.text}")
        break

client.close()
