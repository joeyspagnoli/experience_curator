// Small UI helpers that keep views clean.
export const formatDate = (value?: string) => {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export const clampText = (value: string, max = 180) =>
  value.length > max ? `${value.slice(0, max)}…` : value

export const uniqueId = () =>
  // crypto.randomUUID is available in modern browsers; fallback keeps keys stable enough for UI.
  (crypto?.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`)
