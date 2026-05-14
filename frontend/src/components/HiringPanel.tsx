import { BriefcaseBusiness } from 'lucide-react'
import { currencyFormatter } from '../lib/formatters'
import { levelLabel, specialtyBadge, specialtyLabel } from '../lib/gameLabels'
import { type Candidate, type GameState } from '../types'
import { PanelTitle } from './PanelTitle'
import { Tooltip } from './ui/Tooltip'

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
            <span className="candidate-avatar" aria-hidden="true">{specialtyBadge(candidate.specialty)}</span>
            <div className="candidate-identity">
              <strong>{candidate.name}</strong>
              <span className="candidate-meta">
                <span>{specialtyLabel(candidate.specialty)}</span>
                <span>{levelLabel(candidate.level)}</span>
                <span>Risco bug {(candidate.bug_rate * 100).toFixed(1)}%</span>
              </span>
              {candidate.expires_after_sprint === null ? null : (
                <small>Expira no sprint {candidate.expires_after_sprint}</small>
              )}
            </div>
            <button
              aria-label={`Contratar ${candidate.name}`}
              aria-describedby={`candidate-hire-detail-${candidate.id}`}
              className="tooltip-host"
              onClick={() => onHire(candidate)}
              type="button"
            >
              {currencyFormatter.format(candidate.salary)}
              <Tooltip id={`candidate-hire-detail-${candidate.id}`} text={`Contratar ${candidate.name}. Custo de admissao: ${currencyFormatter.format(candidate.salary)}. Onboarding e processado no backend.`} />
            </button>
          </article>
        ))}
      </div>
    </section>
  )
}
