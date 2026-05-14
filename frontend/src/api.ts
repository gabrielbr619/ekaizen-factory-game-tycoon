import { z } from 'zod'
import {
  type CommandPayload,
  type GameApi,
  type GameState,
  type HallOfKaizen,
  gameStateSchema,
  hallOfKaizenSchema,
} from './types'

const apiBaseUrl = import.meta.env.VITE_API_URL ?? ''
const errorPayloadSchema = z.object({ detail: z.string() })

function commandId(): string {
  return globalThis.crypto.randomUUID()
}

async function parseJson(response: Response): Promise<unknown> {
  const payload = await response.json()
  if (!response.ok) {
    const detail = zodErrorDetail(payload)
    throw new Error(detail)
  }
  return payload
}

function zodErrorDetail(payload: unknown): string {
  const parsed = errorPayloadSchema.safeParse(payload)
  return parsed.success ? parsed.data.detail : 'Falha ao comunicar com o servidor.'
}

export function createHttpApi(): GameApi {
  return {
    async resumeGame(): Promise<GameState | null> {
      const response = await fetch(`${apiBaseUrl}/games/current`, {
        credentials: 'include',
      })
      if (response.status === 404 || response.status === 401) return null
      return gameStateSchema.parse(await parseJson(response))
    },

    async startGame(seed?: number): Promise<GameState> {
      const response = await fetch(`${apiBaseUrl}/games`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seed }),
      })
      return gameStateSchema.parse(await parseJson(response))
    },

    async sendCommand(gameId: string, payload: CommandPayload): Promise<GameState> {
      const id = commandId()
      const response = await fetch(`${apiBaseUrl}/games/${gameId}/commands`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': id,
        },
        body: JSON.stringify({ command_id: id, payload }),
      })
      return gameStateSchema.parse(await parseJson(response))
    },

    async loadHallOfKaizen(gameId: string): Promise<HallOfKaizen> {
      const response = await fetch(`${apiBaseUrl}/games/${gameId}/hall-of-kaizen`, {
        credentials: 'include',
      })
      return hallOfKaizenSchema.parse(await parseJson(response))
    },

    subscribeGame(gameId: string, onState: (state: GameState) => void, onError: () => void): () => void {
      const source = new EventSource(`${apiBaseUrl}/games/${gameId}/events`, {
        withCredentials: true,
      })
      source.addEventListener('state', (event) => {
        const parsed = gameStateSchema.safeParse(JSON.parse(event.data))
        if (parsed.success) onState(parsed.data)
      })
      source.onerror = () => {
        onError()
        source.close()
      }
      return () => source.close()
    },
  }
}
