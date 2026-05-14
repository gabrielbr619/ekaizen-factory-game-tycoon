import { Sparkles } from 'lucide-react'
import { kaizenCost, kaizenLabel, kaizenTargetLabel } from '../lib/gameLabels'
import { kaizenTypes, type Card, type Developer, type GameState, type KaizenType } from '../types'
import { PanelTitle } from './PanelTitle'

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
          return (
            <button
              className={game.active_kaizens.includes(kaizen) ? 'active' : ''}
              disabled={disabled}
              key={kaizen}
              onClick={() => onApply(kaizen)}
              title={`${kaizenLabel(kaizen)} custa ${cost} ponto(s). Alvo atual: ${kaizenTargetLabel(kaizen, selectedDev, selectedCard)}.`}
              type="button"
            >
              <span>{kaizenLabel(kaizen)}</span>
              <small>{cost} pt</small>
            </button>
          )
        })}
      </div>
    </section>
  )
}
