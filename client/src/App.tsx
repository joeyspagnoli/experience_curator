import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './app/AppShell'
import { DebugPage } from './pages/DebugPage'

// Root router for the ExperienceCurator client.
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Default route redirects into the main app shell. */}
        <Route path="/" element={<Navigate to="/app" replace />} />
        {/* Main 3-pane workspace. */}
        <Route path="/app" element={<AppShell />} />
        {/* Dedicated debug page for a single trace id. */}
        <Route path="/debug/:traceId" element={<DebugPage />} />
        {/* Fallback: any unknown route returns to the app shell. */}
        <Route path="*" element={<Navigate to="/app" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
