import { BriefcaseBusiness } from 'lucide-react'
import { currencyFormatter } from '../lib/formatters'
import { type Candidate, type GameState } from '../types'
import { PanelTitle } from './PanelTitle'

type HiringPanelProps = {
  game: GameState
  onHire(candidate: Candidate): void
}

export function HiringPanel({ game, onHire }: HiringPanelProps) {
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
