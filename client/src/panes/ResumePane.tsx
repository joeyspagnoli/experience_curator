import { useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchJson, isApiError } from '../lib/api'
import type { ResumeTailorResponse } from '../lib/types'

// Resume Tailor pane: paste a job description, get cited bullet suggestions.
export function ResumePane() {
  const [jobDescription, setJobDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ResumeTailorResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [traceId, setTraceId] = useState<string | null>(null)

  const handleSubmit = async () => {
    const trimmed = jobDescription.trim()
    if (!trimmed || loading) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const { data, traceId: headerTraceId } = await fetchJson<ResumeTailorResponse>(
        '/resume-tailor',
        {
          method: 'POST',
          body: { job_description: trimmed },
        },
      )
      setResult(data)
      setTraceId(data.trace_id ?? headerTraceId ?? null)
    } catch (err) {
      setTraceId(isApiError(err) ? err.traceId ?? null : null)
      setError(isApiError(err) ? err.message : 'Failed to tailor resume bullets')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="pane-content">
      <header className="pane-header">
        <div>
          <h2>Resume Tailor</h2>
          <p>Paste a job description to get evidence-backed bullet suggestions.</p>
        </div>
      </header>

      <div className="pane-scroll">
        <div className="card form-stack">
          <label className="field">
            <span>Job description</span>
            <textarea
              rows={8}
              placeholder="Paste a job description or role focus..."
              value={jobDescription}
              onChange={(event) => setJobDescription(event.target.value)}
              disabled={loading}
            />
          </label>

          <button
            type="button"
            className="button"
            onClick={handleSubmit}
            disabled={loading || !jobDescription.trim()}
          >
            {loading ? 'Tailoring…' : 'Suggest bullets'}
          </button>
        </div>

        {error && <div className="empty-state error">{error}</div>}

        {result && !error && (
          <>
            {result.no_evidence ? (
              <div className="empty-state">
                {result.message ?? 'No evidence found for this job description yet.'}
              </div>
            ) : (
              result.suggestions.map((suggestion, index) => (
                <article key={`${suggestion.bullet}-${index}`} className="card answer-card">
                  <div className="answer-card__answer">{suggestion.bullet}</div>
                  <div className="muted">{suggestion.rationale}</div>
                  <div className="citations">
                    <div className="section-title">Citations</div>
                    <ul>
                      {suggestion.citations.map((citation) => (
                        <li key={citation.chunk_id}>
                          <span className="mono">{citation.chunk_id.slice(0, 8)}</span> —{' '}
                          {citation.snippet}
                        </li>
                      ))}
                    </ul>
                  </div>
                </article>
              ))
            )}
          </>
        )}

        {traceId && (
          <div className="answer-card__meta">
            <span className="muted">Trace:</span>
            <span className="mono">{traceId}</span>
            <Link className="link" to={`/debug/${traceId}`}>
              View trace
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
