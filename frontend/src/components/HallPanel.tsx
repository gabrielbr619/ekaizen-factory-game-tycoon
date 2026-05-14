import { Award, Gauge, RotateCcw, Sparkles } from 'lucide-react'
import { currencyFormatter, percentFormatter } from '../lib/formatters'
import { verdictLabel } from '../lib/gameLabels'
import { type GameState, type HallOfKaizen } from '../types'
import { Kpi } from './Kpi'
import { PanelTitle } from './PanelTitle'
import { HistoryPanel } from './SidePanels'

type HallPanelProps = {
  hall: HallOfKaizen | null
  game: GameState
  onRestart(): void
}

export function HallPanel({ hall, game, onRestart }: HallPanelProps) {
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
          <p>
            {hall === null ? 'Placar parcial da partida atual' : `Veredito: ${verdictLabel(source.verdict)}`}
          </p>
        </div>
        <button onClick={onRestart} title="Iniciar uma nova partida" type="button">
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
