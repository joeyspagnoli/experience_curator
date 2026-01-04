import { useEffect, useState } from 'react'
import { Tabs, type TabKey } from './Tabs'
import { LibraryPane } from '../panes/LibraryPane'
import { AskPane } from '../panes/AskPane'
import { DebugPane } from '../panes/DebugPane'
import { ResumePane } from '../panes/ResumePane'
import { InterviewPane } from '../panes/InterviewPane'
import { fetchJson, isApiError } from '../lib/api'
import type { HealthResponse } from '../lib/types'

// Top-level 3-pane workspace shell for the /app route.
export function AppShell() {
  const [activeTab, setActiveTab] = useState<TabKey>('ask')
  const [activeTraceId, setActiveTraceId] = useState<string | null>(null)
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthStatus, setHealthStatus] = useState<'loading' | 'ok' | 'error'>('loading')
  const [healthError, setHealthError] = useState<string | null>(null)

  // One-time ping to show API availability and environment in the header.
  useEffect(() => {
    let alive = true
    const loadHealth = async () => {
      setHealthStatus('loading')
      setHealthError(null)
      try {
        const { data } = await fetchJson<HealthResponse>('/health')
        if (!alive) return
        setHealth(data)
        setHealthStatus('ok')
      } catch (error) {
        if (!alive) return
        setHealth(null)
        setHealthStatus('error')
        setHealthError(isApiError(error) ? error.message : 'API unavailable')
      }
    }

    loadHealth()
    return () => {
      alive = false
    }
  }, [])

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand__spark" />
          <div>
            <div className="brand__title">ExperienceCurator</div>
            <div className="brand__subtitle">Week 1 Demo Console</div>
          </div>
        </div>

        <Tabs active={activeTab} onChange={setActiveTab} />

        <div className="health" title={healthError ?? 'API status'}>
          <span className={`status-dot status-dot--${healthStatus}`} />
          <div className="health__label">
            <span>API</span>
            <span className="health__env">env: {health?.env ?? 'offline'}</span>
          </div>
        </div>
      </header>

      {/* Three-pane workspace: library (left), work area (middle), debug (right). */}
      <main className="app-body">
        <section className="pane pane--library">
          <LibraryPane onTraceCapture={setActiveTraceId} />
        </section>

        <section className="pane pane--workspace">
          {activeTab === 'ask' && (
            <AskPane
              onTraceCapture={setActiveTraceId}
              activeTraceId={activeTraceId}
            />
          )}
          {activeTab === 'resume' && <ResumePane />}
          {activeTab === 'interview' && <InterviewPane />}
        </section>

        <section className="pane pane--debug">
          <DebugPane traceId={activeTraceId} />
        </section>
      </main>
    </div>
  )
}
