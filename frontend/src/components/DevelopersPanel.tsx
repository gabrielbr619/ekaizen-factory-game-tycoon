import { Users } from 'lucide-react'
import { currencyFormatter } from '../lib/formatters'
import { allocationTitle, levelLabel, specialtyBadge, specialtyLabel } from '../lib/gameLabels'
import { type Card, type Developer } from '../types'
import { PanelTitle } from './PanelTitle'

type DevelopersPanelProps = {
  developers: Developer[]
  selectedCard: Card | null
  selectedDevId: string | null
  onSelectDev(devId: string): void
  onAllocate(dev: Developer, cardId: string | null): void
}

export function DevelopersPanel({ developers, selectedCard, selectedDevId, onSelectDev, onAllocate }: DevelopersPanelProps) {
  return (
    <section className="panel" aria-label="Devs">
      <PanelTitle icon={<Users aria-hidden="true" />} title="Gemba dos devs" />
      <div className="dev-list">
        {developers.map((dev) => {
          const assignedToSelectedCard = selectedCard?.assigned_dev_ids.includes(dev.id) ?? false
          const selectedCardAcceptsAllocation =
            selectedCard !== null && selectedCard.column !== 'backlog' && selectedCard.column !== 'done'
          const actionDisabled = !dev.active || (!assignedToSelectedCard && !selectedCardAcceptsAllocation)
          const actionLabel = assignedToSelectedCard ? 'Remover' : 'Alocar'
          const targetCardId = assignedToSelectedCard ? null : selectedCard?.id ?? null

          return (
            <article className={`dev-row ${selectedDevId === dev.id ? 'selected' : ''}`} key={dev.id}>
              <button
                className="dev-select"
                onClick={() => onSelectDev(dev.id)}
                title={`${dev.name}. ${specialtyLabel(dev.specialty)}, ${levelLabel(dev.level)}. Moral ${dev.moral}. Salario ${currencyFormatter.format(dev.salary)}. Entregas ${dev.cards_delivered}. Bugs ${dev.bugs_generated}. Tempo de casa ${dev.tenure_sprints} sprints.`}
                type="button"
              >
                <span className={`avatar spec-${dev.specialty}`}>{specialtyBadge(dev.specialty)}</span>
                <span className="dev-identity">
                  <strong>{dev.name}</strong>
                  <small>{levelLabel(dev.level)} · {specialtyLabel(dev.specialty)}</small>
                </span>
                <span className={`morale ${dev.moral < 30 ? 'low' : ''}`} title={`Moral ${dev.moral}`}>
                  {dev.moral}
                </span>
              </button>
              <button
                aria-label={`${actionLabel} ${dev.name}`}
                className={`tiny-action ${assignedToSelectedCard ? 'remove-action' : ''}`}
                disabled={actionDisabled}
                onClick={() => onAllocate(dev, targetCardId)}
                title={allocationTitle(dev, selectedCard, assignedToSelectedCard)}
                type="button"
              >
                {actionLabel}
              </button>
            </article>
          )
        })}
      </div>
    </section>
  )
}
