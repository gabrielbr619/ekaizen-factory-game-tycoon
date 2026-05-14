# eKaizen Factory Game Tycoon

Jogo web single-player de gestao de uma software house em recuperacao. O jogador assume a operacao por 30 sprints principais e 5 sprints de estabilizacao, tentando melhorar fluxo, caixa, reputacao, qualidade e saude do time por meio de Kanban, limites de WIP, metricas de fluxo, PDCA/Kaizens, Andon e Heijunka.

O backend FastAPI e a fonte autoritativa do estado e das regras. O frontend Vite deve funcionar apenas como apresentacao e captura de comandos.

## Status honesto da entrega

Este repositorio contem uma versao integrada e jogavel do desafio. O backend FastAPI persiste partidas em SQLite, expoe os endpoints principais, processa as regras de dominio e e a fonte autoritativa do estado. O frontend Vite/React consome a API real, renderiza o jogo como primeira tela e envia comandos para o backend.

URL publica do deploy: https://promotions-technologies-pastor-wash.trycloudflare.com

Repositorio publico: https://github.com/gabrielbr619/ekaizen-factory-game-tycoon

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

## Roteiro de jogo previsto

1. Criar uma nova partida.
2. Avaliar budget, sprint, reputacao, clientes, devs e alertas Andon.
3. Puxar cards pelo Kanban respeitando o fluxo Backlog -> Analise -> Desenvolvimento -> QA -> Done.
4. Alocar devs conforme especialidade, nivel, moral e risco de bug.
5. Confirmar o fim do sprint para o backend processar progresso, custos, receita, bugs, moral, eventos e metricas.
6. A cada 5 sprints, aplicar Kaizens permanentes pelo ciclo PDCA.
7. Manter throughput estavel para capturar bonus de Heijunka.
8. Ao fim da partida, abrir o Hall of Kaizen com veredito, metricas, top Kaizens, sprint MVP, dev MVP, badges e linha do tempo.

## Decisoes tecnicas e tradeoffs

- **SQLite com snapshot serializado**: reduz risco operacional e permite persistir o estado completo rapidamente. O tradeoff e que o modelo relacional ainda nao esta normalizado; a evolucao natural seria separar partidas, cards, devs, clientes, eventos e comandos em tabelas dedicadas.
- **Backend autoritativo**: regras e calculos devem ficar no FastAPI/dominio. O frontend pode formatar valores e renderizar agrupamentos, mas nao deve calcular resultado de jogo.
- **Nginx no frontend Docker**: o container do frontend serve os arquivos estaticos e faz proxy de `/healthz` e `/games` para o backend, permitindo abrir o jogo em `http://localhost`.
- **SSE como tempo real minimo**: o endpoint `/games/{game_id}/events` existe para o canal de comunicacao em tempo real exigido pelo desafio.
- **Estado de UI local com React state**: a interface usa estado local de tela porque o fluxo e single-player, baseado em comandos e sem compartilhamento complexo entre rotas. A evolucao natural seria Zustand caso o jogo ganhe multiplas telas independentes ou cache de sessoes.
- **CI com comandos reais**: o workflow roda ruff, mypy, pytest, typecheck, testes frontend, E2E Playwright, build frontend e build Docker. Se alguma frente ainda estiver incompleta, a falha deve aparecer no pipeline em vez de ser escondida.

## Fora de escopo ou pendente

- O deploy publico atual usa um tunnel Cloudflare para expor a versao integrada localmente. Para producao real, a evolucao recomendada e publicar frontend e backend em infraestrutura persistente.
- A persistencia SQLite e relacional no arquivo de banco, mas o estado de jogo ainda e salvo como snapshot.
- Algumas regras avancadas do PDF foram simplificadas para priorizar fluxo jogavel, determinismo e separacao backend/frontend dentro do prazo.

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

## Deploy publico

Opcao simples sugerida para a entrega:

- Frontend: Vercel, Netlify ou container estatico equivalente.
- Backend: Render, Railway, Fly.io ou VPS com Docker Compose.
- Banco: SQLite em volume persistente no backend para a versao do desafio; PostgreSQL seria a evolucao recomendada para producao real.

A URL publica acima foi validada com `GET /healthz`, criacao de partida e fluxo basico do jogo.
