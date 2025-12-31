"""Retrieval routes for similarity search over embedded chunks."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from pgvector import Vector

from ..db_client import fetch_all
from ..services.embed import embed_texts

router = APIRouter()

DEFAULT_SNIPPET_LEN = 300
DEFAULT_MIN_SCORE = 0.25
DEFAULT_TOP_K = 8


class RetrieveRequest(BaseModel):
    question: str = Field(..., description="User question to retrieve evidence for.")
    scope_folder_ids: list[uuid.UUID] | None = Field(
        default=None,
        description="Restrict retrieval to one or more folder IDs.",
    )
    top_k: int = Field(
        default=DEFAULT_TOP_K,
        ge=1,
        le=50,
        description="Maximum number of chunks to return.",
    )


@router.post(
    "/retrieve",
    description="Retrieve top-k chunks for a question (cosine similarity).",
)
async def retrieve(payload: RetrieveRequest) -> dict[str, Any]:
    """Embed the question and return top-k similar chunks with scores."""
    # Basic input validation to avoid empty queries.
    question = payload.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="question cannot be empty",
        )

    # Embed the question (returns normalized vectors for cosine similarity).
    embeddings, _meta = embed_texts([question])
    # Wrap in Vector so psycopg sends the parameter as pgvector, not a float array.
    query_embedding = Vector(embeddings[0])

    # Build parameter list for the SQL query in order of appearance.
    params: list[Any] = [DEFAULT_SNIPPET_LEN, query_embedding]
    where_clause = ""
    if payload.scope_folder_ids:
        # Restrict retrieval to selected folders when scope is provided.
        where_clause = "WHERE a.folder_id = ANY(%s) -- scope filter"
        params.append(payload.scope_folder_ids)

    sql = f"""
        SELECT
            c.chunk_id, -- stable citation handle
            left(c.text, %s) AS snippet, -- short preview for UI/debug
            a.storage_path AS artifact_path, -- provenance for evidence
            1.0 - (e.embedding <=> %s) AS score -- cosine similarity score
        FROM embeddings e -- search space of vectors
        JOIN chunks c ON c.chunk_id = e.chunk_id -- attach chunk text
        JOIN artifacts a ON a.id = c.artifact_id -- attach artifact metadata
        {where_clause}
        ORDER BY e.embedding <=> %s -- nearest neighbors first
        LIMIT %s; -- cap number of results
        """
    params.extend([query_embedding, payload.top_k])

    # Execute parameterized SQL to avoid injection and preserve types.
    rows = fetch_all(sql, params)
    if not rows:
        return {"no_evidence": True, "results": []}

    # Strict no-evidence: if top score is too low, return empty results.
    top_score = rows[0].get("score", 0.0)
    if top_score < DEFAULT_MIN_SCORE:
        return {"no_evidence": True, "results": []}

    return {"no_evidence": False, "results": rows}
