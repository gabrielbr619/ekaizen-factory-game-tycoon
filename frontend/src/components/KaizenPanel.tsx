import { Sparkles } from 'lucide-react'
import { kaizenCost, kaizenLabel, kaizenTargetLabel } from '../lib/gameLabels'
import { kaizenTypes, type Card, type Developer, type GameState, type KaizenType } from '../types'
import { PanelTitle } from './PanelTitle'
import { Tooltip } from './ui/Tooltip'

type KaizenPanelProps = {
  game: GameState
  selectedDev: Developer | null
  selectedCard: Card | null
  onApply(kaizen: KaizenType): void
}

export function KaizenPanel({ game, selectedDev, selectedCard, onApply }: KaizenPanelProps) {
  return (
    <section className="panel kaizen-panel" aria-label="PDCA e Kaizens">
      <PanelTitle icon={<Sparkles aria-hidden="true" />} title="PDCA / Kaizens" />
      <p>Plan: escolha. Do: aplique. Check: veja metricas. Act: ajuste a proxima sprint.</p>
      <div className="kaizen-grid">
        {kaizenTypes.map((kaizen) => {
          const cost = kaizenCost(kaizen)
          const disabled = game.kaizen_points < cost
          const detailId = `kaizen-detail-${kaizen}`
          return (
            <button
              aria-label={kaizenLabel(kaizen)}
              aria-describedby={detailId}
              className={`${game.active_kaizens.includes(kaizen) ? 'active ' : ''}tooltip-host`}
              disabled={disabled}
              key={kaizen}
              onClick={() => onApply(kaizen)}
              type="button"
            >
              <span>{kaizenLabel(kaizen)}</span>
              <small>{cost} pt</small>
              <Tooltip id={detailId} text={`${kaizenLabel(kaizen)} custa ${cost} ponto(s). Alvo atual: ${kaizenTargetLabel(kaizen, selectedDev, selectedCard)}.`} />
            </button>
          )
        })}
      </div>
    </section>
  )
}
