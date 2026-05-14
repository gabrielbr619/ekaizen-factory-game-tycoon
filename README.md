# eKaizen Factory Game Tycoon

Jogo web single-player de gestao de uma software house em recuperacao. O jogador assume a operacao por 30 sprints principais e 5 sprints de estabilizacao, tentando melhorar fluxo, caixa, reputacao, qualidade e saude do time por meio de Kanban, limites de WIP, metricas de fluxo, PDCA/Kaizens, Andon e Heijunka.

O backend FastAPI e a fonte autoritativa do estado e das regras. O frontend Vite deve funcionar apenas como apresentacao e captura de comandos.

## Status honesto da entrega

Este repositorio contem uma versao integrada e jogavel do desafio. O backend FastAPI persiste partidas em SQLite, expoe os endpoints principais, processa as regras de dominio e e a fonte autoritativa do estado. O frontend Vite/React consome a API real, renderiza o jogo como primeira tela e envia comandos para o backend.

URL publica do deploy: nao declarada neste README ate validacao final em ambiente publico. O PDF exige uma URL publica funcional no envio; este repositorio nao deve prometer uma URL sem healthcheck, criacao de partida e fluxo basico validados na propria URL.

Repositorio publico: https://github.com/gabrielbr619/ekaizen-factory-game-tycoon

## Como rodar localmente sem Docker

Backend:

```bash
cd backend
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

URLs locais:

- Frontend: http://127.0.0.1:5173
- Backend: http://127.0.0.1:8000
- Healthcheck: http://127.0.0.1:8000/healthz

## Como rodar com Docker Compose

Pre-requisitos:

- Docker Desktop ou Docker Engine com Docker Compose v2.

Subir tudo:

```bash
docker compose up --build
```

URLs locais:

- Frontend: http://localhost
- Backend direto: http://localhost:8000
- Healthcheck: http://localhost/healthz ou http://localhost:8000/healthz

O banco local usa SQLite em um volume Docker nomeado (`factory_game_data`). Para zerar a persistencia local:

```bash
docker compose down -v
```

## API esperada

O contrato atual do backend cobre:

- `GET /healthz`
- `POST /games`
- `GET /games/{game_id}`
- `POST /games/{game_id}/commands`
- `GET /games/{game_id}/events`
- `GET /games/{game_id}/hall-of-kaizen`

Mutações passam por `POST /games/{game_id}/commands` com `command_id` no corpo e aceitam `Idempotency-Key` no header. O backend usa cookie de sessao assinado para proteger o acesso a uma partida criada.

O endpoint de eventos usa Server-Sent Events como canal minimo de tempo real. Ele existe para notificacoes e atualizacoes observaveis da partida; nao substitui o contrato de comandos idempotentes.

## Roteiro de jogo previsto

1. Criar uma nova partida.
2. Avaliar budget, sprint, reputacao, clientes, devs e alertas Andon.
3. Puxar cards pelo Kanban respeitando o fluxo Backlog -> Analise -> Desenvolvimento -> QA; a ida para Done acontece no fechamento da sprint, depois da checagem de QA.
4. Alocar devs conforme especialidade, nivel, moral e risco de bug.
5. Confirmar o fim do sprint para o backend processar progresso, custos, receita, bugs, moral, eventos e metricas.
6. A cada 5 sprints, aplicar Kaizens permanentes pelo ciclo PDCA.
7. Manter throughput estavel para capturar bonus de Heijunka.
8. Ao fim da partida, abrir o Hall of Kaizen com veredito, metricas, top Kaizens, sprint MVP, dev MVP, badges e linha do tempo.

## Decisoes tecnicas e tradeoffs

- **SQLite com snapshot serializado**: o PDF exige persistencia em banco relacional e persistencia do estado completo apos cada sprint; SQLite atende o requisito relacional e o snapshot preserva determinismo com baixo risco operacional. O tradeoff e nao normalizar `cards`, `devs`, `clientes`, `eventos` e `metricas` em tabelas proprias nesta versao. Isso nao fere o PDF porque o requisito e persistir em banco relacional, nao impor um modelo normalizado.
- **Tabela de comandos para idempotencia**: comandos mutantes usam identificador unico e/ou `Idempotency-Key` para evitar reprocessar retries. O tradeoff e guardar a resposta idempotente em vez de montar uma fila/event store completa. Isso atende o PDF porque retentativas devem produzir o mesmo resultado, nao necessariamente exigir event sourcing.
- **Backend autoritativo**: regras, RNG, WIP, processamento de sprint, bugs, OEE, vitoria/derrota e pagamentos ficam no backend. O frontend formata valores, agrupa cards por coluna e gerencia estado de tela. Isso e requisito direto do PDF, nao tradeoff.
- **QA -> Done no fechamento da sprint**: o jogador move cards ate QA; a passagem para Done acontece durante `process-sprint`, depois da checagem de qualidade. O tradeoff e nao permitir um comando manual "aprovar QA" separado. Isso preserva o PDF porque QA roda no fim do sprint e bug detectado retorna para Dev sem penalidade.
- **SSE como canal de tempo real**: `/games/{game_id}/events` cobre o requisito de WebSocket ou Server-Sent Events. O tradeoff e usar fluxo unidirecional servidor -> cliente, suficiente para alertas/atualizacoes, enquanto comandos continuam por HTTP idempotente.
- **Estado de UI local com React state**: a interface usa estado local de tela porque o jogo e single-player, baseado em comandos e sem multiplas rotas complexas. O tradeoff e nao introduzir store global mais pesada para esta versao. Isso nao fere o PDF porque ele exige gerenciamento coerente de estado, nao uma biblioteca especifica.
- **Balanceamento documentado**: regras numericas explicitas do PDF foram preservadas. Parametros abertos, como receita recorrente por cliente ativo, ganho de reputacao por entrega limpa e rampa de demanda por estagio, estao justificados em `docs/BALANCING.md`.
- **Nginx no frontend Docker**: o container do frontend serve os arquivos estaticos e faz proxy de `/healthz` e `/games` para o backend, permitindo abrir o jogo em `http://localhost` com `docker compose up`.
- **CI com comandos reais**: o workflow roda ruff, mypy, pytest, typecheck, testes frontend, E2E Playwright, build frontend e build Docker. Se alguma frente estiver incompleta, a falha deve aparecer no pipeline em vez de ser escondida.

