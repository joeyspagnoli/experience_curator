import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchJson, isApiError } from '../lib/api'
import type { DebugRun } from '../lib/types'
import { clampText } from '../lib/utils'

type DebugPaneProps = {
  traceId: string | null
  fullWidth?: boolean
}

// Right pane: run trace details, retrieved chunks, and citations.
export function DebugPane({ traceId, fullWidth = false }: DebugPaneProps) {
  const [run, setRun] = useState<DebugRun | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [chunkModalId, setChunkModalId] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    const loadRun = async () => {
      if (!traceId) return
      setLoading(true)
      setError(null)
      try {
        const { data } = await fetchJson<DebugRun>(`/runs/${traceId}`)
        if (!alive) return
        setRun(data)
      } catch (err) {
        if (!alive) return
        setError(isApiError(err) ? err.message : 'Failed to load run')
      } finally {
        if (alive) setLoading(false)
      }
    }

    loadRun()
    return () => {
      alive = false
    }
  }, [traceId])

  const scopeLabel = useMemo(() => {
    if (!run?.scope_folder_ids || run.scope_folder_ids.length === 0) {
      return 'All folders'
    }
    return run.scope_folder_ids.join(', ')
  }, [run])

  const verification = run?.verification
  const verificationStatus = verification?.status ?? 'unknown'

  if (!traceId) {
    return (
      <div className="pane-content">
        <header className="pane-header">
          <div>
            <h2>Debug</h2>
            <p>Run traces and evidence will appear here.</p>
          </div>
        </header>
        <div className="empty-state">Ask a question to generate a trace.</div>
      </div>
    )
  }

  return (
    <div className={`pane-content ${fullWidth ? 'pane-content--full' : ''}`}>
      <header className="pane-header">
        <div>
          <h2>Debug</h2>
          <p>Active trace details, citations, and retrieved evidence.</p>
        </div>
        <div className="trace-actions">
          <span className="muted">Active trace_id:</span>
          <span className="mono">{traceId}</span>
          <button
            type="button"
            className="button button--ghost"
            onClick={() => navigator.clipboard.writeText(traceId)}
          >
            Copy
          </button>
          {!fullWidth && (
            <Link className="button" to={`/debug/${traceId}`}>
              Open full page
            </Link>
          )}
        </div>
      </header>

      {loading && <div className="empty-state">Loading run…</div>}
      {error && <div className="empty-state error">{error}</div>}

      {run && !loading && !error && (
        <>
          <section className="card section">
            <div className="section-title">Run summary</div>
            <div className="meta-grid">
              <div>
                <div className="muted">Scope</div>
                <div>{scopeLabel}</div>
              </div>
              <div>
                <div className="muted">Citations</div>
                <div>{run.citations_mode ?? 'on'}</div>
              </div>
              <div>
                <div className="muted">Verification</div>
                <div className={`badge badge--${verificationStatus}`}>{verificationStatus}</div>
              </div>
              <div>
                <div className="muted">Reason</div>
                <div>{verification?.reason ?? 'No verification data'}</div>
              </div>
            </div>
          </section>

          <section className="card section">
            <div className="section-title">Evidence</div>
            {run.retrieved && run.retrieved.length > 0 ? (
              <div className="table">
                {run.retrieved.map((chunk) => (
                  <div key={chunk.chunk_id} className="table-row">
                    <div className="mono">{chunk.chunk_id.slice(0, 8)}</div>
                    <div>{chunk.score.toFixed(3)}</div>
                    <div>{chunk.artifact_filename ?? chunk.artifact_path ?? '—'}</div>
                    <div className="muted">{clampText(chunk.snippet ?? '', 90)}</div>
                    <button
                      type="button"
                      className="link"
                      onClick={() => setChunkModalId(chunk.chunk_id)}
                    >
                      View
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">No retrieved chunks.</div>
            )}
          </section>

          <section className="card section">
            <div className="section-title">Citations</div>
            {run.citations && run.citations.length > 0 ? (
              <ul className="citation-list">
                {run.citations.map((citation) => (
                  <li key={citation.chunk_id}>
                    <button
                      type="button"
                      className="link"
                      onClick={() => setChunkModalId(citation.chunk_id)}
                    >
                      {citation.chunk_id}
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="empty-state">No citations recorded.</div>
            )}
          </section>

          <section className="card section">
            <details>
              <summary className="section-title">Raw JSON</summary>
              <pre className="code-block">{JSON.stringify(run, null, 2)}</pre>
            </details>
          </section>
        </>
      )}

      {chunkModalId && (
        <ChunkViewer chunkId={chunkModalId} onClose={() => setChunkModalId(null)} />
      )}
    </div>
  )
}

function ChunkViewer({ chunkId, onClose }: { chunkId: string; onClose: () => void }) {
  const [payload, setPayload] = useState<unknown>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const { data } = await fetchJson<unknown>(`/chunks/${chunkId}`)
        if (!alive) return
        setPayload(data)
      } catch (err) {
        if (!alive) return
        setError(isApiError(err) ? err.message : 'Chunk lookup failed')
      } finally {
        if (alive) setLoading(false)
      }
    }
    load()
    return () => {
      alive = false
    }
  }, [chunkId])

  return (
    <div className="drawer" role="dialog" aria-modal="true">
      <div className="drawer__content">
        <header className="drawer__header">
          <div>
            <div className="drawer__title">Chunk {chunkId}</div>
            <div className="muted">Source lookup</div>
          </div>
          <button type="button" className="icon-button" onClick={onClose}>
            Close
          </button>
        </header>

        {loading && <div className="empty-state">Loading chunk…</div>}
        {error && <div className="empty-state error">{error}</div>}
        {payload && !loading && !error && (
          <pre className="code-block">{JSON.stringify(payload, null, 2)}</pre>
        )}
      </div>
      <div className="drawer__backdrop" onClick={onClose} />
    </div>
  )
}
