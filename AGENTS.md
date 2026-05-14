# AGENTS.md

## Projeto

Desafio tecnico eKaizen Factory Game Tycoon.

Objetivo: entregar ate 2026-05-14 17h um jogo web publico, jogavel e honesto, com backend FastAPI como fonte autoritativa do dominio, frontend React/Vite como apresentacao, Docker Compose, testes, README, CI e deploy publico.

Este arquivo e contrato operacional para agentes paralelos. Leia antes de editar qualquer arquivo.

## Prioridade de avaliacao

1. Os 8 conceitos de melhoria continua precisam existir de forma funcional e visivel:
   - Kanban
   - WIP Limit
   - Lead Time
   - Cycle Time
   - OEE
   - PDCA / Kaizens permanentes
   - Andon
   - Heijunka
2. O dominio precisa viver no backend.
3. A UI precisa ser compreensivel em 2 minutos.
4. Tipagem e qualidade contam muito. Nao usar atalhos que violem o enunciado.
5. README honesto vale mais que fingir escopo perfeito.

## Regras globais fortes

- Nao criar god object.
- Nao colocar regra de negocio no frontend.
- Nao duplicar regras de calculo entre frontend e backend.
- Nao usar `Any`, `cast()` ou `# type: ignore` em `backend/app/domain`.
- Nao usar `any` ou `as` no frontend, exceto `as const` quando necessario.
- Nao editar `node_modules`, `.venv`, arquivos gerados ou lockfiles sem motivo claro.
- Nao reformatar o projeto inteiro.
- Nao mudar contrato de API sem avisar no README e nos tipos do frontend.
- Nao quebrar Docker para melhorar apenas o ambiente local.
- Nao adicionar dependencia pesada sem necessidade objetiva.
- Nao implementar features cosmeticas antes do fluxo jogavel.
- Nao esconder limitacoes. O README deve dizer o que ficou simplificado.

## Estado atual importante

O projeto ja tem um rascunho inicial, mas ele ainda deve ser tratado como incompleto.

Arquivos existentes relevantes:

- `backend/app/domain/models.py`: entidades e enums do dominio.
- `backend/app/domain/engine.py`: rascunho concentrado da engine. Deve ser quebrado em modulos menores. Nao expandir esse arquivo como god object.
- `backend/app/main.py`: API FastAPI.
- `backend/app/persistence.py`: persistencia SQLite por enquanto.
- `backend/app/api/schemas.py`: contratos HTTP.
- `backend/tests/test_domain_engine.py`: testes iniciais de dominio.
- `backend/tests/test_api.py`: testes iniciais de API.
- `frontend/`: scaffold Vite ainda quase vazio.

## Divisao de agentes

Use no maximo estes agentes simultaneamente. Cada agente deve respeitar ownership e nao mexer em area de outro agente sem coordenar.

### Agente 1 - Backend Domain

Responsavel por:

- `backend/app/domain/**`
- `backend/tests/test_domain_*.py`

Missao:

- Quebrar `engine.py` em modulos pequenos.
- Implementar regras deterministicas do jogo.
- Garantir os 8 conceitos no dominio.
- Garantir seed deterministica.
- Garantir metricas: lead time, cycle time, OEE, throughput, Heijunka.
- Garantir PDCA/Kaizens com efeitos reais.
- Garantir Andon como saida do estado.

Arquitetura esperada:

- `backend/app/domain/models.py`
- `backend/app/domain/game_factory.py`
- `backend/app/domain/commands.py`
- `backend/app/domain/sprint_processor.py`
- `backend/app/domain/rules/flow.py`
- `backend/app/domain/rules/work.py`
- `backend/app/domain/rules/morale.py`
- `backend/app/domain/rules/metrics.py`
- `backend/app/domain/rules/kaizen.py`
- `backend/app/domain/rules/events.py`
- `backend/app/domain/rules/andon.py`
- `backend/app/domain/rules/verdict.py`

Proibido:

- Chamar FastAPI, SQLite, HTTP ou filesystem dentro do dominio.
- Usar dicionarios soltos para representar entidade central se existir dataclass/modelo.
- Fazer frontend.
- Fazer deploy.

Gates:

- `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_domain_*.py`
- `backend/.venv/Scripts/python.exe -m mypy backend/app/domain --strict`

### Agente 2 - Backend API + Persistence

Responsavel por:

- `backend/app/main.py`
- `backend/app/api/**`
- `backend/app/persistence.py`
- `backend/tests/test_api.py`

Missao:

- Expor API limpa para criar partida, obter estado, executar comandos e Hall of Kaizen.
- Manter sessao minima por cookie assinado.
- Manter idempotencia em toda mutacao.
- Persistir estado completo apos cada sprint.
- Expor SSE ou WebSocket funcional.
- Validar fronteira HTTP com Pydantic v2.

