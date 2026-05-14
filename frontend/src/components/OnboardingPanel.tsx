import { AlertTriangle, Award, Gauge, KanbanSquare, Play, Sparkles, Users } from 'lucide-react'

type OnboardingPanelProps = {
  sprint: number
  onDismiss(): void
}

export function OnboardingPanel({ sprint, onDismiss }: OnboardingPanelProps) {
  return (
    <section className="onboarding-backdrop" aria-labelledby="onboarding-title" aria-modal="true" role="dialog">
      <div className="onboarding-dialog">
        <div className="onboarding-header">
          <div>
            <span className="eyebrow">Sprint {sprint} · guia rapido</span>
            <h2 id="onboarding-title">Tutorial inicial</h2>
          </div>
          <button className="secondary-action" onClick={onDismiss} title="Fechar tutorial e continuar no jogo" type="button">
            Fechar
          </button>
        </div>

        <div className="onboarding-body">
          <section className="tutorial-section tutorial-victory">
            <h3>
              <Award aria-hidden="true" />
              Como vencer
            </h3>
            <p>
              Objetivo: manter a software house viva, proteger Budget e lucro acumulado, melhorar Reputacao, OEE,
              Lead Time, Throughput e Bugs ate chegar ao Hall of Kaizen com veredito positivo.
            </p>
            <p>
              Na pratica: entregue cards no prazo, evite bugs em producao, mantenha devs com moral e use Kaizens antes
              dos gargalos virarem crise.
            </p>
          </section>
          <section className="tutorial-section">
            <h3>
              <KanbanSquare aria-hidden="true" />
              Fluxo Kanban
            </h3>
            <p>Puxe demanda do Backlog para Analise, Dev, QA e Done. Respeite WIP e use o botao Mover em cada card.</p>
          </section>
          <section className="tutorial-section">
            <h3>
              <Users aria-hidden="true" />
              Card e dev
            </h3>
            <p>Selecione um card e um dev. Depois use Alocar para colocar a pessoa certa no trabalho ativo.</p>
          </section>
          <section className="tutorial-section">
            <h3>
              <Sparkles aria-hidden="true" />
              Kaizen / PDCA
            </h3>
            <p>Use pontos Kaizen para agir: planeje a mudanca, aplique, confira metricas e ajuste a proxima sprint.</p>
          </section>
          <section className="tutorial-section">
            <h3>
              <AlertTriangle aria-hidden="true" />
              Andon
            </h3>
            <p>Alertas Andon mostram risco operacional: caixa, burnout, qualidade, prazo ou oportunidade de melhoria.</p>
          </section>
          <section className="tutorial-section">
            <h3>
              <Gauge aria-hidden="true" />
              Metricas
            </h3>
            <p>Acompanhe OEE, lead time, cycle time, throughput, bugs e custo fixo antes de encerrar a sprint.</p>
          </section>
          <section className="tutorial-section">
            <h3>
              <Play aria-hidden="true" />
              Confirmacao de sprint
            </h3>
            <p>Encerrar sprint processa custos, entrega, bugs e eventos no backend. Confirme so quando estiver pronto.</p>
          </section>
        </div>

        <div className="onboarding-footer">
          <p>O jogo ja esta carregado atras deste painel. Voce pode reabrir este tutorial pela aba Tutorial.</p>
          <button className="primary-action" onClick={onDismiss} title="Fechar tutorial inicial e comecar a jogar" type="button">
            <Play aria-hidden="true" />
            Começar partida
          </button>
        </div>
      </div>
    </section>
  )
}
