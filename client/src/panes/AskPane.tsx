import { useEffect, useMemo, useState } from 'react'
import { fetchJson, isApiError } from '../lib/api'
import type { ApiList, AskResponse, EvidenceChunk, Folder } from '../lib/types'
import { uniqueId } from '../lib/utils'
import { Link } from 'react-router-dom'

const DEFAULT_TOP_K = 6

type AskTurn = {
  id: string
  question: string
  answer?: string
  citations?: EvidenceChunk[]
  traceId?: string
  noEvidence?: boolean
  warning?: string | null
  status: 'loading' | 'success' | 'error'
  error?: string
  errorPayload?: unknown
  citationsOn: boolean
}

type AskPaneProps = {
  onTraceCapture?: (traceId: string | null) => void
  activeTraceId: string | null
}

// Middle pane: ask grounded questions and see responses.
export function AskPane({ onTraceCapture, activeTraceId }: AskPaneProps) {
  const [folders, setFolders] = useState<Folder[]>([])
  const [scopeIds, setScopeIds] = useState<string[]>([])
  const [citationsMode, setCitationsMode] = useState<'on' | 'brainstorm'>('on')
  const [topK, setTopK] = useState(DEFAULT_TOP_K)
  const [question, setQuestion] = useState('')
  const [turns, setTurns] = useState<AskTurn[]>([])
  const [loadingFolders, setLoadingFolders] = useState(true)
  const [scopeOpen, setScopeOpen] = useState(false)

  useEffect(() => {
    let alive = true
    const loadFolders = async () => {
      setLoadingFolders(true)
      try {
        const { data } = await fetchJson<ApiList<Folder>>('/folders')
        if (!alive) return
        setFolders(data.items ?? [])
      } catch {
        if (!alive) return
        setFolders([])
      } finally {
        if (alive) setLoadingFolders(false)
      }
    }
    loadFolders()
    return () => {
      alive = false
    }
  }, [])

  const scopeLabel = useMemo(() => {
    if (scopeIds.length === 0) return 'All folders'
    const names = folders.filter((folder) => scopeIds.includes(folder.id)).map((f) => f.name)
    return names.length ? names.join(', ') : 'Selected folders'
  }, [folders, scopeIds])

  const toggleScope = (folderId: string) => {
    setScopeIds((prev) => {
      if (prev.includes(folderId)) {
        return prev.filter((id) => id !== folderId)
      }
      return [...prev, folderId]
    })
  }

  const handleSend = async () => {
    const trimmed = question.trim()
    if (!trimmed) return

    const turnId = uniqueId()
    const citationsOn = citationsMode === 'on'
    const nextTurn: AskTurn = {
      id: turnId,
      question: trimmed,
      status: 'loading',
      citationsOn,
    }
    setTurns((prev) => [nextTurn, ...prev])
    setQuestion('')

    try {
      const { data, traceId } = await fetchJson<AskResponse>('/ask', {
        method: 'POST',
        body: {
          question: trimmed,
          scope_folder_ids: scopeIds.length ? scopeIds : undefined,
          citations_mode: citationsMode,
          top_k: topK,
        },
      })

      const resolvedTrace = data.trace_id ?? traceId ?? null
      onTraceCapture?.(resolvedTrace)

      setTurns((prev) =>
        prev.map((turn) =>
              turn.id === turnId
            ? {
                ...turn,
                status: 'success',
                answer: data.answer_text,
                citations: data.citations ?? [],
                noEvidence: data.no_evidence ?? false,
                warning: data.warning ?? null,
                traceId: resolvedTrace ?? undefined,
              }
            : turn,
        ),
      )
    } catch (error) {
      const trace = isApiError(error) ? error.traceId ?? null : null
      onTraceCapture?.(trace)
      setTurns((prev) =>
        prev.map((turn) =>
          turn.id === turnId
            ? {
                ...turn,
                status: 'error',
                error:
                  isApiError(error) && error.status === 501
                    ? 'Ask is not implemented yet.'
                    : isApiError(error)
                      ? error.message
                      : 'Failed to send question',
                errorPayload: isApiError(error) ? error.data : undefined,
                traceId: trace ?? undefined,
              }
            : turn,
        ),
      )
    }
  }

  const sending = turns.some((turn) => turn.status === 'loading')

  return (
    <div className="pane-content">
      <header className="pane-header">
        <div>
          <h2>Ask</h2>
          <p>Get evidence-backed answers from your curated artifacts.</p>
        </div>
        {activeTraceId && (
          <div className="pill">Active trace: {activeTraceId.slice(0, 8)}…</div>
        )}
      </header>

      <div className="controls-row">
        <div className="control">
          <span className="control__label">Scope</span>
          <div className="dropdown">
            <button
              type="button"
              className="dropdown__trigger"
              onClick={() => setScopeOpen((prev) => !prev)}
            >
              {loadingFolders ? 'Loading…' : scopeLabel}
              <span className="caret">▾</span>
            </button>
            {scopeOpen && (
              <div className="dropdown__menu">
                {folders.length === 0 ? (
                  <div className="empty-state">No folders yet.</div>
                ) : (
                  folders.map((folder) => (
                    <label key={folder.id} className="checkbox">
                      <input
                        type="checkbox"
                        checked={scopeIds.includes(folder.id)}
                        onChange={() => toggleScope(folder.id)}
                      />
                      <span>{folder.name}</span>
                    </label>
                  ))
                )}
              </div>
            )}
          </div>
        </div>

        <div className="control">
          <span className="control__label">Citations</span>
          <button
            type="button"
            className={`toggle ${citationsMode === 'on' ? 'toggle--on' : ''}`}
            onClick={() => setCitationsMode((prev) => (prev === 'on' ? 'brainstorm' : 'on'))}
          >
            {citationsMode === 'on' ? 'ON' : 'OFF'}
          </button>
        </div>

        <div className="control">
          <span className="control__label">Top K</span>
          <input
            type="number"
            min={1}
            max={20}
            value={topK}
            onChange={(event) => setTopK(Number(event.target.value || DEFAULT_TOP_K))}
          />
        </div>
      </div>

      <div className="thread">
        {turns.length === 0 ? (
          <div className="empty-state">Ask your first question to start a grounded thread.</div>
        ) : (
          turns.map((turn) => <AnswerCard key={turn.id} turn={turn} />)
        )}
      </div>

      <div className="composer">
        <textarea
          rows={3}
          placeholder="Ask a question about your artifacts..."
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          disabled={sending}
        />
        <button type="button" className="button" onClick={handleSend} disabled={sending}>
          {sending ? 'Sending…' : 'Send'}
        </button>
      </div>
    </div>
  )
}

