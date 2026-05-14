import { z } from 'zod'
import {
  type CommandPayload,
  type GameApi,
  type GameState,
  type HallOfKaizen,
  gameStateSchema,
  hallOfKaizenSchema,
} from './types'
import { createMockApi } from './mocks/mockApi'

const apiBaseUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
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
  }
}

export function createResilientApi(): GameApi {
  const httpApi = createHttpApi()
  const mockApi = createMockApi()
  let usingMock = false

  return {
    async startGame(seed?: number): Promise<GameState> {
      if (usingMock) {
        return mockApi.startGame(seed)
      }
      try {
        return await httpApi.startGame(seed)
      } catch {
        usingMock = true
        return mockApi.startGame(seed)
      }
    },

    async sendCommand(gameId: string, payload: CommandPayload): Promise<GameState> {
      if (usingMock) {
        return mockApi.sendCommand(gameId, payload)
      }
      try {
        return await httpApi.sendCommand(gameId, payload)
      } catch {
        usingMock = true
        return mockApi.sendCommand(gameId, payload)
      }
    },

    async loadHallOfKaizen(gameId: string): Promise<HallOfKaizen> {
      if (usingMock) {
        return mockApi.loadHallOfKaizen(gameId)
      }
      try {
        return await httpApi.loadHallOfKaizen(gameId)
      } catch {
        usingMock = true
        return mockApi.loadHallOfKaizen(gameId)
      }
    },
  }
}
