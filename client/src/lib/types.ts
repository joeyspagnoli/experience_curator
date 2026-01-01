/** Shared API-facing shapes used across panes and routes. */

export type Folder = {
  id: string
  name: string
  created_at: string
  updated_at?: string
}

export type Artifact = {
  id: string
  folder_id: string
  filename: string
  content_type?: string | null
  storage_path?: string
  artifact_kind?: string
  ingestion_status?: 'queued' | 'running' | 'succeeded' | 'failed' | string | null
  ingestion_stage?: 'extract' | 'chunk' | 'embed' | string | null
  error_message?: string | null
  extracted_text_preview?: string | null
  created_at?: string
  updated_at?: string
}

export type HealthResponse = {
  env: string
}

export type EvidenceChunk = {
  rank?: number
  score: number
  chunk_id: string
  snippet: string
  path?: string
  artifact_path?: string
  artifact_filename?: string
  locator?: Record<string, unknown> | null
}

export type Citation = {
  chunk_id: string
  label?: string
  snippet?: string
  rank?: number
}

/** API response from POST /ask (or 501 payload handled as error). */
export type AskResponse = {
  trace_id: string
  answer_text: string
  citations?: EvidenceChunk[]
  retrieved?: { chunk_id: string; score: number; rank: number }[]
  no_evidence?: boolean
  warning?: string | null
}

/** Shape of GET /runs/{trace_id} responses. */
export type DebugRun = {
  trace_id: string
  kind?: string
  created_at?: string
  scope_folder_ids?: string[]
  question_text?: string
  citations_mode?: string
  top_k?: number
  min_score?: number
  no_evidence?: boolean
  model_name?: string
  embed_model?: string
  verification?: { status?: 'pass' | 'fail' | string; reason?: string; blocked?: boolean }
  retrieved?: {
    chunk_id: string
    score: number
    rank: number
    snippet?: string
    locator?: Record<string, unknown> | null
    artifact_filename?: string
    artifact_path?: string
  }[]
  citations?: {
    chunk_id: string
    rank?: number
    snippet?: string
    locator?: Record<string, unknown> | null
    artifact_filename?: string
    artifact_path?: string
  }[]
}

/** Generic wrapper for list endpoints that return { items: T[] }. */
export type ApiList<T> = {
  items: T[]
}
