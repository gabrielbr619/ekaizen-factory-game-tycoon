# AGENTS.md

Operational contract for agents working on this repository.

## Source of Truth

The challenge PDF at `C:\Users\gabri\Downloads\desafio-tecnico-ekaizen-factory-game-tycoon.pdf` is the product and delivery bible.

Before changing any file, read the relevant PDF sections plus the current repository docs:

- `README.md`
- `architecture.md`
- `docs/**`
- this `AGENTS.md`

If code or docs disagree with the PDF, treat the PDF as authoritative and either fix the inconsistency inside your ownership scope or report it clearly.

## Shared Repository Rules

This repo may be edited by multiple agents at the same time.

- Do not revert, reset, checkout, clean, delete, reformat, or "tidy" changes you did not make.
- Run `git status --short --branch` before editing and before final response.
- Keep edits inside the task ownership you were given.
- If a file has unrelated in-flight edits, preserve them and make the smallest compatible change.
- Do not commit unless the user explicitly asks.
- Do not push, open PRs, tag releases, or change deployment state unless explicitly asked.
- Do not edit deploy infrastructure unless the task explicitly includes deployment work.
- Never claim a public URL is ready unless it was validated in the current run.

## Ownership Boundaries

Default ownership lanes:

- Backend agent: `backend/**`, backend tests, backend Dockerfile.
- Frontend agent: `frontend/**`, frontend tests, frontend Dockerfile.
- Documentation/process agent: `README.md`, `AGENTS.md`, `architecture.md`, `ARCHITECTURE.md`, `docs/**`.
- CI smoke/test agent: `.github/workflows/**` only for lint/typecheck/test/build smoke gates, never deploy.
- Deploy agent: deployment files and public URL work only when explicitly assigned.

Cross-lane changes require a clear reason in the final report. When in doubt, stop and report the boundary instead of editing another agent's files.

## Non-Negotiable Product Requirements

The PDF requires a single-player, turn-based factory/software-house tycoon where the backend is authoritative.

Core requirements that must remain true:

- The server owns all game state, decisions, RNG, calculations, and persistence.
- The frontend only presents state and sends player commands.
- Mutations go through server commands and are idempotent through a unique command identifier and/or `Idempotency-Key`.
- RNG is deterministic from the game seed plus sprint/context.
- The full game state is persisted after each processed sprint.
- The Kanban flow is sequential: Backlog -> Analise -> Desenvolvimento -> QA -> Done.
- Cards do not move to Done directly from development; QA resolution happens during sprint processing.
- WIP limits are enforced by the backend.
- At least one real-time channel exists between server and client; this project uses SSE at `/games/{game_id}/events`.
- The eight continuous-improvement concepts must affect gameplay and be visible in the UI: Kanban, WIP Limit, Lead Time, Cycle Time, OEE, PDCA, Andon, Heijunka.
- Hall of Kaizen must summarize final verdict, metrics, impactful Kaizens, MVPs, badges, timeline, and replay path.

## Architecture Rules

Backend:

- Domain code stays independent from FastAPI, SQLite, cookies, HTTP schemas, and JSON transport.
- API code converts HTTP requests into domain commands and maps errors to HTTP responses.
- Persistence stores games and idempotent command responses; it must not calculate gameplay.
- Keep `backend/app/domain/engine.py` as a thin facade if present.
- Prefer small rule modules over a central god object.

Frontend:

- Do not calculate game outcomes, RNG, WIP enforcement, OEE, bug generation, sprint economics, or victory/defeat in React.
- Frontend may format values, group cards by column, render labels, and manage UI state.
- The first screen is the playable game, not a marketing page.

Documentation:

- Be honest without self-sabotage.
- Do not write vague phrases such as "advanced rules were simplified".
- List the exact tradeoff, why it was chosen, and why it does not violate the PDF.
- Do not promise deploy/public URLs unless they are validated and available.

## Quality Gates

Run the lightest gate that matches your changes, and report anything not run.

Documentation-only:

```bash
git diff --check
```

Backend:

```bash
cd backend
ruff check app tests
mypy app --strict
pytest tests
```

Frontend:

```bash
cd frontend
npm run typecheck
npm run test
npm run e2e
npm run build
```

Docker/local smoke:

```bash
docker compose config
docker compose build
```

CI may run the same smoke/test gates. CI must not deploy unless deployment is explicitly part of the task.

## Commit Message Convention

Use clear conventional commits if the user explicitly asks for commits:

- `feat(domain): process qa completion during sprint`
- `feat(api): add idempotent game commands`
- `feat(ui): render kanban board with wip limits`
- `test(domain): cover brooks law and heijunka`
- `docs: document delivery tradeoffs`

Do not mention AI, agents, Codex, Claude, or generated-by tooling in commit messages.

## Final Report Format

End each task with:

- status
- files changed
- tests/checks run
- key decisions or points documented
- remaining risks

If other agents changed files concurrently, mention only what affects the task. Do not blame or revert their work.
