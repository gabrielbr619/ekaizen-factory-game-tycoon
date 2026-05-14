import { useEffect, useMemo, useState } from 'react'
import { Activity, AlertTriangle, Award, CheckCircle2, KanbanSquare } from 'lucide-react'
import { DevelopersPanel } from './components/DevelopersPanel'
import { HallPanel } from './components/HallPanel'
import { HiringPanel } from './components/HiringPanel'
import { KaizenPanel } from './components/KaizenPanel'
import { KanbanBoard } from './components/KanbanBoard'
import { OnboardingPanel } from './components/OnboardingPanel'
import { ClientsPanel, EventsPanel, HistoryPanel, MetricsPanel } from './components/SidePanels'
import { TopBar, type ThemeMode } from './components/TopBar'
import { columnLabel, kaizenLabel, kaizenTarget } from './lib/gameLabels'
import { type CommandPayload, type GameApi, type GameState, type HallOfKaizen } from './types'

type AppProps = {
  api: GameApi
}

type ViewMode = 'ops' | 'hall'

const initialGameRequests = new WeakMap<GameApi, Promise<GameState>>()
const sequentialFlowNotice = 'Fluxo sequencial: mova cards apenas para a proxima coluna.'
const themeStorageKey = 'factory-game-theme'

function initialTheme(): ThemeMode {
  return localStorage.getItem(themeStorageKey) === 'dark' ? 'dark' : 'light'
}

function loadInitialGame(api: GameApi): Promise<GameState> {
  const existing = initialGameRequests.get(api)
  if (existing !== undefined) return existing
  const request = api.startGame()
  initialGameRequests.set(api, request)
  return request
}

