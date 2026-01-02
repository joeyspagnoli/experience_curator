"""Embedding helpers for turning text into vectors."""

import logging
import math
from typing import Any

import httpx

from ..config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

OPENAI_BASE_URL = "https://api.openai.com/v1"
EMBEDDINGS_ENDPOINT = f"{OPENAI_BASE_URL}/embeddings"
DEFAULT_EMBED_MODEL = "text-embedding-3-small"


class EmbeddingError(Exception):
    """Raised when embedding requests fail or return unexpected data."""


def l2_normalize(vec: list[float]) -> list[float]:
    """Return an L2-normalized copy of a vector."""
    # L2 norm = sqrt(sum(x^2))
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]


def normalize_embeddings(embeddings: list[list[float]]) -> list[list[float]]:
    """Normalize each embedding vector using L2 norm."""
    return [l2_normalize(vec) for vec in embeddings]


def embed_texts(
    texts: list[str],
    *,
    model: str = DEFAULT_EMBED_MODEL,
    timeout_s: float = 30.0,
) -> tuple[list[list[float]], dict[str, Any]]:
    """
    Embed a list of strings using the OpenAI embeddings endpoint.

    Returns a list of embedding vectors and model metadata.
    """
    if not texts:
        return [], {"model_name": model, "model_version": None}

    # Auth + JSON content type for the OpenAI REST API.
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    # Payload matches the embeddings API: model name + input texts.
    payload = {"model": model, "input": texts}

    try:
        # POST the request to OpenAI and fail fast on any HTTP error.
        response = httpx.post(
            EMBEDDINGS_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=timeout_s,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception("Embedding request failed")
        raise EmbeddingError(f"Embedding request failed: {exc}") from exc

    # Parse JSON response into embeddings, keeping input order.
    data = response.json()
    if "data" not in data:
        raise EmbeddingError("Embedding response missing data field")

    entries = data["data"]
    if not isinstance(entries, list):
        raise EmbeddingError("Embedding response data is not a list")

    # Sort by index so embeddings align with input texts.
    entries_sorted = sorted(entries, key=lambda item: item.get("index", 0))
    embeddings = [item.get("embedding") for item in entries_sorted]
    if any(vec is None for vec in embeddings):
        raise EmbeddingError("Embedding response missing vectors")
    if len(embeddings) != len(texts):
        raise EmbeddingError("Embedding response length mismatch")
    embeddings = normalize_embeddings(embeddings)
    return embeddings, {"model_name": data.get("model", model), "model_version": None}
