from __future__ import annotations

from app.api.serialization import encode_game
from app.domain.engine import top_kaizens
from app.domain.models import GameState


def build_hall_of_kaizen_response(game: GameState) -> dict[str, object]:
    metrics = game.metrics_history[-1] if game.metrics_history else None
    dev_mvp = max(game.developers, key=lambda dev: dev.clean_cards_delivered)
    return {
        "verdict": game.verdict.value,
        "accumulated_profit": game.accumulated_profit,
        "budget": game.budget,
        "oee_avg": round(
            sum(item.oee for item in game.metrics_history) / max(1, len(game.metrics_history)), 3
        ),
        "lead_time_avg": metrics.lead_time_avg if metrics is not None else 0,
        "throughput_avg": round(
            sum(item.delivered_cards for item in game.metrics_history)
            / max(1, len(game.metrics_history)),
            2,
        ),
        "top_kaizens": encode_game(top_kaizens(game)),
        "sprint_mvp": best_sprint(game),
        "dev_mvp": dev_mvp.name,
        "badges": game.badges,
        "timeline": encode_game(game.timeline[-12:]),
    }


def best_sprint(game: GameState) -> dict[str, int | float]:
    metrics = max(
        game.metrics_history,
        key=lambda item: (item.throughput_value, item.oee),
        default=None,
    )
    if metrics is None:
        return {"sprint": 0, "throughput_value": 0, "oee": 0.0}
    return {
        "sprint": metrics.sprint,
        "throughput_value": metrics.throughput_value,
        "oee": metrics.oee,
    }
