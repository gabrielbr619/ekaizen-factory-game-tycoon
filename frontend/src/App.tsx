import { useEffect, useMemo, useState, type ReactNode } from 'react'
import {
  Activity,
  AlertTriangle,
  Award,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronRight,
  Gauge,
  History,
  KanbanSquare,
  Play,
  RotateCcw,
  Sparkles,
  Users,
} from 'lucide-react'
import {
  columns,
  kaizenTypes,
  type Candidate,
  type Card,
  type Column,
  type CommandPayload,
  type Developer,
  type GameApi,
  type GameState,
  type HallOfKaizen,
  type KaizenType,
  type SprintMetrics,
} from './types'

type AppProps = {
  api: GameApi
}

type ViewMode = 'ops' | 'hall'

const currencyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 0,
})

const percentFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'percent',
  maximumFractionDigits: 0,
})

export function App({ api }: AppProps) {
  const [game, setGame] = useState<GameState | null>(null)
  const [hall, setHall] = useState<HallOfKaizen | null>(null)
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null)
  const [selectedDevId, setSelectedDevId] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('ops')
  const [notice, setNotice] = useState('Inicializando sala de controle...')
  const [busy, setBusy] = useState(false)
  const [confirmSprint, setConfirmSprint] = useState(false)

  useEffect(() => {
    let mounted = true
    setBusy(true)
    api
      .startGame()
      .then((state) => {
        if (mounted) {
          setGame(state)
          setSelectedCardId(state.cards.find((card) => card.column !== 'done')?.id ?? null)
          setSelectedDevId(state.developers.find((dev) => dev.active)?.id ?? null)
          setNotice(
            state.id.startsWith('mock-')
              ? 'Mock temporario ativo: backend indisponivel; a UI esta pronta para trocar pela API real.'
              : 'Partida carregada. O backend e a fonte autoritativa; a UI envia comandos.',
          )
        }
      })
      .catch((error: Error) => {
        if (mounted) setNotice(error.message)
      })
      .finally(() => {
        if (mounted) setBusy(false)
      })
    return () => {
      mounted = false
    }
  }, [api])

  const selectedCard = useMemo(
    () => game?.cards.find((card) => card.id === selectedCardId) ?? null,
    [game, selectedCardId],
  )
  const selectedDev = useMemo(
    () => game?.developers.find((dev) => dev.id === selectedDevId) ?? null,
    [game, selectedDevId],
  )

  async function startFreshGame() {
    setBusy(true)
    setHall(null)
    setViewMode('ops')
    try {
      const state = await api.startGame()
      setGame(state)
      setSelectedCardId(state.cards.find((card) => card.column !== 'done')?.id ?? null)
      setSelectedDevId(state.developers.find((dev) => dev.active)?.id ?? null)
      setNotice('Nova partida iniciada.')
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Falha ao iniciar partida.')
    } finally {
      setBusy(false)
    }
  }

  async function sendCommand(payload: CommandPayload, success: string) {
    if (game === null) return
    setBusy(true)
    try {
      const state = await api.sendCommand(game.id, payload)
      setGame(state)
      setNotice(success)
      if (state.verdict !== 'playing') {
        await loadHall(state)
      }
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Comando recusado pelo servidor.')
    } finally {
      setBusy(false)
      setConfirmSprint(false)
    }
  }

  async function loadHall(state = game) {
    if (state === null) return
    setBusy(true)
    try {
      const result = await api.loadHallOfKaizen(state.id)
      setHall(result)
      setViewMode('hall')
      setNotice('Hall of Kaizen carregado.')
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Falha ao carregar Hall of Kaizen.')
    } finally {
      setBusy(false)
    }
  }

  if (game === null) {
    return (
      <main className="loading-screen">
        <Activity aria-hidden="true" />
        <p>{notice}</p>
      </main>
    )
  }

  const lastMetrics = game.metrics_history.at(-1)
  const activeClients = game.clients.filter((client) => client.active)
  const clientReputation =
    activeClients.length === 0
      ? 0
      : Math.round(activeClients.reduce((total, client) => total + client.reputation, 0) / activeClients.length)

  return (
    <main className="factory-app">
      <TopBar game={game} clientReputation={clientReputation} busy={busy} onRestart={startFreshGame} />

      <section className="andon-strip" aria-label="Andon">
        <div className="andon-title">
          <AlertTriangle aria-hidden="true" />
          <span>Andon</span>
        </div>
        <div className="andon-alerts">
          {game.andon_alerts.length === 0 ? (
            <span className="andon-empty">Linha estavel, sem alertas ativos.</span>
          ) : (
            game.andon_alerts.map((alert) => (
              <span
                className={`andon-alert andon-${alert.severity}`}
                key={`${alert.code}-${alert.message}`}
                title="Andon mostra situacoes que precisam de decisao antes que virem perda."
              >
                {alert.message}
              </span>
            ))
          )}
        </div>
      </section>

      <nav className="view-tabs" aria-label="Telas">
        <button className={viewMode === 'ops' ? 'active' : ''} onClick={() => setViewMode('ops')} type="button">
          <KanbanSquare aria-hidden="true" />
          Jogo
        </button>
        <button className={viewMode === 'hall' ? 'active' : ''} onClick={() => loadHall()} type="button">
          <Award aria-hidden="true" />
          Hall of Kaizen
        </button>
      </nav>

      {viewMode === 'ops' ? (
        <div className="ops-grid">
          <section className="left-rail">
            <MetricsPanel metrics={lastMetrics} game={game} />
            <ClientsPanel game={game} />
            <EventsPanel events={game.pending_events} />
          </section>

          <KanbanBoard
            game={game}
            selectedCardId={selectedCardId}
            onSelectCard={setSelectedCardId}
            onMoveCard={(card, target) =>
              sendCommand({ type: 'move-card', card_id: card.id, target }, `${card.title} enviado para ${columnLabel(target)}.`)
            }
          />

          <section className="right-rail">
            <DevelopersPanel
              developers={game.developers}
              selectedCard={selectedCard}
              selectedDevId={selectedDevId}
              onSelectDev={setSelectedDevId}
              onAllocate={(dev) =>
                sendCommand(
                  { type: 'allocate-dev', dev_id: dev.id, card_id: selectedCard?.id ?? null },
                  `${dev.name} alocado conforme comando do backend.`,
                )
              }
            />
            <HiringPanel game={game} onHire={(candidate) => sendCommand({ type: 'hire-candidate', candidate_id: candidate.id }, `${candidate.name} contratado.`)} />
            <KaizenPanel
              game={game}
              selectedDev={selectedDev}
              selectedCard={selectedCard}
              onApply={(kaizen) =>
                sendCommand(
                  { type: 'apply-kaizen', kaizen, target_id: kaizenTarget(kaizen, selectedDev, selectedCard) },
                  `PDCA aplicado: ${kaizenLabel(kaizen)}.`,
                )
              }
            />
          </section>
        </div>
      ) : (
        <HallPanel hall={hall} game={game} onRestart={startFreshGame} />
      )}

      <footer className="command-bar">
        <div>
          <strong>{notice}</strong>
          <span>Comandos usam `POST /games/{'{game_id}'}/commands` com idempotencia.</span>
        </div>
        {confirmSprint ? (
          <div className="confirm-actions">
            <span>Encerrar a sprint processa custos, progresso, bugs e eventos no backend.</span>
            <button disabled={busy} onClick={() => sendCommand({ type: 'process-sprint' }, 'Sprint processada.')} type="button">
              Confirmar sprint
            </button>
            <button disabled={busy} onClick={() => setConfirmSprint(false)} type="button">
              Cancelar
            </button>
          </div>
        ) : (
          <button className="primary-action" disabled={busy} onClick={() => setConfirmSprint(true)} type="button">
            <Play aria-hidden="true" />
            Encerrar sprint
          </button>
        )}
      </footer>
    </main>
  )
}

