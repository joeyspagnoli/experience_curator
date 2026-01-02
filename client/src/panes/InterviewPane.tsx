// Placeholder pane for the Interview Prep workflow.
export function InterviewPane() {
  return (
    <div className="pane-content">
      <header className="pane-header">
        <div>
          <h2>Interview Prep</h2>
          <p>Draft structured answers grounded in your evidence. Coming soon.</p>
        </div>
      </header>

      <div className="pane-scroll">
        <div className="card form-stack">
          <div className="field">
            <span>Question bank</span>
            <div className="list">
              <div className="list-item muted">Tell me about a project you’re proud of.</div>
              <div className="list-item muted">Describe a challenge you overcame.</div>
              <div className="list-item muted">How do you measure impact?</div>
            </div>
          </div>

          <label className="field">
            <span>Answer editor</span>
            <textarea rows={6} placeholder="Draft an evidence-backed answer..." disabled />
          </label>

          <button type="button" className="button button--ghost" disabled>
            Generate (coming soon)
          </button>
        </div>
      </div>
    </div>
  )
}
