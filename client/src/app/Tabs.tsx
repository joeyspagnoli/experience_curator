import type { ReactNode } from 'react'

// Header tab strip shared across the workspace layout.
export type TabKey = 'ask' | 'resume' | 'interview'

type TabConfig = {
  key: TabKey
  label: string
  subtitle?: string
  icon?: ReactNode
}

const TABS: TabConfig[] = [
  { key: 'ask', label: 'Ask', subtitle: 'Grounded Q&A' },
  { key: 'resume', label: 'Resume Tailor', subtitle: 'Bullet upgrades' },
  { key: 'interview', label: 'Interview Prep', subtitle: 'Practice mode' },
]

export function Tabs({ active, onChange }: { active: TabKey; onChange: (tab: TabKey) => void }) {
  return (
    <div className="tabs" role="tablist" aria-label="Workspace tabs">
      {TABS.map((tab) => (
        <button
          key={tab.key}
          type="button"
          className={`tab ${active === tab.key ? 'tab--active' : ''}`}
          onClick={() => onChange(tab.key)}
          role="tab"
          aria-selected={active === tab.key}
        >
          <span className="tab__label">{tab.label}</span>
          <span className="tab__subtitle">{tab.subtitle}</span>
        </button>
      ))}
    </div>
  )
}
