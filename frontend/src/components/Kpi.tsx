import { AccessibleDetail } from './ui/AccessibleDetail'

type KpiProps = {
  label: string
  value: string
  title?: string
  tone?: 'good' | 'bad' | 'neutral'
}

export function Kpi({ label, value, title, tone = 'neutral' }: KpiProps) {
  const detailId = `kpi-detail-${label.toLowerCase().replace(/\W+/g, '-')}`
  const detail = title ?? `${label}: ${value}`

  return (
    <div
      aria-describedby={detailId}
      aria-label={`${label}: ${value}`}
      className={`kpi kpi-${tone} detail-host`}
      role="group"
      tabIndex={0}
    >
      <span>{label}</span>
      <strong>{value}</strong>
      <AccessibleDetail id={detailId} text={detail} />
    </div>
  )
}
