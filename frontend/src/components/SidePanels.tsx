import { Activity, CheckCircle2, Gauge, History } from 'lucide-react'
import { currencyFormatter, percentFormatter } from '../lib/formatters'
import { type GameState, type SprintMetrics } from '../types'
import { PanelTitle } from './PanelTitle'
import { AccessibleDetail } from './ui/AccessibleDetail'

type MetricsPanelProps = {
  metrics: SprintMetrics | undefined
  game: GameState
}

export function MetricsPanel({ metrics, game }: MetricsPanelProps) {
  return (
    <section className="panel metrics-panel" aria-label="Metricas">
      <PanelTitle icon={<Gauge aria-hidden="true" />} title="Metricas Lean" />
      <div className="metric-grid">
        <Metric label="OEE" value={percentFormatter.format(metrics?.oee ?? 0)} title="Qualidade operacional geral: disponibilidade, performance e qualidade. Quanto maior, melhor o veredito." />
        <Metric label="Lead Time" value={`${metrics?.lead_time_avg ?? 0} sp`} title="Tempo medio ate entregar valor. Quanto menor, maior sua chance de cumprir prazos." />
        <Metric label="Cycle Analise" value={`${metrics?.cycle_time_by_column.analysis ?? 0} sp`} title="Tempo medio por coluna recebido do backend para identificar gargalos." />
        <Metric label="Cycle Dev" value={`${metrics?.cycle_time_by_column.development ?? 0} sp`} title="Tempo medio por coluna recebido do backend para identificar gargalos." />
        <Metric label="Cycle QA" value={`${metrics?.cycle_time_by_column.qa ?? 0} sp`} title="Tempo medio por coluna recebido do backend para identificar gargalos." />
        <Metric label="Throughput" value={currencyFormatter.format(metrics?.throughput_value ?? 0)} title="Valor entregue na ultima sprint. E o motor de caixa e lucro." />
        <Metric label="Heijunka" value={currencyFormatter.format(metrics?.heijunka_bonus ?? 0)} title="Bonus por ritmo constante de entregas." />
        <Metric label="Bugs prod." value={`${metrics?.bugs_in_production ?? 0}`} title="Bugs que escaparam para producao. Derrubam qualidade, reputacao e previsibilidade." />
        <Metric label="Custo fixo" value={currencyFormatter.format(game.fixed_cost)} title="Custo debitado ao processar a sprint. Precisa caber no Budget." />
      </div>
    </section>
  )
}

type MetricProps = {
  label: string
  value: string
  title: string
}

function Metric({ label, value, title }: MetricProps) {
  const detailId = `metric-detail-${label.toLowerCase().replace(/\W+/g, '-')}`

  return (
    <div aria-describedby={detailId} aria-label={`${label}: ${value}`} className="metric detail-host" role="group" tabIndex={0}>
      <span>{label}</span>
      <strong>{value}</strong>
      <AccessibleDetail id={detailId} text={title} />
    </div>
  )
}

type ClientsPanelProps = {
  game: GameState
}

export function ClientsPanel({ game }: ClientsPanelProps) {
  return (
    <section className="panel" aria-label="Clientes">
      <PanelTitle icon={<CheckCircle2 aria-hidden="true" />} title="Clientes" />
      <div className="client-list">
        {game.clients.map((client) => (
          <div className={client.active ? '' : 'inactive'} key={client.id} title="Reputacao individual do cliente recebida do servidor.">
            <span>{client.name}</span>
            <strong>{client.reputation}%</strong>
          </div>
        ))}
      </div>
    </section>
  )
}

type EventsPanelProps = {
  events: string[]
  timeline: GameState['timeline']
}

export function EventsPanel({ events, timeline }: EventsPanelProps) {
  const appliedEvents = timeline.slice(-2).reverse()

  return (
    <section className="panel" aria-label="Eventos">
      <PanelTitle icon={<Activity aria-hidden="true" />} title="Eventos" />
      <div className="event-groups">
        <div>
          <h3>Aguardando decisao</h3>
          <ul className="event-list event-list-pending">
            {events.length === 0 ? (
              <li>Nenhuma decisao pendente informada pelo servidor.</li>
            ) : (
              events.map((event) => <li key={event}>{event}</li>)
            )}
          </ul>
        </div>
        <div>
          <h3>Ja aplicado no estado</h3>
          <ul className="event-list event-list-applied">
            {appliedEvents.length === 0 ? (
              <li>Sem historico aplicado nesta partida.</li>
            ) : (
              appliedEvents.map((event) => (
                <li key={`${event.sprint}-${event.kind}-${event.message}`}>
                  S{event.sprint}: {event.message}
                </li>
              ))
            )}
          </ul>
        </div>
      </div>
    </section>
  )
}

type HistoryPanelProps = {
  timeline: GameState['timeline']
}

export function HistoryPanel({ timeline }: HistoryPanelProps) {
  return (
    <section className="panel history-panel" aria-label="Historico">
      <PanelTitle icon={<History aria-hidden="true" />} title="Historico" />
      <ol>
        {timeline.map((event) => (
          <li key={`${event.sprint}-${event.kind}-${event.message}`}>
            <span>S{event.sprint}</span>
            <p>{event.message}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}
