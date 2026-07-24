# ExperienceCurator — Project Notes (sample document)

> Sample document for demoing ExperienceCurator. It describes this very project
> so the resume-tailor demo has real engineering evidence to cite.

## Summary

Built a single-tenant RAG system ("career memory") with a FastAPI backend and a
React 19/TypeScript client. Users upload career documents; the system answers
questions and drafts resume bullets grounded in those documents, with
chunk-level citations enforced in code.

## Backend engineering

- Designed a 3-stage ingestion pipeline (extract → chunk → embed) with per-stage
  status tracking and typed failure states, so a bad PDF fails loudly at the
  extract stage instead of poisoning retrieval.
- Chunking is strategy-tagged (hybrid_v0: 800-char chunks, 120 overlap;
  heading-aware for Markdown, page-aware for PDFs) and every chunk stores a
  locator (page/heading) so citations point at a place, not just a file.
- Retrieval uses Postgres + pgvector cosine similarity over 1536-dim
  text-embedding-3-small vectors, top-k 8 with a 0.25 minimum-score gate.
- Citation validation is all-or-nothing against the retrieved set: if the model
  cites a chunk id that was not retrieved, the response degrades to an explicit
  no_evidence result instead of shipping an unverifiable answer.
- Every query records a run (parameters, retrieved chunks with scores, final
  citations) keyed by an x-trace-id, inspectable via a debug endpoint and UI.
- Test suite is hermetic: LLM, embeddings, and DB boundaries are monkeypatched,
  so 50+ tests run in under 2 seconds with no network or database.

## Ops

- Postgres 16 + pgvector via docker-compose; schema managed with Alembic
  migrations, raw parameterized SQL via psycopg at request time.
