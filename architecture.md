# architecture.md

## Objetivo arquitetural

Construir uma entrega enxuta, testavel e profissional para o desafio eKaizen Factory Game Tycoon.

O projeto deve demonstrar modelagem de dominio, separacao de camadas, tipagem rigorosa, produto jogavel e capacidade de priorizacao sob prazo curto.

## Decisao central

O backend e a fonte autoritativa do jogo.

O frontend nao calcula regra de negocio. Ele renderiza estado, envia comandos e mostra feedback.

## Stack alvo

Backend:

- Python 3.11+
- FastAPI
- Pydantic v2 em fronteiras HTTP
- SQLite como banco relacional para reduzir risco operacional no prazo
- pytest
- mypy strict
- ruff

Frontend:

- React 18+ ou 19 via Vite
- TypeScript strict
- Zustand ou Context para estado de UI/API
- Zod somente para validacao/narrowing de resposta externa, se necessario
- Vitest + React Testing Library
- Playwright para E2E

Infra:

- Dockerfile backend
- Dockerfile frontend
- docker-compose.yml
- CI com lint, typecheck e testes
- Deploy publico simples como gate de entrega, sem automacao de deploy neste documento

## Camadas

### Backend Domain

Pasta: `backend/app/domain`

Contem:

- Entidades do jogo.
- Regras de progresso.
- Regras de moral/burnout.
- Regras de Kanban/WIP.
- Regras de bugs/QA/Jidoka.
- Regras de PDCA/Kaizen.
- Regras de Andon.
- Regras de metricas.
- Regras de vitoria/derrota.

Nao contem:

- FastAPI.
- SQLite.
- Pydantic HTTP.
- Cookies.
- JSON.
- Requests/responses.
- Arquivos.

### Backend Application/API

Pasta: `backend/app/api` e `backend/app/main.py`

Contem:

- Endpoints HTTP.
- Schemas Pydantic de entrada.
- Conversao de excecoes de dominio para HTTP.
- Sessao minima.
- Idempotencia.
- SSE em `/games/{game_id}/events`.

Nao contem:

- Calculo de OEE.
- Processamento de sprint.
- Regras de Kaizen.
- Regras de WIP.

### Persistence

Arquivo/pasta: `backend/app/persistence.py` ou `backend/app/persistence/**`

Contem:

- Salvamento e carregamento de partidas.
- Registro de comandos idempotentes.
- Inicializacao de tabelas.
- Persistencia do estado completo apos cada sprint processado.

Nao contem:

- Regras de dominio.
- Decisoes de UI.

### Frontend

Pasta: `frontend/src`

Contem:

- Componentes de apresentacao.
- Estado de tela.
- Cliente HTTP.
- Feedback visual.
- Acessibilidade.

Nao contem:

- Calculo de sprint.
- RNG.
- Taxa de bug.
- OEE real.
- Lead time/cycle time real.
- WIP enforcement real.

O frontend pode formatar valores recebidos, agrupar cards por coluna e escolher cores/labels.

## Regra anti-god-object

Nenhum arquivo deve acumular responsabilidades heterogeneas.

Limites praticos:

- `backend/app/domain/engine.py` nao deve crescer. Ele deve virar fachada fina ou desaparecer.
- Qualquer arquivo de dominio com mais de 250 linhas deve ser revisado para split.
- Qualquer funcao com mais de 50 linhas deve ser revisada.
- Qualquer funcao que altera budget, moral, card, cliente e metrica ao mesmo tempo provavelmente precisa ser dividida.

Split recomendado do dominio:

- `models.py`: dataclasses/enums puros.
- `game_factory.py`: criacao de partida, seed inicial, pools iniciais.
- `commands.py`: funcoes de comando publico do dominio.
- `sprint_processor.py`: orquestracao de fim de sprint.
- `rules/flow.py`: Kanban, WIP, movimento de cards.
- `rules/work.py`: alocacao, Brooks, progresso.
- `rules/morale.py`: moral, burnout, demissao.
- `rules/bugs.py`: QA, bug em producao, Jidoka.
- `rules/metrics.py`: lead time, cycle time, OEE, throughput.
- `rules/kaizen.py`: PDCA e Kaizens.
- `rules/events.py`: eventos aleatorios deterministico por seed.
- `rules/andon.py`: alertas visuais.
- `rules/verdict.py`: vitoria, sobrevivencia, falencia.

