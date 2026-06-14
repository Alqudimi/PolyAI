"""
General-purpose helper utilities for the polyai SDK.
"""

from __future__ import annotations

import base64
import math
import re
from typing import Any, Dict, List, Optional, Union


def build_vision_message(
    text: str,
    images: Union[str, List[str]],
    *,
    role: str = "user",
    image_detail: str = "auto",
) -> Dict[str, Any]:
    """Build a multimodal user message containing text and one or more images.

    Images can be provided as:
    - HTTP/S URLs pointing to publicly accessible images
    - ``data:image/...;base64,...`` data URIs
    - Local file paths (automatically base64-encoded)

    Args:
        text:         The text part of the message.
        images:       A single image or a list of images (URLs, data URIs, or file paths).
        role:         Message role. Default: ``"user"``.
        image_detail: Image detail level for vision models (``"low"``, ``"high"``, ``"auto"``).

    Returns:
        A role/content dict with both text and image parts, compatible with all
        OpenAI-format vision endpoints.

    Example::

        msg = build_vision_message(
            "What's in this image?",
            "https://example.com/photo.jpg",
        )
        response = client.chat(provider="ovhcloud", model="Qwen/Qwen3-VL-8B-Instruct", messages=[msg])
    """
    if isinstance(images, str):
        images = [images]

    parts: List[Dict[str, Any]] = [{"type": "text", "text": text}]

    for img in images:
        if img.startswith("data:"):
            image_url = img
        elif img.startswith("http://") or img.startswith("https://"):
            image_url = img
        else:
            image_url = image_url_to_base64(img)

        parts.append({
            "type": "image_url",
            "image_url": {"url": image_url, "detail": image_detail},
        })

    return {"role": role, "content": parts}


def image_url_to_base64(file_path: str, *, mime_type: Optional[str] = None) -> str:
    """Read a local image file and return a base64 data URI.

    Args:
        file_path: Local path to the image file.
        mime_type: MIME type override. If omitted, inferred from file extension.

    Returns:
        A ``data:image/...;base64,...`` URI string.
    """
    import mimetypes
    import os

    if mime_type is None:
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            ext = os.path.splitext(file_path)[1].lower()
            mime_type = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }.get(ext, "image/jpeg")

    with open(file_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")

    return f"data:{mime_type};base64,{data}"


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute the cosine similarity between two vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Cosine similarity in the range [-1, 1].
    """
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def truncate_messages(
    messages: List[Dict[str, Any]],
    max_tokens: int,
    *,
    keep_system: bool = True,
    chars_per_token: float = 4.0,
) -> List[Dict[str, Any]]:
    """Truncate a message list to fit within an approximate token budget.

    Removes messages from the middle of the conversation to preserve both the
    system prompt (if ``keep_system=True``) and the most recent user turn.

    Args:
        messages:        The full conversation message list.
        max_tokens:      Approximate maximum token count.
        keep_system:     Keep the first system message regardless of budget.
        chars_per_token: Characters-per-token approximation. Default: 4.0.

    Returns:
        A truncated message list that fits within the budget.
    """
    budget = max_tokens * chars_per_token

    def _chars(msg: Dict[str, Any]) -> int:
        content = msg.get("content", "")
        if isinstance(content, str):
            return len(content)
        if isinstance(content, list):
            return sum(len(p.get("text", "")) for p in content if isinstance(p, dict))
        return 0

    total = sum(_chars(m) for m in messages)
    if total <= budget:
        return messages

    result = list(messages)
    system_offset = 0

    if keep_system and result and result[0].get("role") == "system":
        system_offset = 1

    while len(result) > system_offset + 1 and sum(_chars(m) for m in result) > budget:
        result.pop(system_offset)

    return result


def count_tokens_approx(text: str, chars_per_token: float = 4.0) -> int:
    """Approximate token count for a text string.

    This is a rough estimate (~4 chars/token for English). For exact counts,
    use a tokenizer like ``tiktoken``.

    Args:
        text:            The string to estimate.
        chars_per_token: Characters per token ratio. Default: 4.0.

    Returns:
        Approximate number of tokens.
    """
    return max(1, int(len(text) / chars_per_token))


def merge_tool_call_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge fragmented streaming tool call deltas into complete tool call objects.

    When a provider streams tool calls across multiple chunks, each with partial
    ``arguments`` strings, this function reassembles them into complete tool call
    dicts suitable for inclusion in follow-up messages.

    Args:
        chunks: List of raw ``tool_calls`` delta dicts from streaming chunks.

    Returns:
        List of complete tool call dicts.
    """
    merged: Dict[int, Dict[str, Any]] = {}

    for chunk in chunks:
        idx = chunk.get("index", 0)
        if idx not in merged:
            merged[idx] = {
                "id": chunk.get("id", ""),
                "type": chunk.get("type", "function"),
                "function": {"name": "", "arguments": ""},
            }
        fn = chunk.get("function", {})
        if fn.get("name"):
            merged[idx]["function"]["name"] = fn["name"]
        if fn.get("arguments"):
            merged[idx]["function"]["arguments"] += fn["arguments"]
        if chunk.get("id"):
            merged[idx]["id"] = chunk["id"]

    return [merged[k] for k in sorted(merged.keys())]
