# Balanceamento e aderencia ao PDF

Este documento registra as decisoes de balanceamento tomadas para manter o jogo dificil, mas vencivel, sem alterar regras explicitas do PDF do desafio.

## Principio

O PDF e a fonte de verdade das regras. Quando o PDF define um numero ou comportamento, o codigo deve seguir esse valor. Quando o PDF descreve um conceito sem fixar numero exato, o projeto usa parametros documentados para balancear a experiencia.

## Regras fixas preservadas

- Budget inicial: R$ 8.000.
- Custo fixo operacional: R$ 2.000 por sprint.
- Time inicial: 3 devs, com 1 pleno e 2 juniors.
- Pontos de Kaizen inicial: 0.
- Fluxo Kanban sequencial: Backlog -> Analise -> Desenvolvimento -> QA; Done e liberado pelo processamento da sprint apos a checagem de qualidade.
- WIP inicial: Backlog 10, Analise 3, Desenvolvimento 5, QA 3, Done infinito.
- Tamanhos de card:
  - P: 8 pts, R$ 2.000, 4 sprints.
  - M: 25 pts, R$ 6.000, 6 sprints.
  - G: 60 pts, R$ 15.000, 10 sprints.
- Distribuicao de tamanho: 50% P, 35% M, 15% G.
- Penalidade por atraso: -15 de reputacao por sprint apos deadline.
- Apos 3 sprints atrasado, o card e cancelado e o cliente perde mais 25 de reputacao.
- Bug em producao: -20 de reputacao.
- Derrota por budget abaixo de -R$ 5.000 por 3 sprints consecutivos.
- Derrota por zero clientes ativos, reputacao geral abaixo de 20 ou zero devs ativos.
- Vitoria plena apos sprint 35 exige lucro acumulado >= R$ 20.000, reputacao geral >= 70, ao menos 5 devs ativos e nenhum dev ativo com moral abaixo de 30.

## Correcoes de regra feitas por aderencia ao PDF

- PO e a especialidade correta para a coluna Analise.
- QA e a especialidade correta para a coluna QA.
- Frontend, Backend, DevOps e Fullstack trabalham na coluna Desenvolvimento.
- O card so pode avancar depois de concluir o trabalho da coluna atual.
- Ao concluir um card em QA sem bug bloqueante no fechamento da sprint, o card vai para Done e a empresa recebe o pagamento do card.
- Bug nao detectado em QA e entregue para Done; depois de 1 a 3 sprints ele reaparece como bug em producao, aplica -20 de reputacao ao cliente e volta ao Backlog como card BUG.
- Cliente com reputacao abaixo de 30 nao cancela imediatamente; o cancelamento acontece no sprint seguinte.
- O cancelamento de card apos 3 sprints atrasado foi implementado explicitamente.

## Parametros abertos pelo PDF

O PDF nao fixa todos os numeros abaixo. Eles existem para tornar a partida jogavel sem contrariar as regras obrigatorias.

### Receita recorrente por cliente ativo

Valor atual: `R$ 1.700` por cliente ativo por sprint.

Justificativa: o PDF afirma que, quando um cliente cancela, "receita recorrente e perdida", mas nao define o valor dessa receita. Sem receita recorrente, a empresa depende apenas de pagamento por card e quase sempre entra em falencia antes de o lead time natural do Kanban gerar caixa.

### Ganho de reputacao por entrega limpa

Valor atual: `+20` de reputacao para o cliente do card entregue.

Justificativa: o PDF define que reputacao sobe ao entregar cards no prazo sem bug, mas nao fixa o valor positivo. As penalidades negativas sao altas e explicitas (`-15` por sprint atrasado e `-20` por bug em producao), entao a recompensa positiva precisa ser forte o suficiente para tornar entrega limpa uma estrategia real.

### Geração de demanda por estagio

Parametros atuais:

- Estado inicial: 2 cards no Backlog.
- Recovery ate sprint 20: 1 card novo a cada 3 sprints.
- Recovery final ate sprint 30: 1 card novo a cada 2 sprints.
- Stabilization apos sprint 30: 1 card novo por sprint.

Justificativa: o PDF diz que cards sao gerados pseudo-aleatoriamente a cada sprint conforme parametros do estagio do jogo. Ele nao fixa a quantidade por sprint. A rampa evita que o jogo mate o jogador por volume automatico antes que o jogador tenha recursos, Kaizens e contratacoes para estabilizar o fluxo.

### Mix de tipo de card no inicio

Na fase inicial, cards de infra/hotfix aparecem com menor frequencia. A distribuicao de tamanho P/M/G permanece a do PDF.

Justificativa: o time inicial nao possui DevOps nem Frontend dedicado. O PDF permite que a empresa comece em crise, mas a primeira fase precisa dar ao jogador tempo para contratar e aplicar Kaizens antes de aumentar a variedade de especialidades.

## Evidencia de jogabilidade

Antes do balanceamento, um bot que seguia a melhor heuristica disponivel testou 200 seeds e encontrou:

- 0 vitorias.
- 0 sobrevivencias.
- 200 falencias.

Depois das correcoes e do balanceamento dentro dos parametros abertos pelo PDF, um bot conservador conseguiu vencer algumas seeds em 500 tentativas. Isso nao prova que o bot joga perfeitamente; prova que o jogo deixou de ser matematicamente impossivel e passou a ter um caminho de vitoria.

Resultado de referencia:

```text
conservative wins 5
surv 13
bank 482
best seed 431
verdict master-kaizen
sprint 36
budget R$ 65.600
accumulated_profit R$ 58.600
reputation 85
active_clients 2
active_devs 5
min_moral 50
delivered_cards 10
throughput R$ 32.000
```

## Estrategia recomendada de jogo

- Nao encher Analise nem Desenvolvimento so porque existe WIP disponivel.
- Puxar poucos cards e proteger prazo.
- Priorizar cards de maior valor quando houver tempo suficiente.
- Contratar para cobrir Frontend/DevOps/Fullstack, mas evitar folha alta cedo demais.
- Usar Kaizen de descanso quando moral cair.
- Usar QA Automation para reduzir risco de bug depois que o fluxo estiver ativo.
- Usar Marketing quando clientes estiverem perto de cancelar ou a reputacao geral estiver em risco.

## Decisoes evitadas

Estas alternativas foram consideradas e rejeitadas por serem interpretacoes mais arriscadas do PDF:

- Fazer o deadline comecar apenas quando o card sai do Backlog.
- Ignorar atraso de cards ainda em Backlog.
- Alterar Budget inicial, custo fixo, penalidades de atraso ou criterios de derrota/vitoria.
- Remover a necessidade de passar por QA.