type TopBarProps = {
  game: GameState
  clientReputation: number
  busy: boolean
  onRestart(): void
}

function TopBar({ game, clientReputation, busy, onRestart }: TopBarProps) {
  return (
    <header className="top-bar">
      <div className="brand-block">
        <span className="brand-mark">eK</span>
        <div>
          <h1>eKaizen Factory Game Tycoon</h1>
          <p>Fase {game.phase} · sprint {game.sprint}/35</p>
        </div>
      </div>
      <div className="kpi-strip" aria-label="Estado geral">
        <Kpi label="Budget" value={currencyFormatter.format(game.budget)} tone={game.budget < 0 ? 'bad' : 'good'} />
        <Kpi label="Lucro acum." value={currencyFormatter.format(game.accumulated_profit)} />
        <Kpi label="Reputacao" value={`${clientReputation}%`} tone={clientReputation < 40 ? 'bad' : 'good'} />
        <Kpi label="Devs ativos" value={`${game.developers.filter((dev) => dev.active).length}`} />
        <Kpi label="Kaizen" value={`${game.kaizen_points} pts`} tone={game.kaizen_points > 0 ? 'good' : 'neutral'} />
      </div>
      <button className="icon-button" disabled={busy} onClick={onRestart} title="Iniciar nova partida" type="button">
        <RotateCcw aria-hidden="true" />
        Nova
      </button>
    </header>
  )
}

