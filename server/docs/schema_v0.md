# Schema v0 — ExperienceCurator.ai (Folders → Artifacts → Chunks → Embeddings + Runs)

This doc is the **v0 database blueprint** for ExperienceCurator.ai, aligned with
`server/src/app/db/models.py`.

## Why this schema exists (core invariants)

**Non-negotiable product rule:** “No evidence → no claim.”

So any citation must be traceable:

`chunk_id → chunks.text → artifacts.filename + artifacts.storage_path → folders.name`

This schema guarantees:

- A chunk always belongs to exactly one artifact (file)
- An artifact always belongs to exactly one folder (project bucket)
- A `chunk_id` is a stable handle you can use in citations and debugging

---

## ER sketch (how tables connect)

folders (1) ────< artifacts (many) ────< chunks (many) ────1 embeddings
|
└──────────────< run_retrieved_chunks >────────────── runs ────< run_citations

---

## Global embedding decision (locked for v0)

- EMBED_MODEL_NAME = `text-embedding-3-small`
- EMBED_DIM = `1536`

Implication:

- `embeddings.embedding` will be `vector(1536)`
- All chunks are embedded using the same model/dim so similarity search is consistent.

If you later change embedding model or dimension:

- you will either re-embed everything, or
- store multiple embeddings per chunk (more complex; not v0).

---

## Tables (data dictionary)

### 1) folders

Purpose: top-level organization + retrieval scoping.

Columns:

- id (uuid, PK)
- name (text, NOT NULL)
- created_at (timestamptz, NOT NULL, default now())
- updated_at (timestamptz, NOT NULL, default now())

Notes:

- For v0, maintain `updated_at` in app code (no triggers yet).

---

### 2) artifacts

Purpose: one row per ingested file (doc/code/etc). Stores provenance and ingestion status.

Columns:

- id (uuid, PK)
- folder_id (uuid, NOT NULL, FK → folders.id ON DELETE CASCADE)
- filename (text, NOT NULL)
- storage_path (text, NOT NULL) -- where it lives on disk / local storage
- source_url (text, NULL) -- optional external source
- content_type (text, NULL) -- e.g., "text/markdown", "application/pdf"
- file_hash (text, NULL) -- used for dedupe in uploads
- file_size (int, NULL)
- artifact_kind (text, NOT NULL) -- 'doc' | 'code' | 'repo_map' | 'resume'
- ingestion_status (text, NOT NULL) -- 'queued' | 'running' | 'succeeded' | 'failed'
- ingestion_stage (text, NULL) -- 'extract' | 'chunk' | 'embed'
- error_message (text, NULL)
- extracted_text_preview (text, NULL) -- optional: quick UI preview
- chunker_name (text, NULL)
- chunker_params (jsonb, NULL)
- embed_model (text, NULL)
- created_at (timestamptz, NOT NULL, default now())
- updated_at (timestamptz, NOT NULL, default now())

Constraints:

- CHECK (ingestion_status IN ('queued','running','succeeded','failed'))
- CHECK (artifact_kind IN ('doc','code','repo_map','resume'))
- CHECK (ingestion_stage IN ('extract','chunk','embed'))

Indexes (minimal):

- INDEX artifacts_folder_id_idx ON artifacts(folder_id)

---

### 3) chunks

Purpose: cite-able text units. **Citations reference chunk_id.**

Columns:

- chunk_id (uuid, PK) -- stable citation handle
- artifact_id (uuid, NOT NULL, FK → artifacts.id ON DELETE CASCADE)
- chunk_index (int, NOT NULL) -- stable ordering within an artifact
- text (text, NOT NULL) -- the snippet
- chunk_hash (text, NULL) -- content hash for dedupe/debug
- locator (jsonb, NULL) -- optional: { "heading": "...", "start": 123, "end": 456 }
- created_at (timestamptz, NOT NULL, default now())

Constraints:

- UNIQUE (artifact_id, chunk_index) -- prevent duplicate chunks per artifact

