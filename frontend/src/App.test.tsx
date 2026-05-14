import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
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
    subscribeGame: vi.fn(() => () => undefined),
  }
}

function createDataTransfer() {
  const values = new Map<string, string>()
  return {
    dropEffect: 'none',
    effectAllowed: 'all',
    getData(format: string): string {
      return values.get(format) ?? ''
    },
    setData(format: string, data: string): void {
      values.set(format, data)
    },
  }
}

describe('Factory game UI', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

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

  it('exposes card, developer and metric details without native title-only help', async () => {
    render(<App api={createTestApi()} />)

    const metrics = await screen.findByRole('region', { name: 'Metricas' })
    const oeeMetric = within(metrics).getByRole('group', { name: /OEE: 64%/ })
    expect(oeeMetric).not.toHaveAttribute('title')
    expect(oeeMetric).toHaveAccessibleDescription(/Qualidade operacional geral/i)
    expect(within(oeeMetric).getAllByText(/Qualidade operacional geral/i)).toHaveLength(2)

    const devPanel = screen.getByRole('region', { name: 'Devs' })
    const devButton = within(devPanel)
      .getAllByRole('button', { name: /Lia Backend/i })
      .find((button) => !button.className.includes('tiny-action'))
    expect(devButton).toBeDefined()
    expect(devButton).not.toHaveAttribute('title')
    expect(devButton).toHaveAccessibleDescription(/Salario R\$\s*700/i)

    const kanban = screen.getByRole('region', { name: 'Kanban' })
    const cardButton = within(kanban).getByRole('button', { name: /Selecionar card Dashboard OEE/i })
    expect(cardButton).not.toHaveAttribute('title')
    expect(cardButton).toHaveAccessibleDescription(/Valor R\$\s*6\.000/i)
  })

  it('separates server pending decisions from events already applied to state', async () => {
    render(<App api={createTestApi()} />)

    const eventsPanel = await screen.findByRole('region', { name: 'Eventos' })

    expect(within(eventsPanel).getByText('Eventos para reagir')).toBeInTheDocument()
    expect(within(eventsPanel).getByText(/Auditoria de OEE/i)).toBeInTheDocument()
    expect(within(eventsPanel).getByText('Ja aplicado no estado')).toBeInTheDocument()
    expect(within(eventsPanel).getByText(/Pipeline de deploy foi puxado/i)).toBeInTheDocument()
  })

  it('shows an initial tutorial overlay explaining core gameplay', async () => {
    render(<App api={createTestApi()} />)

    const tutorial = await screen.findByRole('dialog', { name: 'Tutorial inicial' })

    expect(within(tutorial).getByRole('heading', { name: 'Tutorial inicial' })).toBeInTheDocument()
    expect(within(tutorial).getByText(/Kanban/i)).toBeInTheDocument()
    expect(within(tutorial).getByText(/Selecione um card e um dev/i)).toBeInTheDocument()
    expect(within(tutorial).getByText(/PDCA/i)).toBeInTheDocument()
    expect(within(tutorial).getByRole('heading', { name: 'Andon' })).toBeInTheDocument()
    expect(within(tutorial).getByRole('heading', { name: 'Como vencer' })).toBeInTheDocument()
    expect(within(tutorial).getByText(/software house viva/i)).toBeInTheDocument()
    expect(within(tutorial).getByText(/Hall of Kaizen com veredito positivo/i)).toBeInTheDocument()
    expect(within(tutorial).getByRole('button', { name: 'Começar partida' })).toBeInTheDocument()
    await waitFor(() => expect(within(tutorial).getByRole('button', { name: 'Começar partida' })).toHaveFocus())
    expect(screen.getByRole('heading', { name: 'Kanban operacional' })).toBeInTheDocument()
  })

  it('supports keyboard dismissal and a simple focus trap in the tutorial', async () => {
    const user = userEvent.setup()
    render(<App api={createTestApi()} />)

    const tutorial = await screen.findByRole('dialog', { name: 'Tutorial inicial' })
    const closeButton = within(tutorial).getByRole('button', { name: 'Fechar' })
    const startButton = within(tutorial).getByRole('button', { name: 'Começar partida' })

    await waitFor(() => expect(startButton).toHaveFocus())

    await user.tab()
    expect(closeButton).toHaveFocus()

    await user.tab({ shift: true })
    expect(startButton).toHaveFocus()

    await user.keyboard('{Escape}')
    expect(screen.queryByRole('dialog', { name: 'Tutorial inicial' })).not.toBeInTheDocument()
  })

  it('keeps win instructions in the tutorial instead of fixed operation chrome', async () => {
    render(<App api={createTestApi()} />)

    const tutorial = await screen.findByRole('dialog', { name: 'Tutorial inicial' })

    expect(within(tutorial).getByRole('heading', { name: 'Como vencer' })).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Objetivo do jogo' })).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Como ganhar' })).not.toBeInTheDocument()
  })

  it('lets the player toggle and persist dark mode', async () => {
    const user = userEvent.setup()
    render(<App api={createTestApi()} />)

    await screen.findByRole('heading', { name: 'Kanban operacional' })
    await user.click(screen.getByRole('button', { name: 'Ativar modo escuro' }))

    expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
    expect(localStorage.getItem('factory-game-theme')).toBe('dark')
    expect(screen.getByRole('button', { name: 'Ativar modo claro' })).toBeInTheDocument()
  })

  it('lets the player close the initial tutorial and keep playing', async () => {
    const user = userEvent.setup()
    render(<App api={createTestApi()} />)

    const tutorial = await screen.findByRole('dialog', { name: 'Tutorial inicial' })
    await user.click(within(tutorial).getByRole('button', { name: 'Começar partida' }))

    expect(screen.queryByRole('dialog', { name: 'Tutorial inicial' })).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Kanban operacional' })).toBeInTheDocument()
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

  it('sends move-card when a card is dropped on the next Kanban column', async () => {
    const api = createTestApi()
    render(<App api={api} />)

    const kanban = await screen.findByRole('region', { name: 'Kanban' })
    const card = within(kanban).getByRole('article', { name: 'Card Dashboard OEE' })
    const analysisColumn = within(kanban).getByRole('region', { name: 'Analise' })
    const dataTransfer = createDataTransfer()

    fireEvent.dragStart(card, { dataTransfer })
    fireEvent.dragEnter(analysisColumn, { dataTransfer })
    fireEvent.drop(analysisColumn, { dataTransfer })

    await waitFor(() => {
      expect(api.sendCommand).toHaveBeenCalledWith('mock-4242', {
        type: 'move-card',
        card_id: 'card-1-1',
        target: 'analysis',
      })
    })
  })

  it('does not send move-card and explains when a card is dropped on an invalid column', async () => {
    const api = createTestApi()
    render(<App api={api} />)

    const kanban = await screen.findByRole('region', { name: 'Kanban' })
    const card = within(kanban).getByRole('article', { name: 'Card Dashboard OEE' })
    const devColumn = within(kanban).getByRole('region', { name: 'Dev' })
    const dataTransfer = createDataTransfer()

    fireEvent.dragStart(card, { dataTransfer })
    fireEvent.dragEnter(devColumn, { dataTransfer })
    fireEvent.drop(devColumn, { dataTransfer })

    expect(api.sendCommand).not.toHaveBeenCalled()
    expect(screen.getByRole('region', { name: 'Status' })).toHaveTextContent(
      'Fluxo sequencial: mova cards apenas para a proxima coluna.',
    )
  })

  it('does not send move-card and explains when a card is dropped on an earlier column', async () => {
    const api = createTestApi()
    render(<App api={api} />)

    const kanban = await screen.findByRole('region', { name: 'Kanban' })
    const card = within(kanban).getByRole('article', { name: 'Card Bug critico em apontamento' })
    const analysisColumn = within(kanban).getByRole('region', { name: 'Analise' })
    const dataTransfer = createDataTransfer()

    fireEvent.dragStart(card, { dataTransfer })
    fireEvent.dragEnter(analysisColumn, { dataTransfer })

    expect(analysisColumn).toHaveClass('drop-invalid')

    fireEvent.drop(analysisColumn, { dataTransfer })

    expect(api.sendCommand).not.toHaveBeenCalled()
    expect(screen.getByRole('region', { name: 'Status' })).toHaveTextContent(
      'Fluxo sequencial: mova cards apenas para a proxima coluna.',
    )
  })

  it('keeps QA completion as sprint processing instead of manual Done movement', async () => {
    render(<App api={createTestApi()} />)

    const kanban = await screen.findByRole('region', { name: 'Kanban' })
    const qaCard = within(kanban).getByRole('article', { name: 'Card Bug critico em apontamento' })

    expect(within(qaCard).getByRole('button', { name: /Mover/i })).toBeDisabled()
  })

  it('surfaces backend Andons before confirming sprint processing', async () => {
    const user = userEvent.setup()
    const state = createMockState()
    state.andon_alerts = [
      {
        severity: 'warning',
        code: 'large-card-junior-alone',
        message: 'Nina QA sozinho em card G (Pipeline de deploy) nao vai progredir.',
      },
      {
        severity: 'warning',
        code: 'large-card-pleno-no-mentor',
        message: 'Pleno em card G (Pipeline de deploy) precisa de mentor Senior/God-tier.',
      },
      { severity: 'success', code: 'kaizen', message: 'Ha ponto de Kaizen disponivel.' },
    ]
    const api = createTestApi(state)
    render(<App api={api} />)

    await screen.findByRole('heading', { name: 'Kanban operacional' })
    await user.click(screen.getByRole('button', { name: 'Encerrar sprint' }))

    const warning = screen.getByRole('alert', { name: 'Riscos antes de encerrar sprint' })
    expect(within(warning).getByText('Antes de encerrar')).toBeInTheDocument()
    expect(within(warning).getByText(/Nina QA sozinho em card G/i)).toBeInTheDocument()
    expect(within(warning).getByText(/precisa de mentor Senior\/God-tier/i)).toBeInTheDocument()
    expect(within(warning).queryByText(/Kaizen disponivel/i)).not.toBeInTheDocument()
    expect(api.sendCommand).not.toHaveBeenCalled()

    await user.click(within(warning).getByRole('button', { name: 'Confirmar' }))

    expect(api.sendCommand).toHaveBeenCalledWith('mock-4242', { type: 'process-sprint' })
  })

  it('lets the player remove a developer already allocated to the selected card', async () => {
    const user = userEvent.setup()
    const api = createTestApi()
    render(<App api={api} />)

    await screen.findByRole('heading', { name: 'Kanban operacional' })
    await user.click(screen.getByRole('button', { name: /Selecionar card Pipeline de deploy/i }))

    const devPanel = screen.getByRole('region', { name: 'Devs' })
    await user.click(within(devPanel).getByRole('button', { name: 'Remover Lia Backend' }))

    expect(api.sendCommand).toHaveBeenCalledWith('mock-4242', {
      type: 'allocate-dev',
      dev_id: 'd1',
      card_id: null,
    })
  })
})
