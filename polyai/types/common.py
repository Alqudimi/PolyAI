"""Shared primitive types used across all resources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Usage:
    """Token / resource usage returned by a provider.

    Attributes:
        prompt_tokens:     Number of tokens in the prompt / input.
        completion_tokens: Number of tokens in the generated completion.
        total_tokens:      Sum of prompt + completion tokens.
        extra:             Provider-specific usage fields (cache hits, reasoning tokens, etc.).
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Usage":
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
            extra={k: v for k, v in data.items() if k not in ("prompt_tokens", "completion_tokens", "total_tokens")},
        )

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


@dataclass
class FunctionDefinition:
    """JSON Schema definition for a callable function.

    Args:
        name:        Function name (must match ``[a-zA-Z0-9_-]{1,64}``).
        description: Human-readable description shown to the model.
        parameters:  JSON Schema object describing the function parameters.
        strict:      Enable strict schema validation (OpenAI o-series).
    """

    name: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=lambda: {"type": "object", "properties": {}})
    strict: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"name": self.name, "description": self.description, "parameters": self.parameters}
        if self.strict:
            d["strict"] = True
        return d


@dataclass
class Tool:
    """A tool (function) the model may call.

    Args:
        function: The function definition.
        type:     Tool type — always ``"function"`` for current providers.
    """

    function: FunctionDefinition
    type: str = "function"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "function": self.function.to_dict()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tool":
        fn = data.get("function", {})
        return cls(
            function=FunctionDefinition(
                name=fn.get("name", ""),
                description=fn.get("description", ""),
                parameters=fn.get("parameters", {}),
            ),
            type=data.get("type", "function"),
        )


@dataclass
class ToolCall:
    """A tool call requested by the model.

    Attributes:
        id:        Unique identifier for this tool call.
        type:      Always ``"function"``.
        name:      The function name being called.
        arguments: JSON string of the arguments dict.
    """

    id: str
    type: str
    name: str
    arguments: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        fn = data.get("function", {})
        return cls(
            id=data.get("id", ""),
            type=data.get("type", "function"),
            name=fn.get("name", ""),
            arguments=fn.get("arguments", "{}"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "function": {"name": self.name, "arguments": self.arguments},
        }

    def parse_arguments(self) -> Dict[str, Any]:
        """Parse the JSON arguments string into a dict."""
        import json
        try:
            return json.loads(self.arguments)
        except json.JSONDecodeError:
            return {}
