"""Embedding response types."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Embedding:
    """A single embedding vector.

    Attributes:
        index:  Position in the original input list.
        vector: The embedding values.
        object: Always ``"embedding"``.
    """

    index: int
    vector: List[float]
    object: str = "embedding"

    @property
    def dimensions(self) -> int:
        """Number of dimensions in this embedding."""
        return len(self.vector)

    def cosine_similarity(self, other: "Embedding") -> float:
        """Compute cosine similarity between this and another embedding."""
        return _cosine_similarity(self.vector, other.vector)

    def dot_product(self, other: "Embedding") -> float:
        """Compute dot product between this and another embedding."""
        return sum(a * b for a, b in zip(self.vector, other.vector))


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


@dataclass
class EmbeddingResponse:
    """Normalised response from an embedding request.

    Attributes:
        embeddings: List of generated embeddings.
        model:      Model ID used.
        provider:   Provider name.
        usage:      Token usage.
        raw:        Raw provider response.
    """

    embeddings: List[Embedding] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def vectors(self) -> List[List[float]]:
        """All embedding vectors as a plain list of lists."""
        return [e.vector for e in self.embeddings]

    @property
    def first(self) -> Optional[Embedding]:
        """The first embedding, or None if empty."""
        return self.embeddings[0] if self.embeddings else None

    def similarity_matrix(self) -> List[List[float]]:
        """Compute all pairwise cosine similarities between embeddings."""
        n = len(self.embeddings)
        matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                matrix[i][j] = self.embeddings[i].cosine_similarity(self.embeddings[j])
        return matrix

    @classmethod
    def from_openai_dict(cls, data: Dict[str, Any], provider: str) -> "EmbeddingResponse":
        embeddings = [
            Embedding(index=item.get("index", i), vector=item.get("embedding", []))
            for i, item in enumerate(data.get("data", []))
        ]
        return cls(
            embeddings=embeddings,
            model=data.get("model", ""),
            provider=provider,
            usage=data.get("usage", {}),
            raw=data,
        )
