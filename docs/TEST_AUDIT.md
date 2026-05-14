# Auditoria de testes e CI

Fonte normativa: `C:\Users\gabri\Downloads\desafio-tecnico-ekaizen-factory-game-tycoon.pdf`, secao 8.5.

Este documento registra a auditoria final de gates nao-deploy. Ele nao declara URL publica, deploy, VPS ou ambiente de producao.

## Gates exigidos pelo PDF

| Requisito | Cobertura atual |
| --- | --- |
| Backend pytest | `.github/workflows/ci.yml` executa `pytest tests` em `backend`. |
| Cobertura minima de 70% em regras de dominio | `backend/pyproject.toml` aplica `--cov=app.domain --cov-fail-under=70`. |
| Ruff | `.github/workflows/ci.yml` executa `ruff check app tests`. |
| Mypy strict | `.github/workflows/ci.yml` executa `mypy app --strict`. |
| Frontend typecheck | `.github/workflows/ci.yml` executa `npm run typecheck`. |
| Frontend unit tests | `.github/workflows/ci.yml` executa `npm run test`. |
| Frontend build | `.github/workflows/ci.yml` executa `npm run build`. |
| E2E | `.github/workflows/ci.yml` executa `npm run e2e` com Playwright Chromium. |
| Docker Compose config | `.github/workflows/ci.yml` executa `docker compose config`. |
| Docker Compose build | `.github/workflows/ci.yml` executa `docker compose build`. |

## Casos criticos do backend

| Caso do PDF | Testes existentes |
| --- | --- |
| OEE | `test_oee_calculation` cobre performance e qualidade; `test_oee_availability_drops_when_dev_moral_is_below_burnout_threshold` cobre disponibilidade afetada por moral baixa; `test_oee_quality_drops_when_production_bug_emerges_without_delivery` cobre bug em producao mesmo sem entrega na sprint. |
| Processamento de sprint | `test_process_sprint_applies_progress_and_moral_drain`, `test_moving_completed_qa_card_to_done_pays_value_once`, `test_active_clients_generate_recurring_revenue` e testes de atraso/cancelamento cobrem efeitos centrais de sprint. |
| Lei de Brooks | `test_junior_alone_on_large_card_makes_no_progress`, `test_pleno_needs_senior_mentor_on_large_card` e `test_brooks_law_overstaffing_increases_moral_drain_and_bug_risk` cobrem senioridade, mentoria e custo de coordenação. |
| Drenagem de moral | `test_process_sprint_applies_progress_and_moral_drain`, `test_qa_worker_matches_qa_column`, `test_rest_space_kaizen_reduces_active_work_moral_drain` e cenarios de God-tier cobrem impacto de trabalho, estagio, Kaizen e retenção. |
| Geração de eventos | `test_urgent_client_event_adds_playable_short_deadline_card`, `test_referral_event_adds_discount_candidate_to_pool`, `test_retro_bug_event_turns_done_card_into_backlog_bug`, `test_raise_request_event_sets_salary_deadline_and_dev_leaves_if_unanswered`, `test_headhunter_event_targets_senior_and_retention_cost_is_processed`, `test_conference_event_gives_moral_and_blocks_one_productive_sprint`, `test_oee_audit_event_cancels_lowest_reputation_client_when_average_oee_is_bad`, `test_market_trend_event_adds_extra_specialty_demand_for_five_sprints` e `test_urgent_client_event_penalizes_reputation_when_backlog_wip_is_full` cobrem eventos que alteram estado e consequencias de WIP cheio. |

## Frontend e E2E

- Kanban: `frontend/src/App.test.tsx` valida colunas, WIP visivel, OEE no card e bloqueio de movimentos invalidos.
- Painel de devs: `frontend/src/App.test.tsx` valida nomes proprios e moral no painel Gemba.
- Hall of Kaizen: `frontend/src/App.test.tsx` valida abertura, metricas finais, badges e MVP.
- E2E: `frontend/e2e/factory-game.spec.ts` cobre criar partida, jogar sprints, contratar dev, aplicar Kaizen e abrir Hall of Kaizen.

## Lacunas restantes

- O CI valida `docker compose config` e `docker compose build`, mas nao sobe os containers nem executa um smoke HTTP contra o Compose. Esse smoke exigiria tempo e dependencias maiores; para esta rodada foi mantido fora por ser nao essencial e para evitar ampliar risco no fim.
- Acoes de mitigacao para alguns eventos ainda sao agregadas no processamento de sprint. Exemplo: pedido de aumento e headhunter podem ser resolvidos quando o caixa comporta o novo salario, mas nao ha comandos HTTP dedicados chamados `accept-raise` ou `retain-dev`.
