import { Moon, Play, RotateCcw, Sun } from 'lucide-react'
import { currencyFormatter } from '../lib/formatters'
import { type AndonAlert, type GameState } from '../types'
import { Button } from './ui/Button'
import { Kpi } from './Kpi'

export type ThemeMode = 'light' | 'dark'

type TopBarProps = {
  game: GameState
  sprintAlerts: AndonAlert[]
  clientReputation: number
  theme: ThemeMode
  busy: boolean
  confirmSprint: boolean
  onCancelSprint(): void
  onConfirmSprint(): void
  onRequestSprint(): void
  onRestart(): void
  onToggleTheme(): void
}

export function TopBar({
  game,
  sprintAlerts,
  clientReputation,
  theme,
  busy,
  confirmSprint,
  onCancelSprint,
  onConfirmSprint,
  onRequestSprint,
  onRestart,
  onToggleTheme,
}: TopBarProps) {
  const visibleSprintAlerts = sprintAlerts.filter((alert) => alert.severity !== 'success')

  return (
    <header className="top-bar">
      <div className="brand-block">
        <span className="brand-mark">eK</span>
        <div>
          <h1>eKaizen Factory Game Tycoon</h1>
          <p>Fase {game.phase} · sprint {game.sprint}/35</p>
        </div>
      </div>
      <div className="kpi-strip" aria-label="Estado geral">
        <Kpi label="Budget" value={currencyFormatter.format(game.budget)} tone={game.budget < 0 ? 'bad' : 'good'} title="Caixa disponivel. Se virar negativo por tempo demais, a software house quebra." />
        <Kpi label="Lucro acum." value={currencyFormatter.format(game.accumulated_profit)} title="Resultado acumulado depois de entregas, custos fixos e eventos." />
        <Kpi label="Reputacao" value={`${clientReputation}%`} tone={clientReputation < 40 ? 'bad' : 'good'} title="Media dos clientes ativos. Prazos perdidos e bugs derrubam este placar." />
        <Kpi label="Devs ativos" value={`${game.developers.filter((dev) => dev.active).length}`} title="Capacidade atual do time. Moral baixa e burnout reduzem sua chance de sobreviver." />
        <Kpi label="Kaizen" value={`${game.kaizen_points} pts`} tone={game.kaizen_points > 0 ? 'good' : 'neutral'} title="Pontos para melhorias de processo que ajudam fluxo, qualidade, moral e caixa." />
      </div>
      <div className="top-actions">
        {confirmSprint ? (
          <div className="confirm-sprint" role="alert" aria-live="assertive" aria-label="Riscos antes de encerrar sprint">
            <div className="confirm-actions">
              <Button disabled={busy} onClick={onConfirmSprint} title="Confirmar processamento da sprint no backend" variant="danger">
                Confirmar
              </Button>
              <Button disabled={busy} onClick={onCancelSprint} title="Cancelar e continuar jogando a sprint atual" variant="secondary">
                Cancelar
              </Button>
            </div>
            <div className="sprint-risk-summary">
              <strong>{visibleSprintAlerts.length > 0 ? 'Antes de encerrar' : 'Sem alertas bloqueantes'}</strong>
              {visibleSprintAlerts.length > 0 ? (
                <ul>
                  {visibleSprintAlerts.map((alert, index) => (
                    <li className={`sprint-risk sprint-risk-${alert.severity}`} key={`${alert.code}-${index}-${alert.message}`}>
                      {alert.message}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>O backend nao informou Andons ativos para esta sprint.</p>
              )}
            </div>
          </div>
        ) : (
          <Button disabled={busy} onClick={onRequestSprint} title="Encerrar sprint e processar custos, progresso, bugs e eventos" variant="primary">
            <Play aria-hidden="true" />
            Encerrar sprint
          </Button>
        )}
        <Button disabled={busy} onClick={onToggleTheme} title={theme === 'dark' ? 'Ativar modo claro' : 'Ativar modo escuro'} aria-label={theme === 'dark' ? 'Ativar modo claro' : 'Ativar modo escuro'} variant="icon">
          {theme === 'dark' ? <Sun aria-hidden="true" /> : <Moon aria-hidden="true" />}
        </Button>
        <Button disabled={busy} onClick={onRestart} title="Iniciar nova partida" variant="icon">
          <RotateCcw aria-hidden="true" />
          Nova
        </Button>
      </div>
    </header>
  )
}
