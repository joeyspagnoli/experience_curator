"""Run trace routes for debugging and observability."""

import uuid

from fastapi import APIRouter, HTTPException, Query, Path

from ..db_client import fetch_one, fetch_all
from . import retrieval as retrieval_api


router = APIRouter()

def _coerce_trace_id(path_trace_id: str, query_trace_id: str | None) -> uuid.UUID:
    """Return a UUID parsed from either the path or query trace id."""
    candidate = path_trace_id
    if candidate in ("{trace_id}", "trace_id", "") and query_trace_id:
        candidate = query_trace_id
    candidate = candidate.strip().strip("'").strip('"')
    try:
        return uuid.UUID(candidate)
    except ValueError:
        try:
            return uuid.UUID(hex=candidate)
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail="trace_id must be a valid UUID"
            ) from exc


@router.get(
    "/runs/{trace_id}",
    description="Get a specific run from a trace ID",
)
async def get_run(
    trace_id: str = Path(
        ...,
        description="Run trace id (UUID or 32-char hex).",
        examples=["62614f35fe6347379544ae3d1937e38b"],
    ),
    trace_id_query: str | None = Query(default=None, alias="_trace_id"),
):
    """Return run metadata, retrieved chunks, and citations for a trace."""
    trace_uuid = _coerce_trace_id(trace_id, trace_id_query)

    run_row = fetch_one(
        """
        SELECT
            trace_id,
            kind,
            created_at,
            scope_folder_ids,
            question_text,
            citations_mode,
            top_k,
            min_score,
            no_evidence,
            model_name,
            embed_model
        FROM runs
        WHERE trace_id = %s
        """,
        (trace_uuid,),
    )
    if not run_row:
        raise HTTPException(status_code=404, detail="run not found")

    retrieved_rows = fetch_all(
        """
        SELECT
            rrc.chunk_id,
            rrc.score,
            rrc.rank,
            left(c.text, %s) AS snippet,
            c.locator AS locator,
            a.filename AS artifact_filename,
            a.storage_path AS artifact_path
        FROM run_retrieved_chunks rrc
        JOIN chunks c ON c.chunk_id = rrc.chunk_id
        JOIN artifacts a ON a.id = c.artifact_id
        WHERE rrc.trace_id = %s
        ORDER BY rrc.rank
        """,
        (retrieval_api.DEFAULT_SNIPPET_LEN, trace_uuid),
    )

    citation_rows = fetch_all(
        """
        SELECT
            rc.chunk_id,
            rc.rank,
            left(c.text, %s) AS snippet,
            c.locator AS locator,
            a.filename AS artifact_filename,
            a.storage_path AS artifact_path
        FROM run_citations rc
        JOIN chunks c ON c.chunk_id = rc.chunk_id
        JOIN artifacts a ON a.id = c.artifact_id
        WHERE rc.trace_id = %s
        ORDER BY rc.rank
        """,
        (retrieval_api.DEFAULT_SNIPPET_LEN, trace_uuid),
    )

    return {
        **run_row,
        "retrieved": retrieved_rows,
        "citations": citation_rows,
    }


@router.get(
    "/runs/{trace_id}/retrieved-chunks",
    description="Placeholder endpoint for fetching retrieved chunks for a run.",
)
async def get_run_retrieved_chunks(_trace_id: str):
    """Return 501 until retrieved chunks lookup is implemented."""
    raise HTTPException(
        status_code=501, detail="Run retrieved chunks is not implemented yet"
    )
