import { BriefcaseBusiness } from 'lucide-react'
import { currencyFormatter } from '../lib/formatters'
import { levelLabel, specialtyLabel } from '../lib/gameLabels'
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
        {game.candidates.map((candidate) => (
          <article key={candidate.id}>
            <span className="candidate-avatar" aria-hidden="true">{candidate.avatar}</span>
            <div>
              <strong>{candidate.name}</strong>
              <span>
                {specialtyLabel(candidate.specialty)} · {levelLabel(candidate.level)} · bug {(candidate.bug_rate * 100).toFixed(1)}%
              </span>
              {candidate.expires_after_sprint === null ? null : (
                <small>Expira no sprint {candidate.expires_after_sprint}</small>
              )}
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
