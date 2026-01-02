"""Unit tests for embedding normalization helpers."""

import math
import os

import pytest

from app import db_client
from app.services.embed import l2_normalize, normalize_embeddings


def _sum_squares(vec: list[float]) -> float:
    # Sum of squares checks length without reusing normalization logic.
    return sum(x * x for x in vec)


def _parse_embedding(value: object) -> list[float]:
    """Parse a stored pgvector embedding into a list of floats."""
    if isinstance(value, str):
        # pgvector may return strings like "[0.1, -0.2, ...]" without an adapter.
        cleaned = value.strip().strip("[]()")
        if not cleaned:
            return []
        return [float(x) for x in cleaned.split(",")]
    if isinstance(value, (list, tuple)):
        return [float(x) for x in value]
    return [float(x) for x in value]  # type: ignore[arg-type]


def test_l2_normalize_unit_length_from_mock_db_vector() -> None:
    """Normalization should return a unit-length vector for typical input."""

    def fake_db_fetch_embedding() -> list[float]:
        # Simulated DB row: small, easy-to-check vector.
        return [3.0, 4.0]

    raw_vec = fake_db_fetch_embedding()
    normalized = l2_normalize(raw_vec)
    expected = [0.6, 0.8]  # 3-4-5 triangle, so norm is 5.

    assert normalized == pytest.approx(expected)
    assert _sum_squares(normalized) == pytest.approx(1.0)


# Parametrized inputs cover multiple "happy path" shapes.
@pytest.mark.parametrize(
    ("vec", "expected"),
    [
        ([1.0, 0.0, 0.0], [1.0, 0.0, 0.0]),
        ([-2.0, 0.0, 2.0], [-math.sqrt(0.5), 0.0, math.sqrt(0.5)]),
    ],
)
def test_l2_normalize_handles_negative_and_unit_vectors(
    vec: list[float],
    expected: list[float],
) -> None:
    """Normalization should keep direction and produce unit length."""
    normalized = l2_normalize(vec)

    assert normalized == pytest.approx(expected)
    assert _sum_squares(normalized) == pytest.approx(1.0)


def test_l2_normalize_zero_vector_returns_unchanged() -> None:
    """Zero vectors should remain unchanged to avoid division by zero."""
    vec = [0.0, 0.0, 0.0]
    normalized = l2_normalize(vec)

    assert normalized == vec
    assert _sum_squares(normalized) == 0.0


def test_normalize_embeddings_multiple_vectors() -> None:
    """Batch normalization should normalize each vector independently."""
    embeddings = [[3.0, 4.0], [0.0, 0.0], [1.0, 1.0]]

    normalized = normalize_embeddings(embeddings)

    assert normalized[0] == pytest.approx([0.6, 0.8])
    assert normalized[1] == [0.0, 0.0]
    assert _sum_squares(normalized[2]) == pytest.approx(1.0)


def test_normalize_embeddings_empty_list() -> None:
    """Empty input should return an empty list."""
    assert normalize_embeddings([]) == []


def test_db_embeddings_are_unit_length_when_enabled() -> None:
    """Optionally verify stored embeddings are unit length."""
    if os.getenv("RUN_DB_TESTS") != "1":
        pytest.skip("Set RUN_DB_TESTS=1 to enable DB normalization checks.")

    row = db_client.fetch_one("SELECT embedding FROM embeddings LIMIT 1;")
    if row is None:
        pytest.skip("No embeddings found for normalization check.")

    embedding = row["embedding"] if isinstance(row, dict) else row[0]
    embedding_list = _parse_embedding(embedding)

    assert _sum_squares(embedding_list) == pytest.approx(1.0)