function AnswerCard({ turn }: { turn: AskTurn }) {
  return (
    <article className="card answer-card">
      <div className="answer-card__question">
        <span className="pill">Question</span>
        <div>{turn.question}</div>
      </div>

      {turn.status === 'loading' && <div className="answer-card__loading">Thinking…</div>}

      {turn.status === 'error' && (
        <div className="answer-card__error">
          <strong>{turn.error}</strong>
          {turn.errorPayload && (
            <pre className="code-block">{JSON.stringify(turn.errorPayload, null, 2)}</pre>
          )}
        </div>
      )}

      {turn.status === 'success' && (
        <div className="answer-card__body">
          <div className="answer-card__answer">{turn.answer}</div>

          {turn.warning && <div className="pill">Note: {turn.warning}</div>}
          {turn.noEvidence && (
            <div className="empty-state">No evidence returned for this answer.</div>
          )}

          {turn.citationsOn && (
            <div className="citations">
              <div className="section-title">Citations</div>
              {turn.citations && turn.citations.length > 0 ? (
                <ul>
                  {turn.citations.map((citation) => (
                    <li key={citation.chunk_id}>
                      <span className="mono">{citation.chunk_id.slice(0, 8)}</span> —{' '}
                      {citation.snippet}
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="empty-state">No citations returned.</div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="answer-card__meta">
        {turn.traceId ? (
          <>
            <span className="muted">Trace:</span>
            <span className="mono">{turn.traceId}</span>
            <button
              type="button"
              className="link"
              onClick={() => navigator.clipboard.writeText(turn.traceId ?? '')}
            >
              Copy
            </button>
            <Link className="link" to={`/debug/${turn.traceId}`}>
              Open Debug
            </Link>
          </>
        ) : (
          <span className="muted">No trace yet</span>
        )}
      </div>
    </article>
  )
}
