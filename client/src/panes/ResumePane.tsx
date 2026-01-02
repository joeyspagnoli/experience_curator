// Placeholder pane for the Resume Tailor workflow.
export function ResumePane() {
  return (
    <div className="pane-content">
      <header className="pane-header">
        <div>
          <h2>Resume Tailor</h2>
          <p>Evidence-first bullet refinement. Coming soon.</p>
        </div>
      </header>

      <div className="pane-scroll">
        <div className="card form-stack">
          <label className="field">
            <span>Source bullet (from your artifacts)</span>
            <textarea
              rows={6}
              placeholder="Paste a grounded bullet to refine..."
              disabled
            />
          </label>

          <label className="field">
            <span>Target role context</span>
            <textarea
              rows={6}
              placeholder="Paste a job description or role focus..."
              disabled
            />
          </label>

          <button type="button" className="button button--ghost" disabled>
            Coming soon
          </button>
        </div>
      </div>
    </div>
  )
}