type KpiProps = {
  label: string
  value: string
  tone?: 'good' | 'bad' | 'neutral'
}

function Kpi({ label, value, tone = 'neutral' }: KpiProps) {
  return (
    <div className={`kpi kpi-${tone}`} title={`${label}: ${value}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

type MetricsPanelProps = {
  metrics: SprintMetrics | undefined
  game: GameState
}

function MetricsPanel({ metrics, game }: MetricsPanelProps) {
  return (
    <section className="panel metrics-panel" aria-label="Metricas">
      <PanelTitle icon={<Gauge aria-hidden="true" />} title="Metricas Lean" />
      <div className="metric-grid">
        <Metric label="OEE" value={percentFormatter.format(metrics?.oee ?? 0)} title="OEE vem do backend: disponibilidade x performance x qualidade." />
        <Metric label="Lead Time" value={`${metrics?.lead_time_avg ?? 0} sp`} title="Lead Time medio recebido do backend." />
        <Metric label="Throughput" value={currencyFormatter.format(metrics?.throughput_value ?? 0)} title="Valor entregue na ultima sprint." />
        <Metric label="Heijunka" value={currencyFormatter.format(metrics?.heijunka_bonus ?? 0)} title="Bonus por ritmo constante de entregas." />
        <Metric label="Bugs prod." value={`${metrics?.bugs_in_production ?? 0}`} title="Bugs que escaparam para producao na ultima sprint." />
        <Metric label="Custo fixo" value={currencyFormatter.format(game.fixed_cost)} title="Debitado pelo backend ao processar a sprint." />
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
  return (
    <div className="metric" title={title}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

type KanbanProps = {
  game: GameState
  selectedCardId: string | null
  onSelectCard(cardId: string): void
  onMoveCard(card: Card, target: Column): void
}

function KanbanBoard({ game, selectedCardId, onSelectCard, onMoveCard }: KanbanProps) {
  return (
    <section className="kanban-area" aria-label="Kanban">
      <div className="section-heading">
        <PanelTitle icon={<KanbanSquare aria-hidden="true" />} title="Kanban operacional" />
        <span>Fluxo sequencial: Backlog → Analise → Dev → QA → Done</span>
      </div>
      <div className="kanban-columns">
        {columns.map((column) => {
          const cards = game.cards.filter((card) => card.column === column)
          const limit = game.wip_limits[column] ?? 0
          return (
            <section className="kanban-column" key={column} aria-label={columnLabel(column)}>
              <header>
                <div>
                  <strong>{columnLabel(column)}</strong>
                  <span title="WIP recebido do backend. O servidor bloqueia estouro real.">
                    WIP {cards.length}/{limit >= 900 ? '∞' : limit}
                  </span>
                </div>
                <small>{columnHelp(column)}</small>
              </header>
              <div className="card-stack">
                {cards.map((card) => (
                  <WorkCard
                    card={card}
                    game={game}
                    key={card.id}
                    selected={card.id === selectedCardId}
                    onSelect={() => onSelectCard(card.id)}
                    onMove={() => {
                      const target = nextColumn(card.column)
                      if (target !== null) onMoveCard(card, target)
                    }}
                  />
                ))}
              </div>
            </section>
          )
        })}
      </div>
    </section>
  )
}

type WorkCardProps = {
  card: Card
  game: GameState
  selected: boolean
  onSelect(): void
  onMove(): void
}

function WorkCard({ card, game, selected, onSelect, onMove }: WorkCardProps) {
  const client = game.clients.find((item) => item.id === card.client_id)
  const assigned = card.assigned_dev_ids
    .map((id) => game.developers.find((dev) => dev.id === id)?.name)
    .filter((name) => name !== undefined)
  const progress = `${card.progress}/${card.points_total}`
  const canMove = nextColumn(card.column) !== null
  return (
    <article className={`work-card ${selected ? 'selected' : ''} ${card.blocked_by_jidoka ? 'jidoka' : ''}`}>
      <button
        className="card-select"
        onClick={onSelect}
        title={`Card ${card.title}. Requisitos: ${card.required_specialties.join(', ')}. Valor ${currencyFormatter.format(card.value)}. Prazo sprint ${card.deadline_sprint}. Progresso ${progress}.`}
        type="button"
      >
        <span className="card-type">{card.card_type}</span>
        <strong>{card.title}</strong>
        <span>{client?.name ?? 'Cliente'} · {card.size} · prazo S{card.deadline_sprint}</span>
      </button>
      <div className="progress-track" title={`Progresso recebido: ${progress}`}>
        <span style={{ width: `${Math.min(100, Math.round((card.progress / card.points_total) * 100))}%` }} />
      </div>
      <div className="card-meta">
        <span>{currencyFormatter.format(card.value)}</span>
        <span>Cycle {cycleSummary(card)}</span>
      </div>
      <div className="assigned-list">
        {assigned.length === 0 ? <span>Sem dev</span> : assigned.map((name) => <span key={name}>{name}</span>)}
      </div>
      <button className="move-button" disabled={!canMove} onClick={onMove} type="button">
        Mover
        <ChevronRight aria-hidden="true" />
      </button>
    </article>
  )
}

type DevelopersPanelProps = {
  developers: Developer[]
  selectedCard: Card | null
  selectedDevId: string | null
  onSelectDev(devId: string): void
  onAllocate(dev: Developer): void
}

function DevelopersPanel({ developers, selectedCard, selectedDevId, onSelectDev, onAllocate }: DevelopersPanelProps) {
  return (
    <section className="panel" aria-label="Devs">
      <PanelTitle icon={<Users aria-hidden="true" />} title="Gemba dos devs" />
      <div className="dev-list">
        {developers.map((dev) => (
          <article className={`dev-row ${selectedDevId === dev.id ? 'selected' : ''}`} key={dev.id}>
            <button
              onClick={() => onSelectDev(dev.id)}
              title={`${dev.name}. ${dev.specialty}, ${dev.level}. Moral ${dev.moral}. Salario ${currencyFormatter.format(dev.salary)}. Entregas ${dev.cards_delivered}. Bugs ${dev.bugs_generated}. Tempo de casa ${dev.tenure_sprints} sprints.`}
              type="button"
            >
              <span className={`avatar spec-${dev.specialty}`}>{dev.avatar}</span>
              <span>
                <strong>{dev.name}</strong>
                <small>{dev.specialty} · {dev.level}</small>
              </span>
              <span className={`morale ${dev.moral < 30 ? 'low' : ''}`}>{dev.moral}</span>
            </button>
            <button
              className="tiny-action"
              disabled={selectedCard === null || selectedCard.column === 'backlog' || selectedCard.column === 'done' || !dev.active}
              onClick={() => onAllocate(dev)}
              type="button"
            >
              Alocar
            </button>
          </article>
        ))}
      </div>
    </section>
  )
}

type HiringPanelProps = {
  game: GameState
  onHire(candidate: Candidate): void
}

function HiringPanel({ game, onHire }: HiringPanelProps) {
  return (
    <section className="panel hiring-panel" aria-label="Contratacoes">
      <PanelTitle icon={<BriefcaseBusiness aria-hidden="true" />} title="Contratacao" />
      <div className="candidate-list">
        {game.candidates.slice(0, 3).map((candidate) => (
          <article key={candidate.id}>
            <div>
              <strong>{candidate.name}</strong>
              <span>{candidate.specialty} · {candidate.level}</span>
            </div>
            <button
              onClick={() => onHire(candidate)}
              title={`Contratar ${candidate.name}. Custo de admissao: ${currencyFormatter.format(candidate.salary)}. Onboarding e processado no backend.`}
              type="button"
            >
              {currencyFormatter.format(candidate.salary)}
            </button>
          </article>
        ))}
      </div>
    </section>
  )
}

type KaizenPanelProps = {
  game: GameState
  selectedDev: Developer | null
  selectedCard: Card | null
  onApply(kaizen: KaizenType): void
}

function KaizenPanel({ game, selectedDev, selectedCard, onApply }: KaizenPanelProps) {
  return (
    <section className="panel kaizen-panel" aria-label="PDCA e Kaizens">
      <PanelTitle icon={<Sparkles aria-hidden="true" />} title="PDCA / Kaizens" />
      <p>Plan: escolha. Do: aplique. Check: veja metricas. Act: ajuste a proxima sprint.</p>
      <div className="kaizen-grid">
        {kaizenTypes.map((kaizen) => (
          <button
            className={game.active_kaizens.includes(kaizen) ? 'active' : ''}
            disabled={game.kaizen_points <= 0}
            key={kaizen}
            onClick={() => onApply(kaizen)}
            title={`Aplicar ${kaizenLabel(kaizen)}. Alvo atual: ${kaizenTargetLabel(kaizen, selectedDev, selectedCard)}.`}
            type="button"
          >
            {kaizenLabel(kaizen)}
          </button>
        ))}
      </div>
    </section>
  )
}

type ClientsPanelProps = {
  game: GameState
}

function ClientsPanel({ game }: ClientsPanelProps) {
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
}

function EventsPanel({ events }: EventsPanelProps) {
  return (
    <section className="panel" aria-label="Eventos">
      <PanelTitle icon={<Activity aria-hidden="true" />} title="Eventos" />
      <ul className="event-list">
        {events.length === 0 ? <li>Sem evento pendente.</li> : events.map((event) => <li key={event}>{event}</li>)}
      </ul>
    </section>
  )
}

type HallPanelProps = {
  hall: HallOfKaizen | null
  game: GameState
  onRestart(): void
}

function HallPanel({ hall, game, onRestart }: HallPanelProps) {
  const source = hall ?? {
    verdict: game.verdict,
    accumulated_profit: game.accumulated_profit,
    budget: game.budget,
    oee_avg: game.metrics_history.at(-1)?.oee ?? 0,
    lead_time_avg: game.metrics_history.at(-1)?.lead_time_avg ?? 0,
    throughput_avg: game.metrics_history.at(-1)?.delivered_cards ?? 0,
    top_kaizens: [],
    sprint_mvp: { sprint: 0, throughput_value: 0, oee: 0 },
    dev_mvp: game.developers[0]?.name ?? 'Sem MVP',
    badges: game.badges,
    timeline: game.timeline,
  }

  return (
    <section className="hall-panel" aria-label="Hall of Kaizen">
      <div className="hall-header">
        <div>
          <Award aria-hidden="true" />
          <h2>Hall of Kaizen</h2>
          <p>Veredito: {verdictLabel(source.verdict)}</p>
        </div>
        <button onClick={onRestart} type="button">
          <RotateCcw aria-hidden="true" />
          Jogar novamente
        </button>
      </div>
      <div className="hall-scoreboard">
        <Kpi label="Lucro final" value={currencyFormatter.format(source.accumulated_profit)} />
        <Kpi label="Budget" value={currencyFormatter.format(source.budget)} />
        <Kpi label="OEE medio" value={percentFormatter.format(source.oee_avg)} />
        <Kpi label="Lead Time" value={`${source.lead_time_avg} sp`} />
        <Kpi label="Throughput" value={`${source.throughput_avg}`} />
      </div>
      <div className="hall-grid">
        <section className="panel">
          <PanelTitle icon={<Sparkles aria-hidden="true" />} title="Top Kaizens" />
          {source.top_kaizens.length === 0 ? (
            <p>Nenhum Kaizen impactante registrado ainda.</p>
          ) : (
            source.top_kaizens.map((impact) => (
              <div className="impact-row" key={impact.kaizen}>
                <span>{impact.label}</span>
                <strong>
                  {percentFormatter.format(impact.before)} → {percentFormatter.format(impact.after)}
                </strong>
              </div>
            ))
          )}
        </section>
        <section className="panel">
          <PanelTitle icon={<Gauge aria-hidden="true" />} title="MVPs" />
          <div className="mvp-box">
            <span>Sprint MVP</span>
            <strong>S{source.sprint_mvp.sprint} · {currencyFormatter.format(source.sprint_mvp.throughput_value)}</strong>
          </div>
          <div className="mvp-box">
            <span>Dev MVP</span>
            <strong>{source.dev_mvp}</strong>
          </div>
        </section>
        <section className="panel">
          <PanelTitle icon={<Award aria-hidden="true" />} title="Badges" />
          <div className="badge-list">
            {source.badges.length === 0 ? <span>Sem badges ainda</span> : source.badges.map((badge) => <span key={badge}>{badge}</span>)}
          </div>
        </section>
        <HistoryPanel timeline={source.timeline} />
      </div>
    </section>
  )
}

type HistoryPanelProps = {
  timeline: GameState['timeline']
}

function HistoryPanel({ timeline }: HistoryPanelProps) {
  return (
    <section className="panel history-panel" aria-label="Historico">
      <PanelTitle icon={<History aria-hidden="true" />} title="Historico" />
      <ol>
        {timeline.slice(0, 8).map((event) => (
          <li key={`${event.sprint}-${event.kind}-${event.message}`}>
            <span>S{event.sprint}</span>
            <p>{event.message}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}

type PanelTitleProps = {
  icon: ReactNode
  title: string
}

function PanelTitle({ icon, title }: PanelTitleProps) {
  return (
    <h2 className="panel-title">
      {icon}
      {title}
    </h2>
  )
}

function nextColumn(column: Column): Column | null {
  if (column === 'backlog') return 'analysis'
  if (column === 'analysis') return 'development'
  if (column === 'development') return 'qa'
  if (column === 'qa') return 'done'
  return null
}

function columnLabel(column: Column): string {
  if (column === 'backlog') return 'Backlog'
  if (column === 'analysis') return 'Analise'
  if (column === 'development') return 'Dev'
  if (column === 'qa') return 'QA'
  return 'Done'
}

function columnHelp(column: Column): string {
  if (column === 'backlog') return 'Demanda aguardando pull'
  if (column === 'analysis') return 'PO destrava requisitos'
  if (column === 'development') return 'Execucao tecnica'
  if (column === 'qa') return 'Qualidade e Jidoka'
  return 'Receita entregue'
}

function cycleSummary(card: Card): string {
  const entries = Object.entries(card.cycle_times)
  if (entries.length === 0) return '0 sp'
  return entries.map(([column, value]) => `${column}:${value}`).join(' ')
}

function kaizenLabel(kaizen: KaizenType): string {
  if (kaizen === 'train-dev') return 'Treinar Dev'
  if (kaizen === 'poka-yoke') return 'Poka-Yoke'
  if (kaizen === 'qa-automation') return 'QA Auto'
  if (kaizen === 'rest-space') return 'Descanso'
  if (kaizen === 'wip-increase') return 'Aumentar WIP'
  if (kaizen === 'mentoring') return 'Mentoria'
  if (kaizen === 'interns') return 'Estagiarios'
  if (kaizen === 'marketing') return 'Marketing'
  if (kaizen === 'devops-culture') return 'Cultura DevOps'
  return 'Heijunka'
}

function kaizenTarget(kaizen: KaizenType, selectedDev: Developer | null, selectedCard: Card | null): string | null {
  if (kaizen === 'train-dev') return selectedDev?.id ?? null
  if (kaizen === 'wip-increase') return selectedCard?.column ?? 'development'
  return null
}

function kaizenTargetLabel(kaizen: KaizenType, selectedDev: Developer | null, selectedCard: Card | null): string {
  if (kaizen === 'train-dev') return selectedDev?.name ?? 'selecione um dev'
  if (kaizen === 'wip-increase') return selectedCard === null ? 'Desenvolvimento' : columnLabel(selectedCard.column)
  return 'global'
}

function verdictLabel(verdict: string): string {
  if (verdict === 'master-kaizen') return 'Mestre Kaizen'
  if (verdict === 'survived') return 'Sobreviveu'
  if (verdict === 'bankrupt') return 'Falencia'
  return 'Em andamento'
}