## Contrato de dominio

Comandos de dominio devem ser funcoes puras ou quase puras que recebem `GameState` e retornam `GameState` mutado ou novo.

Comandos principais:

- `create_game(seed: int | None) -> GameState`
- `move_card(game, card_id, target_column) -> GameState`
- `allocate_dev(game, dev_id, card_id | None) -> GameState`
- `hire_candidate(game, candidate_id) -> GameState`
- `apply_kaizen(game, kaizen, target_id | None) -> GameState`
- `process_sprint(game) -> GameState`
- `build_hall_of_kaizen(game) -> HallOfKaizen`

Se uma regra precisa de aleatoriedade, ela deve receber RNG derivado de `game.seed` + `game.sprint` + contexto deterministico.

## Persistencia

Escolha atual: SQLite.

Motivo:

- Atende banco relacional.
- Roda facil em Docker.
- Reduz risco de deploy e compose.
- Permite foco em dominio e experiencia.

Formato aceitavel no prazo:

- Tabela `games` com `id` e estado serializado.
- Tabela `commands` para idempotencia.

README deve assumir tradeoff: persistencia relacional existe, mas o estado de jogo e salvo como snapshot para cumprir prazo e manter determinismo. Evolucao ideal seria normalizar entidades principais.

## API

Endpoints obrigatorios internos do projeto:

- `GET /healthz`
- `POST /games`
- `GET /games/{game_id}`
- `POST /games/{game_id}/commands`
- `GET /games/{game_id}/events`
- `GET /games/{game_id}/hall-of-kaizen`

Toda mutacao passa por `POST /games/{game_id}/commands`.

Payload padrao:

```json
{
  "command_id": "uuid-ou-string-unica",
  "payload": {
    "type": "process-sprint"
  }
}
```

Idempotencia:

- Se `command_id` ou `Idempotency-Key` repetir, retornar exatamente o mesmo estado salvo.
- Nao reprocessar sprint em retry.
- Persistir a resposta associada ao comando para que retry de rede seja seguro.

Sessao:

- Cookie assinado simples e suficiente para desafio.
- Nao implementar login completo.

Tempo real:

- O canal escolhido e Server-Sent Events em `GET /games/{game_id}/events`.
- SSE e usado para observabilidade de eventos/atualizacoes do jogo.
- Mutacoes continuam em HTTP por `POST /games/{game_id}/commands`, mantendo idempotencia e backend autoritativo.

## Fluxo autoritativo de sprint

O backend e a unica fonte de verdade para estado, RNG, calculos e decisao de resultado.

Fluxo esperado:

1. Frontend envia comandos de preparacao: mover card, alocar dev, contratar, aplicar Kaizen ou encerrar sprint.
2. API valida sessao, payload e idempotencia.
3. Dominio aplica a regra de comando no `GameState`.
4. Ao processar sprint, o dominio calcula progresso, custos, receitas, moral, eventos, bugs, metricas e condicoes finais.
5. Cards em QA passam pela checagem de qualidade no fechamento da sprint.
6. Card aprovado em QA vai para Done e gera pagamento.
7. Bug detectado em QA volta para Desenvolvimento sem penalidade ao cliente.
8. Bug nao detectado pode emergir 1 a 3 sprints depois como bug em producao, aplicar penalidade e voltar ao Backlog como BUG.
9. Estado completo e resposta idempotente sao persistidos.
10. API devolve o novo estado e SSE pode expor o evento para a UI.

Consequencias arquiteturais:

- Nao existe comando frontend confiavel para mover Desenvolvimento direto para Done.
- Nao existe calculo de resultado no cliente.
- WIP e fluxo sequencial sao bloqueados no dominio, mesmo que a UI tente uma acao invalida.
- Eventos sao parte do estado de jogo, nao apenas mensagens cosmeticas.

## Frontend UX

Primeira tela deve ser o jogo, nao landing page.

Layout recomendado:

- Top bar: sprint, fase, budget, lucro, reputacao geral, pontos Kaizen.
- Andon: alertas criticos sempre visiveis.
- Main: Kanban com Backlog, Analise, Desenvolvimento, QA, Done.
- Sidebar: Devs, candidatos, PDCA/Kaizens, clientes.
- Bottom/aside: Historico e metricas.
- Hall of Kaizen: view/tela acessivel quando jogo encerra ou botao de preview.

