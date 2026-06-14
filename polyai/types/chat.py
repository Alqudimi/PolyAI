"""Chat-related types: messages, responses, streaming chunks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from polyai.types.common import ToolCall, Usage


# ---------------------------------------------------------------------------
# Message constructors
# ---------------------------------------------------------------------------

def SystemMessage(content: str) -> Dict[str, str]:
    """Convenience constructor for a system message dict."""
    return {"role": "system", "content": content}


def UserMessage(content: Union[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Convenience constructor for a user message dict.

    ``content`` can be a plain string or a list of content parts for multimodal
    inputs (text + images).
    """
    return {"role": "user", "content": content}


def AssistantMessage(content: str, *, tool_calls: Optional[List[ToolCall]] = None) -> Dict[str, Any]:
    """Convenience constructor for an assistant message dict."""
    msg: Dict[str, Any] = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = [tc.to_dict() for tc in tool_calls]
    return msg


def ToolMessage(content: str, *, tool_call_id: str) -> Dict[str, Any]:
    """Convenience constructor for a tool-result message dict."""
    return {"role": "tool", "content": content, "tool_call_id": tool_call_id}


# Type alias for any message dict
ChatMessage = Dict[str, Any]


# ---------------------------------------------------------------------------
# Response types
# ---------------------------------------------------------------------------

@dataclass
class ChatResponse:
    """Normalised response from a chat completion request.

    Attributes:
        text:          The generated text content of the first choice.
        model:         Model ID as returned by the provider.
        provider:      Provider name (``"ovhcloud"``, ``"pollinations"``, etc.).
        finish_reason: Stop reason (``"stop"``, ``"length"``, ``"tool_calls"``, etc.).
        tool_calls:    List of tool calls requested by the model, if any.
        usage:         Token usage for this request.
        id:            Provider-assigned request / completion ID.
        raw:           The raw provider response dict for advanced use.
    """

    text: str
    model: str
    provider: str
    finish_reason: str = "stop"
    tool_calls: List[ToolCall] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    id: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.text

    @classmethod
    def from_openai_dict(cls, data: Dict[str, Any], provider: str) -> "ChatResponse":
        """Construct from an OpenAI-format response dict."""
        choices = data.get("choices", [{}])
        first = choices[0] if choices else {}
        message = first.get("message", {})
        content = message.get("content") or ""

        raw_tool_calls = message.get("tool_calls") or []
        tool_calls = [ToolCall.from_dict(tc) for tc in raw_tool_calls]

        usage_data = data.get("usage") or {}

        return cls(
            text=content,
            model=data.get("model", ""),
            provider=provider,
            finish_reason=first.get("finish_reason", "stop") or "stop",
            tool_calls=tool_calls,
            usage=Usage.from_dict(usage_data),
            id=data.get("id", ""),
            raw=data,
        )


@dataclass
class ChatDelta:
    """A single streaming delta containing incremental content."""

    content: str = ""
    role: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    finish_reason: Optional[str] = None


@dataclass
class ChatChunk:
    """A streaming chunk yielded during a streaming chat completion.

    Attributes:
        delta:    The incremental content for this chunk.
        model:    Model ID.
        provider: Provider name.
        id:       Provider-assigned stream ID.
        raw:      The raw chunk dict.
    """

    delta: str
    model: str
    provider: str
    id: str = ""
    finish_reason: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.delta

    @classmethod
    def from_openai_dict(cls, data: Dict[str, Any], provider: str) -> "ChatChunk":
        choices = data.get("choices", [{}])
        first = choices[0] if choices else {}
        delta = first.get("delta", {})
        content = delta.get("content") or ""
        return cls(
            delta=content,
            model=data.get("model", ""),
            provider=provider,
            id=data.get("id", ""),
            finish_reason=first.get("finish_reason"),
            raw=data,
        )