export function App({ api }: AppProps) {
  const [game, setGame] = useState<GameState | null>(null)
  const [hall, setHall] = useState<HallOfKaizen | null>(null)
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null)
  const [selectedDevId, setSelectedDevId] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('ops')
  const [notice, setNotice] = useState('Inicializando sala de controle...')
  const [busy, setBusy] = useState(false)
  const [confirmSprint, setConfirmSprint] = useState(false)
  const [showOnboarding, setShowOnboarding] = useState(true)
  const [theme, setTheme] = useState<ThemeMode>(initialTheme)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem(themeStorageKey, theme)
  }, [theme])

  useEffect(() => {
    let mounted = true
    setBusy(true)
    loadInitialGame(api)
      .then((state) => {
        if (mounted) {
          setGame(state)
          setSelectedCardId(state.cards.find((card) => card.column !== 'done')?.id ?? null)
          setSelectedDevId(state.developers.find((dev) => dev.active)?.id ?? null)
          setNotice(state.id.startsWith('mock-') ? 'Mock temporario ativo: backend indisponivel.' : '')
        }
      })
      .catch((error: Error) => {
        if (mounted) setNotice(error.message)
      })
      .finally(() => {
        if (mounted) setBusy(false)
      })
    return () => {
      mounted = false
    }
  }, [api])

  useEffect(() => {
    if (game === null || game.id.startsWith('mock-')) return undefined
    return api.subscribeGame(
      game.id,
      (state) => {
        setGame(state)
      },
      () => {
        setNotice('Conexao em tempo real encerrada; comandos continuam sincronizando.')
      },
    )
  }, [api, game?.id])

  const selectedCard = useMemo(
    () => game?.cards.find((card) => card.id === selectedCardId) ?? null,
    [game, selectedCardId],
  )
  const selectedDev = useMemo(
    () => game?.developers.find((dev) => dev.id === selectedDevId) ?? null,
    [game, selectedDevId],
  )

  async function startFreshGame() {
    setBusy(true)
    setHall(null)
    setViewMode('ops')
    try {
      const state = await api.startGame()
      setGame(state)
      setSelectedCardId(state.cards.find((card) => card.column !== 'done')?.id ?? null)
      setSelectedDevId(state.developers.find((dev) => dev.active)?.id ?? null)
      setNotice('Nova partida iniciada.')
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Falha ao iniciar partida.')
    } finally {
      setBusy(false)
    }
  }

  async function sendCommand(payload: CommandPayload, success: string) {
    if (game === null) return
    setBusy(true)
    try {
      const state = await api.sendCommand(game.id, payload)
      setGame(state)
      setNotice(success)
      if (state.verdict !== 'playing') {
        await loadHall(state)
      }
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Comando recusado pelo servidor.')
    } finally {
      setBusy(false)
      setConfirmSprint(false)
    }
  }

  async function loadHall(state = game) {
    if (state === null) return
    setBusy(true)
    try {
      const result = await api.loadHallOfKaizen(state.id)
      setHall(result)
      setViewMode('hall')
      setNotice('Hall of Kaizen carregado.')
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Falha ao carregar Hall of Kaizen.')
    } finally {
      setBusy(false)
    }
  }

  if (game === null) {
    return (
      <main className="loading-screen">
        <Activity aria-hidden="true" />
        <p>{notice}</p>
      </main>
    )
  }

  const lastMetrics = game.metrics_history.at(-1)
  const activeClients = game.clients.filter((client) => client.active)
  const clientReputation =
    activeClients.length === 0
      ? 0
      : Math.round(activeClients.reduce((total, client) => total + client.reputation, 0) / activeClients.length)

  return (
    <main className="factory-app">
      <TopBar
        game={game}
        clientReputation={clientReputation}
        theme={theme}
        busy={busy}
        confirmSprint={confirmSprint}
        onCancelSprint={() => setConfirmSprint(false)}
        onConfirmSprint={() => sendCommand({ type: 'process-sprint' }, 'Sprint processada.')}
        onRequestSprint={() => setConfirmSprint(true)}
        onRestart={startFreshGame}
        onToggleTheme={() => setTheme((current) => (current === 'dark' ? 'light' : 'dark'))}
      />

      <section className="andon-strip" aria-label="Andon">
        <div className="andon-title">
          <AlertTriangle aria-hidden="true" />
          <span>Andon</span>
        </div>
        <div className="andon-alerts">
          {game.andon_alerts.length === 0 ? (
            <span className="andon-empty">Linha estavel, sem alertas ativos.</span>
          ) : (
            game.andon_alerts.map((alert, index) => (
              <span
                className={`andon-alert andon-${alert.severity}`}
                key={`${alert.code}-${index}-${alert.message}`}
                title="Andon mostra situacoes que precisam de decisao antes que virem perda."
              >
                {alert.message}
              </span>
            ))
          )}
        </div>
      </section>

      <nav className="view-tabs" aria-label="Telas">
        <button className={viewMode === 'ops' ? 'active' : ''} onClick={() => setViewMode('ops')} title="Voltar para a sala de controle da partida atual" type="button">
          <KanbanSquare aria-hidden="true" />
          Jogo
        </button>
        <button className={viewMode === 'hall' ? 'active' : ''} onClick={() => loadHall()} title="Abrir Hall of Kaizen com placar, historico, MVPs e badges" type="button">
          <Award aria-hidden="true" />
          Hall of Kaizen
        </button>
        <button onClick={() => setShowOnboarding(true)} title="Abrir tutorial de como jogar" type="button">
          <CheckCircle2 aria-hidden="true" />
          Tutorial
        </button>
      </nav>

      {notice.length > 0 ? (
        <section className="status-strip" aria-label="Status">
          <strong>{notice}</strong>
        </section>
      ) : null}

      {viewMode === 'ops' ? (
        <div className="ops-grid">
          <section className="left-rail">
            <MetricsPanel metrics={lastMetrics} game={game} />
            <ClientsPanel game={game} />
            <EventsPanel events={game.pending_events} />
            <HistoryPanel timeline={game.timeline} />
          </section>

          <KanbanBoard
            game={game}
            selectedCardId={selectedCardId}
            onSelectCard={setSelectedCardId}
            onInvalidDrop={() => setNotice(sequentialFlowNotice)}
            onMoveCard={(card, target) =>
              sendCommand({ type: 'move-card', card_id: card.id, target }, `${card.title} enviado para ${columnLabel(target)}.`)
            }
          />

          <section className="right-rail">
            <DevelopersPanel
              developers={game.developers}
              selectedCard={selectedCard}
              selectedDevId={selectedDevId}
              onSelectDev={setSelectedDevId}
              onAllocate={(dev, cardId) =>
                sendCommand(
                  { type: 'allocate-dev', dev_id: dev.id, card_id: cardId },
                  cardId === null
                    ? `${dev.name} removido do card conforme comando do backend.`
                    : `${dev.name} alocado conforme comando do backend.`,
                )
              }
            />
            <HiringPanel game={game} onHire={(candidate) => sendCommand({ type: 'hire-candidate', candidate_id: candidate.id }, `${candidate.name} contratado.`)} />
            <KaizenPanel
              game={game}
              selectedDev={selectedDev}
              selectedCard={selectedCard}
              onApply={(kaizen) =>
                sendCommand(
                  { type: 'apply-kaizen', kaizen, target_id: kaizenTarget(kaizen, selectedDev, selectedCard) },
                  `PDCA aplicado: ${kaizenLabel(kaizen)}.`,
                )
              }
            />
          </section>
        </div>
      ) : (
        <HallPanel hall={hall} game={game} onRestart={startFreshGame} />
      )}

      {showOnboarding ? <OnboardingPanel sprint={game.sprint} onDismiss={() => setShowOnboarding(false)} /> : null}
    </main>
  )
}
