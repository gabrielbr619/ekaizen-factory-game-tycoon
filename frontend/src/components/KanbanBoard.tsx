import { useMemo, useState, type DragEvent } from 'react'
import { ChevronRight, KanbanSquare } from 'lucide-react'
import { currencyFormatter } from '../lib/formatters'
import { columnHelp, columnLabel, cycleSummary, nextColumn } from '../lib/gameLabels'
import { columns, type Card, type Column, type GameState } from '../types'
import { PanelTitle } from './PanelTitle'

type KanbanBoardProps = {
  game: GameState
  selectedCardId: string | null
  onSelectCard(cardId: string): void
  onInvalidDrop(): void
  onMoveCard(card: Card, target: Column): void
}

export function KanbanBoard({ game, selectedCardId, onSelectCard, onInvalidDrop, onMoveCard }: KanbanBoardProps) {
  const [draggingCardId, setDraggingCardId] = useState<string | null>(null)
  const [dropTargetColumn, setDropTargetColumn] = useState<Column | null>(null)

  const draggingCard = useMemo(
    () => game.cards.find((card) => card.id === draggingCardId) ?? null,
    [draggingCardId, game.cards],
  )

  function clearDragState() {
    setDraggingCardId(null)
    setDropTargetColumn(null)
  }

  function handleDrop(event: DragEvent<HTMLElement>, target: Column) {
    event.preventDefault()
    const draggedId = draggingCardId ?? event.dataTransfer.getData('text/plain')
    const card = game.cards.find((item) => item.id === draggedId)
    setDropTargetColumn(null)
    if (card === undefined || nextColumn(card.column) !== target) {
      if (card !== undefined) onInvalidDrop()
      clearDragState()
      return
    }
    onMoveCard(card, target)
    clearDragState()
  }

  return (
    <section className="kanban-area" aria-label="Kanban">
      <div className="section-heading">
        <PanelTitle icon={<KanbanSquare aria-hidden="true" />} title="Kanban operacional" />
        <span>Fluxo sequencial: Backlog → Analise → Dev → QA; Done e liberado no fechamento da sprint</span>
      </div>
      <div className="kanban-columns">
        {columns.map((column) => {
          const cards = game.cards.filter((card) => card.column === column)
          const limit = game.wip_limits[column] ?? 0
          const acceptsDraggingCard = draggingCard !== null && nextColumn(draggingCard.column) === column
          const isDropTarget = dropTargetColumn === column
          return (
            <section
              className={`kanban-column ${isDropTarget ? (acceptsDraggingCard ? 'drop-valid' : 'drop-invalid') : ''}`}
              key={column}
              aria-label={columnLabel(column)}
              onDragEnter={(event) => {
                event.preventDefault()
                setDropTargetColumn(column)
              }}
              onDragOver={(event) => {
                event.preventDefault()
                event.dataTransfer.dropEffect = acceptsDraggingCard ? 'move' : 'none'
              }}
              onDragLeave={(event) => {
                event.preventDefault()
                setDropTargetColumn(null)
              }}
              onDrop={(event) => handleDrop(event, column)}
            >
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
                    dragging={card.id === draggingCardId}
                    onSelect={() => onSelectCard(card.id)}
                    onDragStart={(event) => {
                      event.dataTransfer.effectAllowed = 'move'
                      event.dataTransfer.setData('text/plain', card.id)
                      setDraggingCardId(card.id)
                    }}
                    onDragEnd={clearDragState}
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
  dragging: boolean
  onSelect(): void
  onDragStart(event: DragEvent<HTMLElement>): void
  onDragEnd(): void
  onMove(): void
}

function WorkCard({ card, game, selected, dragging, onSelect, onDragStart, onDragEnd, onMove }: WorkCardProps) {
  const client = game.clients.find((item) => item.id === card.client_id)
  const assigned = card.assigned_dev_ids.flatMap((id) => {
    const dev = game.developers.find((item) => item.id === id)
    return dev === undefined ? [] : [dev.name]
  })
  const progress = `${card.progress}/${card.points_total}`
  const canMove = nextColumn(card.column) !== null
  const movementHint = canMove
    ? 'Arraste para a proxima coluna ou use Mover.'
    : 'QA e Done sao resolvidos no fechamento da sprint.'
  return (
    <article
      aria-label={`Card ${card.title}`}
      className={`work-card ${selected ? 'selected' : ''} ${dragging ? 'dragging' : ''} ${card.blocked_by_jidoka ? 'jidoka' : ''}`}
      draggable={canMove}
      onDragEnd={onDragEnd}
      onDragStart={onDragStart}
    >
      <button
        className="card-select"
        aria-label={`Selecionar card ${card.title}`}
        onClick={onSelect}
        title={`Selecionar ${card.title}. ${movementHint} Requisitos: ${card.required_specialties.join(', ')}. Valor ${currencyFormatter.format(card.value)}. Prazo sprint ${card.deadline_sprint}. Progresso ${progress}.`}
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
      <button
        className="move-button"
        disabled={!canMove}
        onClick={onMove}
        title={
          canMove
            ? `Mover ${card.title} para ${columnLabel(nextColumn(card.column) ?? card.column)}`
            : 'QA e Done sao resolvidos no fechamento da sprint'
        }
        type="button"
      >
        Mover
        <ChevronRight aria-hidden="true" />
      </button>
    </article>
  )
}
