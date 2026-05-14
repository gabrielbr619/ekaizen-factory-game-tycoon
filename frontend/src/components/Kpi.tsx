type KpiProps = {
  label: string
  value: string
  title?: string
  tone?: 'good' | 'bad' | 'neutral'
}

export function Kpi({ label, value, title, tone = 'neutral' }: KpiProps) {
  return (
    <div className={`kpi kpi-${tone}`} title={title ?? `${label}: ${value}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}