## Fora de escopo ou pendente

- **URL publica validada**: o PDF exige URL publica funcional no envio. Este README nao declara uma URL ate que ela seja validada com healthcheck, criacao de partida e fluxo basico online.
- **Modelo relacional normalizado**: a persistencia usa SQLite relacional com snapshot de estado e comandos idempotentes. A evolucao natural e normalizar partidas, cards, devs, clientes, eventos e comandos para consultas analiticas mais ricas.
- **Eventos aleatorios com efeitos agregados**: cliente urgente, indicacao, bug retroativo, pedido de aumento, auditoria OEE e tendencia de mercado alteram o estado da partida e aparecem via Andon/historico. O tradeoff e que algumas respostas ainda sao agregadas no processamento de sprint, em vez de comandos dedicados para cada evento.
- **Drag and drop completo**: comandos por botoes acessiveis sao aceitaveis quando o fluxo e claro e enviado ao servidor. A evolucao natural e adicionar drag and drop preservando os mesmos comandos backend.

## Como rodar verificacoes locais

Backend:

```bash
cd backend
pip install -r requirements-dev.txt
ruff check app tests
mypy app --strict
pytest tests
```

Frontend:

```bash
cd frontend
npm ci
npm run typecheck
npm run test
npm run e2e
npm run build
```

Docker:

```bash
docker compose config
docker compose build
```

A auditoria de aderencia dos gates de teste/CI ao PDF esta em `docs/TEST_AUDIT.md`.

## Entrega publica

O PDF exige que o envio final inclua uma URL publica funcional. Como este documento nao valida deploy, a URL deve ser preenchida somente apos verificacao real.

Opcoes simples para a entrega:

- Frontend: Vercel, Netlify ou container estatico equivalente.
- Backend: Render, Railway, Fly.io ou VPS com Docker Compose.
- Banco: SQLite em volume persistente no backend para a versao do desafio; PostgreSQL seria a evolucao recomendada para producao real.

A URL publica deve ser validada com `GET /healthz`, criacao de partida e fluxo basico do jogo antes da entrega final.
