import { type Column, type CommandPayload, type GameApi, type GameState, type HallOfKaizen } from '../types'
import { createMockHall, createMockState } from './mockData'

const delayMs = 120

function wait(): Promise<void> {
  return new Promise((resolve) => {
    globalThis.setTimeout(resolve, delayMs)
  })
}

function cloneState(state: GameState): GameState {
  return structuredClone(state)
}

function nextColumn(column: Column): Column {
  if (column === 'backlog') return 'analysis'
  if (column === 'analysis') return 'development'
  if (column === 'development') return 'qa'
  if (column === 'qa') return 'done'
  return 'done'
}

export function createMockApi(): GameApi {
  let state = createMockState()

  return {
    async resumeGame(): Promise<GameState | null> {
      return null
    },

    async startGame(seed?: number): Promise<GameState> {
      await wait()
      state = createMockState(seed)
      return cloneState(state)
    },

    async sendCommand(_gameId: string, payload: CommandPayload): Promise<GameState> {
      await wait()
      state = applyMockCommand(state, payload)
      return cloneState(state)
    },

    async loadHallOfKaizen(_gameId: string): Promise<HallOfKaizen> {
      await wait()
      return createMockHall(state)
    },

    subscribeGame(): () => void {
      return () => undefined
    },
  }
}

function applyMockCommand(state: GameState, payload: CommandPayload): GameState {
  const next = cloneState(state)

  if (payload.type === 'move-card') {
    next.cards = next.cards.map((card) =>
      card.id === payload.card_id
        ? {
            ...card,
            column: payload.target,
            entered_column_sprint: next.sprint,
            progress: payload.target === 'done' ? card.points_total : card.progress,
          }
        : card,
    )
    next.timeline = [
      { sprint: next.sprint, kind: 'move', message: 'Comando de mover card registrado.' },
      ...next.timeline,
    ]
  }

  if (payload.type === 'allocate-dev') {
    next.cards = next.cards.map((card) => ({
      ...card,
      assigned_dev_ids: card.assigned_dev_ids.filter((id) => id !== payload.dev_id),
    }))
    if (payload.card_id !== null) {
      next.cards = next.cards.map((card) =>
        card.id === payload.card_id
          ? { ...card, assigned_dev_ids: [...card.assigned_dev_ids, payload.dev_id] }
          : card,
      )
    }
    next.timeline = [
      { sprint: next.sprint, kind: 'allocate', message: 'Alocacao enviada ao servidor.' },
      ...next.timeline,
    ]
  }

  if (payload.type === 'hire-candidate') {
    const candidate = next.candidates.find((item) => item.id === payload.candidate_id)
    if (candidate !== undefined) {
      next.candidates = next.candidates.filter((item) => item.id !== candidate.id)
      next.developers = [
        ...next.developers,
        {
          ...candidate,
          id: candidate.id.replace('cand', 'dev'),
          active: true,
          cards_delivered: 0,
          bugs_generated: 0,
          tenure_sprints: 0,
          onboarding_sprints: 2,
          clean_cards_delivered: 0,
          god_low_work_streak: 0,
        },
      ]
      next.budget -= candidate.salary
    }
  }

  if (payload.type === 'apply-kaizen') {
    next.kaizen_points = Math.max(0, next.kaizen_points - 1)
    next.active_kaizens = next.active_kaizens.includes(payload.kaizen)
      ? next.active_kaizens
      : [...next.active_kaizens, payload.kaizen]
  }

  if (payload.type === 'process-sprint') {
    const deliveredCards = next.cards.filter((card) => card.column === 'qa' && card.progress >= card.points_total)
    const throughput = deliveredCards.reduce((total, card) => total + card.value, 0)
    next.cards = next.cards.map((card) => {
      if (card.column === 'qa' && card.progress >= card.points_total && !card.blocked_by_jidoka) {
        return { ...card, column: 'done', assigned_dev_ids: [] }
      }
      if (card.assigned_dev_ids.length > 0 && card.column !== 'done') {
        return { ...card, progress: Math.min(card.points_total, card.progress + 6) }
      }
      return card.column === 'backlog' ? card : { ...card, column: nextColumn(card.column) }
    })
    next.sprint += 1
    next.budget += throughput - next.fixed_cost
    next.accumulated_profit += throughput - next.fixed_cost
    next.kaizen_points += next.sprint % 5 === 1 ? 1 : 0
    next.metrics_history = [
      ...next.metrics_history,
      {
        sprint: next.sprint - 1,
        delivered_cards: deliveredCards.length,
        throughput_value: throughput,
        oee: Math.min(0.95, 0.58 + deliveredCards.length * 0.08),
        lead_time_avg: Math.max(1, 5 - deliveredCards.length),
        bugs_in_production: next.cards.some((card) => card.blocked_by_jidoka) ? 1 : 0,
        heijunka_bonus: next.active_kaizens.includes('heijunka') ? Math.round(throughput * 0.1) : 0,
        cycle_time_by_column: { backlog: 1, analysis: 1, development: 1, qa: 1 },
      },
    ]
    next.timeline = [
      { sprint: next.sprint - 1, kind: 'sprint', message: 'Sprint processada no mock temporario.' },
      ...next.timeline,
    ]
  }

  next.andon_alerts = [
    ...next.andon_alerts.filter((alert) => alert.code !== 'kaizen'),
    ...(next.kaizen_points > 0
      ? [{ severity: 'success', code: 'kaizen', message: 'Ha ponto de Kaizen disponivel.' }]
      : []),
  ]

  return next
}
