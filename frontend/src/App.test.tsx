import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { App } from './App'
import { createMockHall, createMockState } from './mocks/mockData'
import { type CommandPayload, type GameApi, type GameState, type HallOfKaizen } from './types'

function createTestApi(state = createMockState()): GameApi {
  let currentState = state
  const hall = createMockHall(currentState)

  return {
    startGame: vi.fn(async (): Promise<GameState> => currentState),
    sendCommand: vi.fn(async (_gameId: string, _payload: CommandPayload): Promise<GameState> => currentState),
    loadHallOfKaizen: vi.fn(async (): Promise<HallOfKaizen> => hall),
  }
}

describe('Factory game UI', () => {
  it('renders Kanban columns with visible WIP limits', async () => {
    render(<App api={createTestApi()} />)

    expect(await screen.findByRole('heading', { name: 'Kanban operacional' })).toBeInTheDocument()
    const kanban = screen.getByRole('region', { name: 'Kanban' })

    expect(within(kanban).getByRole('region', { name: 'Backlog' })).toHaveTextContent('WIP 1/10')
    expect(within(kanban).getByRole('region', { name: 'Dev' })).toHaveTextContent('WIP 1/5')
    expect(within(kanban).getByText('Dashboard OEE')).toBeInTheDocument()
  })

  it('renders developer Gemba details with names and morale', async () => {
    render(<App api={createTestApi()} />)

    const devPanel = await screen.findByRole('region', { name: 'Devs' })

    expect(within(devPanel).getByText('Lia Backend')).toBeInTheDocument()
    expect(within(devPanel).getByText('Theo Produto')).toBeInTheDocument()
    expect(within(devPanel).getByText('42')).toBeInTheDocument()
  })

  it('opens Hall of Kaizen with final metrics and badges', async () => {
    const user = userEvent.setup()
    render(<App api={createTestApi()} />)

    await screen.findByRole('heading', { name: 'Kanban operacional' })
    await user.click(screen.getByRole('button', { name: 'Hall of Kaizen' }))

    const hall = await screen.findByRole('region', { name: 'Hall of Kaizen' })
    expect(within(hall).getByRole('heading', { name: 'Hall of Kaizen' })).toBeInTheDocument()
    expect(within(hall).getByText('Zero Bug Sprint')).toBeInTheDocument()
    expect(within(hall).getByText('Dev MVP')).toBeInTheDocument()
  })
})