Regras visuais:

- WIP limit aparece no titulo de cada coluna.
- Cards mostram tipo, tamanho, prazo, valor, progresso e cliente.
- Devs mostram nome real, avatar, especialidade, nivel, moral e salario.
- Tooltips ou paineis de detalhe para dev/card/metrica.
- Acao irreversivel pede confirmacao.
- Feedback de comando aparece apos toda acao.

## 8 conceitos e onde vivem

Kanban:

- Dominio: coluna do card e movimento sequencial.
- UI: quadro principal.

WIP Limit:

- Dominio: bloqueia movimento acima do limite.
- UI: mostra limite e ocupacao.

Lead Time:

- Dominio: calcula do Backlog ao Done.
- UI: painel de metricas.

Cycle Time:

- Dominio: tempo por coluna.
- UI: detalhe de card/metrica.

OEE:

- Dominio: disponibilidade x performance x qualidade.
- UI: painel principal e Hall.

PDCA:

- Dominio: pontos a cada 5 sprints e Kaizens permanentes.
- UI: painel Kaizen com efeitos.

Andon:

- Dominio: lista de alertas a partir do estado.
- UI: faixa visual de alertas.

Heijunka:

- Dominio: bonus por throughput constante.
- UI: metrica/streak/bonus financeiro.

## Testes minimos obrigatorios

Backend:

- `test_kanban_blocks_invalid_jump`
- `test_wip_limit_blocks_overflow`
- `test_brooks_law_reduces_linear_gain`
- `test_morale_drains_and_rest_space_helps`
- `test_oee_calculation`
- `test_heijunka_bonus_requires_consistency`
- `test_idempotent_command_returns_same_state`
- `test_seed_reproduces_initial_state`

Frontend:

- Kanban renderiza colunas e WIP.
- Painel de devs renderiza nome, moral e especialidade.
- Hall of Kaizen renderiza veredito e metricas.

E2E:

- Criar partida.
- Mover/alocar card.
- Processar 3 sprints.
- Contratar dev.
- Aplicar Kaizen.
- Abrir Hall of Kaizen.

## Commits e processo

Quando o projeto virar repo git:

- Fazer commits frequentes.
- Usar mensagens claras:
  - `feat(domain): model factory game state`
  - `feat(api): add idempotent game commands`
  - `feat(ui): build kanban board`
  - `test(domain): cover oee and heijunka`
  - `docs: explain tradeoffs and runbook`

Nao fazer um commit unico gigante se houver tempo.

## Tradeoffs aceitos

Aceitos se documentados:

- Snapshot em SQLite relacional em vez de schema altamente normalizado para cada entidade do jogo.
- Tabela de comandos idempotentes em vez de event sourcing completo.
- SSE em vez de WebSocket bidirecional, porque os comandos continuam por HTTP idempotente.
- QA resolvido no fechamento da sprint em vez de um comando manual separado de aprovacao.
- Eventos aleatorios com respostas agregadas por Andon/decisao de sprint, desde que afetem o jogo e nao sejam cosmeticos.
- God-tier implementado como raridade e alto impacto dentro do sistema de devs, mesmo que futuras versoes ampliem regras especificas de retencao.
- Drag and drop substituido por botoes acessiveis de mover, se o fluxo for claro.
- Deploy com SQLite em volume persistente para o desafio; SQLite efemero so e aceitavel em ambiente local/teste, nao como promessa de entrega publica.

Nao aceitos:

- Frontend fake sem backend real.
- README prometendo features ausentes.
- 8 conceitos apenas cosmeticos.
- Engine central gigante sem separacao.
- Falta de Docker.
- README prometendo URL publica sem validacao.
- Automatizar deploy sem tarefa explicita.

## Mensagem final de envio

A mensagem ao avaliador deve ter no maximo um paragrafo e seguir este modelo:

```text
Segue o repositorio e a URL publica validada do desafio. O ponto forte da entrega e a modelagem autoritativa no backend: Kanban, WIP, Lead/Cycle Time, OEE, PDCA, Andon e Heijunka afetam a jogabilidade, com comandos idempotentes, SSE e testes no pipeline. O principal tradeoff e persistir o estado do jogo como snapshot em SQLite relacional, em vez de normalizar todas as entidades, para preservar determinismo e reduzir risco operacional dentro do prazo sem abrir mao dos requisitos do PDF.
```
