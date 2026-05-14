type KpiProps = {
  label: string
  value: string
  title?: string
  tone?: 'good' | 'bad' | 'neutral'
}

export function Kpi({ label, value, title, tone = 'neutral' }: KpiProps) {
  const accessibleLabel = title === undefined ? `${label}: ${value}` : `${label}: ${value}. ${title}`

  return (
    <div aria-label={accessibleLabel} className={`kpi kpi-${tone}`} role="group" title={title ?? `${label}: ${value}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}