Proibido:

- Implementar regra de jogo na API.
- Duplicar calculo de metricas na API.
- Quebrar contratos usados pelo frontend sem atualizar `frontend/src/api`.

Gates:

- `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_api.py`
- `backend/.venv/Scripts/python.exe -m mypy backend/app --strict`

### Agente 3 - Frontend Game UI

Responsavel por:

- `frontend/src/**`
- `frontend/index.html`
- `frontend/vite.config.ts`
- `frontend/tsconfig*.json`

Missao:

- Criar UI jogavel e autoexplicativa.
- Mostrar estado geral em 5 segundos: budget, sprint, reputacao, devs, clientes, alertas.
- Implementar Kanban com colunas, WIP visivel e comandos de mover/alocar.
- Implementar painel de devs com tooltips/detalhe Gemba.
- Implementar PDCA/Kaizen, Andon, historico e Hall of Kaizen.
- Chamar backend para toda decisao.

Proibido:

- Calcular regra de dominio no cliente.
- Criar simulacao local paralela.
- Usar `any` ou `as`, exceto `as const`.
- Colocar textos longos de manual dentro da tela principal.
- Criar landing page no lugar do jogo.

Gates:

- `npm --prefix frontend run typecheck`
- `npm --prefix frontend run test`
- `npm --prefix frontend run build`

### Agente 4 - Tests + Quality

Responsavel por:

- `backend/tests/**`
- `frontend/src/**/*.test.tsx`
- `frontend/e2e/**`
- `frontend/playwright.config.ts`
- `.github/workflows/**`

Missao:

- Cobrir regras criticas do dominio.
- Cobrir componentes-chave: Kanban, painel de devs, Hall of Kaizen.
- Criar E2E minimo: criar partida -> jogar 3 sprints -> contratar dev -> aplicar Kaizen -> ver Hall.
- Criar CI com lint, typecheck e testes.

Proibido:

- "Consertar" testes relaxando regra critica sem registrar no README.
- Criar testes que so validam render generico.
- Quebrar comandos dos outros agentes.

Gates:

- Backend unit tests passam.
- Frontend unit tests passam.
- E2E passa localmente ou README explica limitacao com evidencia.
- CI executa comandos reais.

### Agente 5 - Infra + README + Deploy

Responsavel por:

- `Dockerfile`
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `docker-compose.yml`
- `README.md`
- `.dockerignore`
- `.gitignore`
- arquivos de deploy, se houver

Missao:

- Garantir `docker compose up --build` subindo backend, frontend e banco.
- Documentar portas e URL local.
- Preparar deploy publico com menor risco.
- Escrever README completo, honesto e avaliavel.
- Preparar mensagem final de envio.

Proibido:

- Mudar dominio para facilitar Docker.
- Prometer no README o que nao esta funcionando.
- Esconder falta de cobertura ou E2E.

Gates:

- `docker compose up --build` funciona.
- `README.md` tem: jogo, como rodar, URL deploy, decisoes/tradeoffs, fora de escopo, roteiro, testes.

## Ordem recomendada

1. Backend Domain entrega modelos/regras testadas.
2. Backend API estabiliza contratos.
3. Frontend consome contratos reais.
4. Tests + Quality cobre fluxo critico.
5. Infra + README fecha Docker/deploy/documentacao.

Execucao paralela permitida:

- Agente 1 e Agente 3 podem trabalhar em paralelo se Agente 3 usar mocks temporarios em `frontend/src/mocks` e remover depois.
- Agente 4 pode preparar estrutura de testes em paralelo, mas nao deve travar contratos antes da API estabilizar.
- Agente 5 pode criar Docker/README em paralelo, mas deve revisar no fim contra o estado real.

## Contratos de integracao

Backend deve expor:

- `GET /healthz`
- `POST /games`
- `GET /games/{game_id}`
- `POST /games/{game_id}/commands`
- `GET /games/{game_id}/events`
- `GET /games/{game_id}/hall-of-kaizen`

Toda mutacao deve aceitar:

- `command_id` no corpo
- `Idempotency-Key` opcional no header

Frontend deve tratar erros 400/401/404 com mensagem visivel.

## Como agentes devem reportar

Cada agente deve devolver:

- Arquivos alterados.
- Regras implementadas.
- Comandos de verificacao rodados.
- Pendencias ou riscos.
- Se tocou fora do ownership, explicar por que.

## Criterio de corte por prazo

Se faltar tempo, cortar nesta ordem:

1. Animacoes e polimento visual extra.
2. Eventos aleatorios raros.
3. God-tier detalhado.
4. Todos os tipos de Kaizen completos.
5. E2E robusto.

Nao cortar:

- 8 conceitos funcionais.
- Backend autoritativo.
- README honesto.
- Docker.
- Deploy publico.
- Fluxo jogavel basico.

