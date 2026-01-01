import { useParams } from 'react-router-dom'
import { DebugPane } from '../panes/DebugPane'

// Full-width debug page at /debug/:trace_id.
export function DebugPage() {
  const { traceId } = useParams()

  return (
    <div className="page">
      <DebugPane traceId={traceId ?? null} fullWidth />
    </div>
  )
}
