import { Users } from 'lucide-react'
import { currencyFormatter } from '../lib/formatters'
import { allocationTitle, levelLabel, specialtyBadge, specialtyLabel } from '../lib/gameLabels'
import { type Card, type Developer } from '../types'
import { PanelTitle } from './PanelTitle'
import { Tooltip } from './ui/Tooltip'

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
          const devDetailId = `dev-detail-${dev.id}`
          const actionDetailId = `dev-action-detail-${dev.id}`
          const raiseDetail =
            dev.raise_requested_salary === undefined || dev.raise_requested_salary === null
              ? ''
              : ` Pedido de aumento para ${currencyFormatter.format(dev.raise_requested_salary)} ate sprint ${dev.raise_request_deadline_sprint}.`
          const devDetail = `${dev.name}. ${specialtyLabel(dev.specialty)}, ${levelLabel(dev.level)}. Moral ${dev.moral}. Salario ${currencyFormatter.format(dev.salary)}. Entregas ${dev.cards_delivered}. Bugs ${dev.bugs_generated}. Tempo de casa ${dev.tenure_sprints} sprints.${raiseDetail}`

          return (
            <article className={`dev-row ${selectedDevId === dev.id ? 'selected' : ''}`} key={dev.id}>
              <button
                aria-describedby={devDetailId}
                aria-label={`Selecionar dev ${dev.name}`}
                className="dev-select tooltip-host"
                onClick={() => onSelectDev(dev.id)}
                type="button"
              >
                <span className={`avatar spec-${dev.specialty}`}>{specialtyBadge(dev.specialty)}</span>
                <span className="dev-identity">
                  <strong>{dev.name}</strong>
                  <small>{levelLabel(dev.level)} · {specialtyLabel(dev.specialty)}</small>
                  {dev.raise_requested_salary === undefined || dev.raise_requested_salary === null ? null : (
                    <small className="dev-warning">Aumento ate S{dev.raise_request_deadline_sprint}</small>
                  )}
                </span>
                <span className={`morale ${dev.moral < 30 ? 'low' : ''}`}>
                  {dev.moral}
                </span>
                <Tooltip id={devDetailId} text={devDetail} />
              </button>
              <button
                aria-label={`${actionLabel} ${dev.name}`}
                aria-describedby={actionDetailId}
                className={`tiny-action tooltip-host ${assignedToSelectedCard ? 'remove-action' : ''}`}
                disabled={actionDisabled}
                onClick={() => onAllocate(dev, targetCardId)}
                type="button"
              >
                {actionLabel}
                <Tooltip id={actionDetailId} text={allocationTitle(dev, selectedCard, assignedToSelectedCard)} />
              </button>
            </article>
          )
        })}
      </div>
    </section>
  )
}
