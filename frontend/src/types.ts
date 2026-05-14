import { z } from 'zod'

export const columns = ['backlog', 'analysis', 'development', 'qa', 'done'] as const
export const kaizenTypes = [
  'train-dev',
  'poka-yoke',
  'qa-automation',
  'rest-space',
  'wip-increase',
  'mentoring',
  'interns',
  'marketing',
  'devops-culture',
  'heijunka',
] as const

export type Column = (typeof columns)[number]
export type KaizenType = (typeof kaizenTypes)[number]

const clientSchema = z.object({
  id: z.string(),
  name: z.string(),
  reputation: z.number(),
  active: z.boolean(),
})

const developerSchema = z.object({
  id: z.string(),
  name: z.string(),
  specialty: z.string(),
  level: z.string(),
  speed: z.number(),
  salary: z.number(),
  bug_rate: z.number(),
  moral: z.number(),
  avatar: z.string(),
  active: z.boolean(),
  cards_delivered: z.number(),
  bugs_generated: z.number(),
  tenure_sprints: z.number(),
  onboarding_sprints: z.number(),
  clean_cards_delivered: z.number(),
  god_low_work_streak: z.number(),
})

const cardSchema = z.object({
  id: z.string(),
  title: z.string(),
  card_type: z.string(),
  size: z.string(),
  required_specialties: z.array(z.string()),
  points_total: z.number(),
  progress: z.number(),
  value: z.number(),
  deadline_sprint: z.number(),
  client_id: z.string(),
  column: z.enum(columns),
  created_sprint: z.number(),
  entered_column_sprint: z.number(),
  assigned_dev_ids: z.array(z.string()),
  latent_bug: z.boolean(),
  blocked_by_jidoka: z.boolean(),
  cycle_times: z.record(z.string(), z.number()),
})

const candidateSchema = z.object({
  id: z.string(),
  name: z.string(),
  specialty: z.string(),
  level: z.string(),
  speed: z.number(),
  salary: z.number(),
  bug_rate: z.number(),
  moral: z.number(),
  avatar: z.string(),
  expires_after_sprint: z.number().nullable(),
})

const metricsSchema = z.object({
  sprint: z.number(),
  delivered_cards: z.number(),
  throughput_value: z.number(),
  oee: z.number(),
  lead_time_avg: z.number(),
  bugs_in_production: z.number(),
  heijunka_bonus: z.number(),
})

const timelineEventSchema = z.object({
  sprint: z.number(),
  kind: z.string(),
  message: z.string(),
})

const andonAlertSchema = z.object({
  severity: z.string(),
  code: z.string(),
  message: z.string(),
})

const kaizenImpactSchema = z.object({
  kaizen: z.enum(kaizenTypes),
  label: z.string(),
  before: z.number(),
  after: z.number(),
  delta: z.number(),
})

export const gameStateSchema = z.object({
  id: z.string(),
  seed: z.number(),
  sprint: z.number(),
  phase: z.string(),
  budget: z.number(),
  fixed_cost: z.number(),
  accumulated_profit: z.number(),
  clients: z.array(clientSchema),
  developers: z.array(developerSchema),
  candidates: z.array(candidateSchema),
  cards: z.array(cardSchema),
  wip_limits: z.record(z.string(), z.number()),
  kaizen_points: z.number(),
  active_kaizens: z.array(z.enum(kaizenTypes)),
  metrics_history: z.array(metricsSchema),
  timeline: z.array(timelineEventSchema),
  andon_alerts: z.array(andonAlertSchema),
  pending_events: z.array(z.string()),
  consecutive_negative_budget_sprints: z.number(),
  heijunka_streak: z.number(),
  badges: z.array(z.string()),
  verdict: z.string(),
})

export const hallOfKaizenSchema = z.object({
  verdict: z.string(),
  accumulated_profit: z.number(),
  budget: z.number(),
  oee_avg: z.number(),
  lead_time_avg: z.number(),
  throughput_avg: z.number(),
  top_kaizens: z.array(kaizenImpactSchema),
  sprint_mvp: z.object({
    sprint: z.number(),
    throughput_value: z.number(),
    oee: z.number(),
  }),
  dev_mvp: z.string(),
  badges: z.array(z.string()),
  timeline: z.array(timelineEventSchema),
})

export type Client = z.infer<typeof clientSchema>
export type Developer = z.infer<typeof developerSchema>
export type Card = z.infer<typeof cardSchema>
export type Candidate = z.infer<typeof candidateSchema>
export type SprintMetrics = z.infer<typeof metricsSchema>
export type TimelineEvent = z.infer<typeof timelineEventSchema>
export type AndonAlert = z.infer<typeof andonAlertSchema>
export type GameState = z.infer<typeof gameStateSchema>
export type HallOfKaizen = z.infer<typeof hallOfKaizenSchema>

export type CommandPayload =
  | { type: 'move-card'; card_id: string; target: Column }
  | { type: 'allocate-dev'; dev_id: string; card_id: string | null }
  | { type: 'hire-candidate'; candidate_id: string }
  | { type: 'apply-kaizen'; kaizen: KaizenType; target_id: string | null }
  | { type: 'process-sprint' }

export interface GameApi {
  startGame(seed?: number): Promise<GameState>
  sendCommand(gameId: string, payload: CommandPayload): Promise<GameState>
  loadHallOfKaizen(gameId: string): Promise<HallOfKaizen>
}
