"""Advanced interaction patterns: negotiation and auction.

These are simple, deterministic stubs suitable for tests and demos. They do not
assume any transport and can be used locally or wired over a CommunicationBus.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple


@dataclass(frozen=True)
class NegotiationResult:
    converged: bool
    rounds: int
    final_value: float
    history: List[float]
    spread: float


def negotiate_numeric(
    proposal_fns: List[Callable[[float, int], float]],
    *,
    initial_value: float = 0.0,
    max_rounds: int = 10,
    epsilon: float = 1e-3,
    aggregation: Callable[[List[float]], float] | None = None,
) -> NegotiationResult:
    """Run a simple numeric negotiation across participants.

    Each round, every participant proposes a numeric value given the current aggregate and round.
    We compute an aggregate (mean by default). Converged when (max - min) < epsilon.
    """
    current = initial_value
    history: List[float] = []
    agg = aggregation or (lambda vals: sum(vals) / len(vals) if vals else current)

    prev: float | None = None
    for r in range(1, max_rounds + 1):
        proposals = [fn(current, r) for fn in proposal_fns]
        lo, hi = min(proposals), max(proposals)
        spread = hi - lo
        new_val = agg(proposals)
        history.append(new_val)
        if prev is not None and abs(new_val - prev) < epsilon:
            return NegotiationResult(converged=True, rounds=r, final_value=new_val, history=history, spread=spread)
        prev = current
        current = new_val

    # Not converged
    # Recompute final spread for reporting
    final_proposals = [fn(current, max_rounds) for fn in proposal_fns]
    spread = max(final_proposals) - min(final_proposals) if final_proposals else 0.0
    return NegotiationResult(converged=False, rounds=max_rounds, final_value=current, history=history, spread=spread)
