# Requisitos de entrega extraidos do PDF

Fonte: `C:\Users\gabri\Downloads\desafio-tecnico-ekaizen-factory-game-tycoon.pdf`.

Este documento resume os pontos que afetam README, arquitetura, testes e processo. O PDF continua sendo a fonte de verdade.

## Entregaveis

- Repositorio publico com a versao final na `main`.
- `README.md` completo com apresentacao, Docker Compose, URL publica, decisoes/tradeoffs, fora de escopo, roteiro de jogo e testes.
- Dockerfile do backend.
- Dockerfile do frontend.
- `docker-compose.yml` que sobe backend, frontend e banco com um unico `docker compose up`.
- Jogo acessivel em `http://localhost` apos Docker Compose.
- Deploy publico funcional e ativo no momento da avaliacao.
- Mensagem final curta, em um paragrafo, com ponto forte e ponto fraco da entrega.

## Arquitetura obrigatoria

- Backend Python 3.11+ com FastAPI.
- Frontend React 18+ com Vite e TypeScript strict.
- Persistencia em banco relacional: SQLite, PostgreSQL ou MariaDB.
- Servidor e fonte autoritativa de estado, decisoes e calculos.
- Frontend apenas apresenta estado e captura comandos.
- Estado completo da partida persistido apos cada sprint processado.
- RNG deterministico no servidor a partir de seed da partida.
- Autenticacao minima de sessao por cookie assinado ou token.
- Endpoint `/healthz`.
- Canal de tempo real por WebSocket ou Server-Sent Events.
- Mutacoes idempotentes com identificador unico de comando por header ou campo.

## Regras de jogo que afetam arquitetura

- 30 sprints principais e 5 sprints de estabilizacao.
- Kanban sequencial: Backlog -> Analise -> Desenvolvimento -> QA -> Done.
- Nao pode pular colunas.
- Nao pode ir de Desenvolvimento direto para Done.
- WIP e bloqueado pelo sistema.
- QA roda no fim do sprint para cards na coluna QA.
- Bug detectado em QA volta para Desenvolvimento sem penalidade ao cliente.
- Bug nao detectado pode emergir 1 a 3 sprints depois como bug em producao.
- Cards em Done geram pagamento.
- Eventos aleatorios devem ser anunciados via Andon antes de o jogador confirmar o sprint.

## Oito conceitos eliminatorios

Todos devem ser funcionais, visiveis e afetar jogabilidade:

- Kanban.
- WIP Limit.
- Lead Time.
- Cycle Time.
- OEE.
- PDCA.
- Andon.
- Heijunka.

A implementacao apenas cosmetica de qualquer um deles invalida a entrega.

## UX obrigatoria

- O jogo deve ser compreensivel em ate 2 minutos sem documentacao externa.
- Todo dev tem nome proprio.
- Tooltips em elementos interativos importantes.
- Estado geral visivel rapidamente na tela principal.
- Alertas Andon criticos devem ser dificeis de ignorar sem poluir a tela.
- Decisoes irreversiveis exigem confirmacao.
- Tutorial/onboarding nos primeiros sprints.
- Feedback claro apos cada acao.
- Historico da partida acessivel.
- UI responsiva minima para desktop 1280x720.

## Testes e pipeline

- Backend: pytest.
- Cobertura minima de 70% nas regras de dominio.
- Casos criticos: OEE, processamento de sprint, Lei de Brooks, drenagem de moral, geracao de eventos.
- Frontend: Vitest + React Testing Library para Kanban, painel de devs e Hall of Kaizen.
- E2E: fluxo criar partida -> jogar 3 sprints -> contratar dev -> aplicar Kaizen -> ver Hall of Kaizen.
- Lint e typecheck em pipeline.
- CI a cada push.

## Processo

- Commits incrementais e descritivos.
- Branch `main` sempre deployavel.
- Historico de commits sera analisado para avaliar evolucao do raciocinio.
- README deve declarar tradeoffs e fora de escopo com honestidade tecnica.
- Nao prometer URL publica sem validacao real.
