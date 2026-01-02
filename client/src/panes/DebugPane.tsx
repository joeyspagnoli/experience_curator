import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchJson, isApiError } from '../lib/api'
import type { ApiList, Artifact, DebugRun, Folder } from '../lib/types'
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
  const [folderMap, setFolderMap] = useState<Record<string, string>>({})
  const [artifactMap, setArtifactMap] = useState<Record<string, string[]>>({})
  const [indexLoading, setIndexLoading] = useState(false)

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

  useEffect(() => {
    let alive = true
    const loadIndex = async () => {
      if (!traceId) return
      setIndexLoading(true)
      try {
        const { data } = await fetchJson<ApiList<Folder>>('/folders')
        if (!alive) return
        const folders = data.items ?? []
        const nextFolderMap: Record<string, string> = {}
        folders.forEach((folder) => {
          nextFolderMap[folder.id] = folder.name
        })
        setFolderMap(nextFolderMap)

        const artifactEntries = await Promise.all(
          folders.map(async (folder) => {
            try {
              const { data: artifactData } = await fetchJson<ApiList<Artifact>>(
                `/folders/${folder.id}/artifacts`,
              )
              return (artifactData.items ?? []).map((artifact) => ({
                filename: artifact.filename,
                folderName: folder.name,
              }))
            } catch {
              return []
            }
          }),
        )

        if (!alive) return
        const nextArtifactMap: Record<string, string[]> = {}
        artifactEntries.flat().forEach((entry) => {
          if (!nextArtifactMap[entry.filename]) {
            nextArtifactMap[entry.filename] = [entry.folderName]
          } else if (!nextArtifactMap[entry.filename].includes(entry.folderName)) {
            nextArtifactMap[entry.filename].push(entry.folderName)
          }
        })
        setArtifactMap(nextArtifactMap)
      } finally {
        if (alive) setIndexLoading(false)
      }
    }

    loadIndex()
    return () => {
      alive = false
    }
  }, [traceId])

  const scopeLabel = useMemo(() => {
    if (!run?.scope_folder_ids || run.scope_folder_ids.length === 0) {
      return 'All folders'
    }
    return run.scope_folder_ids
      .map((folderId) => folderMap[folderId] ?? folderId)
      .join(', ')
  }, [run, folderMap])

  const verification = run?.verification
  const verificationStatus = verification?.status ?? 'unknown'
  const evidenceLabel = (filename?: string, fallback?: string) => {
    const resolved = filename ?? fallback ?? '—'
    const folderNames = filename ? artifactMap[filename] : undefined
    if (!folderNames || folderNames.length === 0) return resolved
    const suffix = folderNames.length > 1 ? ` +${folderNames.length - 1}` : ''
    return `${folderNames[0]}${suffix}/${resolved}`
  }

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

      <div className="pane-scroll">
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
                  <div className="table-row table-row--header">
                    <div className="muted">Chunk</div>
                    <div className="muted">Score</div>
                    <div className="muted">Path</div>
                    <div className="muted">Snippet</div>
                    <div className="muted">Open</div>
                  </div>
                  {run.retrieved.map((chunk) => (
                    <div key={chunk.chunk_id} className="table-row">
                      <div className="mono">{chunk.chunk_id.slice(0, 8)}</div>
                      <div>{chunk.score.toFixed(3)}</div>
                      <div
                        className="path-label"
                        title={chunk.artifact_filename ?? chunk.artifact_path ?? '—'}
                      >
                        {evidenceLabel(chunk.artifact_filename, chunk.artifact_path)}
                      </div>
                      <div className="muted">{clampText(chunk.snippet ?? '', 120)}</div>
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
                <div className="empty-state">
                  No retrieved chunks yet. Upload more artifacts or widen the scope.
                </div>
              )}
              {indexLoading && <div className="muted">Indexing folders…</div>}
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
      </div>

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
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    document.body.classList.add('modal-open')
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.classList.remove('modal-open')
    }
  }, [onClose])

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
          <button type="button" className="button button--ghost button--compact" onClick={onClose}>
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
