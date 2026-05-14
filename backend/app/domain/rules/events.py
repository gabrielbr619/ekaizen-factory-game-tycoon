from __future__ import annotations

import random

from app.domain.models import GameState


def generate_events(game: GameState, rng: random.Random) -> list[str]:
    options = [
        "Cliente urgente: card de alto valor com deadline curto apareceu.",
        "Pedido de aumento: um dev quer reconhecimento financeiro.",
        "Bug retroativo: um card em Done pode voltar como bug critico.",
        "Auditoria de OEE: cliente avaliara sua eficiencia na proxima sprint.",
        "Tendencia de mercado: uma especialidade tera mais demanda.",
        "Indicacao: um candidato com salario reduzido apareceu no pool.",
    ]
    return rng.sample(options, k=rng.randint(1, 3))
