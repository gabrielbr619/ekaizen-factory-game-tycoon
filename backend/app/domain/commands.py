from __future__ import annotations

from app.domain.models import Developer, GameState, TimelineEvent
from app.domain.rules.andon import refresh_alerts


def hire_candidate(game: GameState, candidate_id: str) -> GameState:
    candidate = next((item for item in game.candidates if item.id == candidate_id), None)
    if candidate is None:
        raise ValueError("Candidato nao encontrado.")
    game.budget -= candidate.salary
    game.developers.append(
        Developer(
            candidate.id.replace("cand", "dev"),
            candidate.name,
            candidate.specialty,
            candidate.level,
            candidate.speed,
            candidate.salary,
            candidate.bug_rate,
            candidate.moral,
            candidate.avatar,
            onboarding_sprints=2,
        )
    )
    game.candidates = [item for item in game.candidates if item.id != candidate_id]
    game.timeline.append(TimelineEvent(game.sprint, "hire", f"{candidate.name} entrou no time."))
    return refresh_alerts(game)