Indexes (minimal):

- INDEX chunks_artifact_id_idx ON chunks(artifact_id)
- INDEX chunks_artifact_id_chunk_hash_idx ON chunks(artifact_id, chunk_hash)

---

### 4) embeddings

Purpose: vector representation of each chunk for similarity search.

Columns:

- chunk_id (uuid, PK, FK → chunks.chunk_id ON DELETE CASCADE)
- embedding (vector(1536), NOT NULL) -- matches text-embedding-3-small default dimension
- model_name (text, NOT NULL) -- store "text-embedding-3-small"
- model_version (text, NULL) -- optional string you control (e.g., "2025-12-27")
- created_at (timestamptz, NOT NULL, default now())

Notes:

- v0 assumes **one embedding per chunk** (one chosen embedding model for the whole corpus).
- Later, if you want multi-model embeddings, change PK to (chunk_id, model_name) or add an embeddings_id.

Vector index:

- Add a vector index later (HNSW/IVFFlat) once you have enough data to benefit.
  (Don’t optimize prematurely in Week 1.)

---

### 5) runs

Purpose: audit/debug trail for each “ask” request.

Columns:

- trace_id (uuid, PK) -- match your request trace_id
- kind (text, NOT NULL) -- e.g. 'ask'
- created_at (timestamptz, NOT NULL, default now())
- scope_folder_ids (jsonb, NOT NULL, default '[]'::jsonb)
- question_text (text, NULL)
- citations_mode (text, NULL) -- 'on' | 'brainstorm'
- top_k (int, NULL)
- min_score (double precision, NULL)
- no_evidence (bool, NULL)
- model_name (text, NULL) -- chat model used for generation
- embed_model (text, NULL) -- e.g. "text-embedding-3-small"

Notes:

- `no_evidence` reflects retrieval strength (top score vs min score) at retrieval time.
  If generation later fails citation validation, the response may still return no-evidence even
  though the run row shows `no_evidence = false`. If you need final-response status, update the
  run after generation.

---

### 6) run_retrieved_chunks

Purpose: store what retrieval returned (evidence panel + debugging).

Columns:

- trace_id (uuid, NOT NULL, FK → runs.trace_id ON DELETE CASCADE)
- chunk_id (uuid, NOT NULL, FK → chunks.chunk_id ON DELETE CASCADE)
- score (double precision, NOT NULL)
- rank (int, NOT NULL)

Constraints:

- PRIMARY KEY (trace_id, rank) -- rank unique per run
- UNIQUE (trace_id, chunk_id) -- prevent duplicates per run

Indexes:

- INDEX rrc_trace_id_idx ON run_retrieved_chunks(trace_id)

---

### 7) run_citations

Purpose: store final, validated citations for a run.

Columns:

- trace_id (uuid, NOT NULL, FK → runs.trace_id ON DELETE CASCADE)
- chunk_id (uuid, NOT NULL, FK → chunks.chunk_id ON DELETE CASCADE)
- rank (int, NOT NULL)

Constraints:

- PRIMARY KEY (trace_id, rank)
- UNIQUE (trace_id, chunk_id)

Indexes:

- INDEX rc_trace_id_idx ON run_citations(trace_id)

---

## Required “citation lookup” query (concept)

Given a chunk_id, you must be able to fetch:

- chunk text + locator
- artifact filename + storage path
- folder name

Join chain:
`chunks → artifacts → folders`

---

## Migration build order (for Alembic)

1. Enable extensions:
   - pgvector
   - (optional) pgcrypto if you want gen_random_uuid() in SQL defaults
2. Create folders
3. Create artifacts (FK → folders)
4. Create chunks (FK → artifacts)
5. Create embeddings (FK → chunks)
6. Create runs
7. Create run_retrieved_chunks (FK → runs, chunks)
8. Create run_citations (FK → runs, chunks)
9. Add indexes + CHECK constraints
