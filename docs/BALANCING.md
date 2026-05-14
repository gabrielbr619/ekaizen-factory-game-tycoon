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

Valor atual: `+50` de reputacao para o cliente do card entregue.

Justificativa: o PDF define que reputacao sobe ao entregar cards no prazo sem bug, mas nao fixa o valor positivo. As penalidades negativas sao altas e explicitas (`-15` por sprint atrasado, `-25` no cancelamento e `-20` por bug em producao), entao a recompensa positiva precisa ser forte o suficiente para tornar entrega limpa uma estrategia real.

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

### Rodada anterior, antes dos eventos avancados recentes

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

### Revalidacao apos eventos avancados e regras de retencao

Em 2026-05-14, uma nova simulacao heuristica foi executada contra o motor real do backend por meio de `backend/scripts/balance_simulation.py`. O bot:

- joga seeds deterministicas usando `create_game`, `move_card`, `allocate_dev`, `hire_candidate`, `apply_kaizen` e `process_sprint`;
- prioriza nao lotar WIP, puxa cards por valor/prazo/risco, cobre especialidades faltantes por contratacao e respeita a regra de card G para nao depender de Junior/Pleno sem Senior+;
- usa Kaizens para descanso, treino, QA automation, marketing, DevOps culture e aumento de WIP quando ha pontos e risco operacional;
- evita contratar Senior/God-tier cedo demais quando o caixa nao suporta o risco de retencao e pedido de aumento.

Resultado principal antes da ultima correcao de balanceamento:

```text
seeds 500
master-kaizen 0
survived 0
bankrupt 500
best seed 279
verdict bankrupt
sprint 14
budget R$ 35.320
accumulated_profit R$ 29.160
reputation 16
active_clients 1
active_devs 5
min_moral 7
delivered_cards 3
throughput R$ 38.000
average_oee 0.730
kaizens rest-space 1, train-dev 1
```

Medias da rodada:

```text
budget R$ 3.805,40
accumulated_profit R$ -1.952,52
reputation 5,77
active_clients 0,94
active_devs 5,36
min_moral 35,72
delivered_cards 2,16
throughput R$ 5.444
```

Sinais de causa raiz observados na amostra:

- 325/500 falencias aconteceram ainda com budget positivo, indicando que a derrota esta vindo principalmente por reputacao/clientes, nao por caixa.
- 486/500 falencias terminaram com reputacao geral abaixo de 20.
- As mortes se concentraram cedo: sprints 13, 14, 15 e 16 concentraram a maior parte das quebras.
- Cada partida recebeu em media 23,2 eventos mutantes antes de falir, 4,52 cancelamentos de card, 2,06 cancelamentos de cliente e 2,38 saidas por pedido de aumento.
- O melhor seed tinha lucro acumulado suficiente para vitoria, mas faliu por reputacao 16 antes de chegar ao periodo de estabilizacao.

Controle isolado sem eventos aleatorios, mantendo o restante do dominio:

```text
seeds 500
master-kaizen 0
survived 12
bankrupt 488
best seed 324
verdict survived
sprint 36
budget R$ 37.900
accumulated_profit R$ 31.900
reputation 68
active_clients 3
active_devs 5
min_moral 13
delivered_cards 16
throughput R$ 40.000
```

Essa rodada de controle nao prova que o jogo base esta bem balanceado; ela mostra que os eventos avancados sem ponderacao adequada transformavam uma simulacao ja dificil em uma simulacao sem caminho observado de sobrevivencia ou Master Kaizen para o bot.

### Revalidacao apos correcoes de conformidade PDF e ponderacao

Depois das correcoes de conformidade do PDF, os eventos obrigatorios cobertos sao:

- Cliente urgente com prazo de 2 sprints.
- Pedido de aumento com prazo de 2 sprints.
- Bug retroativo.
- Headhunter em Senior/God-tier.
- Conferencia com +20 moral e 1 sprint improdutivo.
- Auditoria de OEE que cancela 1 cliente se OEE medio ficar abaixo de 50%.
- Tendencia de mercado por 5 sprints.
- Indicacao com candidato a salario 20% menor.

O RNG continua disparando 1 a 3 eventos por sprint, mas usa pesos por estagio para evitar que eventos destrutivos dominem a fase inicial. Eventos de oportunidade, como indicacao e conferencia, aparecem com peso maior; eventos severos entram com peso menor e/ou depois de a empresa ter algum tempo de reacao.

Resultado atual de referencia, revalidado em 2.000 seeds:

```text
seeds 2000
master-kaizen 17
survived 155
bankrupt 1828
best seed 1580
verdict master-kaizen
sprint 36
budget R$ 76.500
accumulated_profit R$ 69.800
reputation 85
active_clients 2
active_devs 6
min_moral 49
delivered_cards 17
throughput R$ 100.000
kaizens marketing 1, rest-space 1, train-dev 2, wip-increase 1
```

Medias atuais:

```text
budget R$ 2.283,57
accumulated_profit R$ -4.026,49
reputation 27,40
active_clients 1,11
active_devs 6,03
min_moral 33,76
delivered_cards 6,73
throughput R$ 22.842
```

A conclusao operacional e que o jogo segue dificil, mas nao esta mais sem caminho observado: a simulacao heuristica encontrou sobrevivencias e Master Kaizen mantendo os numeros fixos do PDF. O objetivo nao e garantir vitoria media, e sim permitir que boas decisoes de fluxo, qualidade, contratacao e Kaizen tenham impacto mensuravel.

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
