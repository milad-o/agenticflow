import math
import pytest

from agenticflow.communication.patterns.negotiation import negotiate_numeric
from agenticflow.communication.patterns.auction import second_price_auction


def _towards(target: float):
    def fn(current: float, round_no: int) -> float:
        # Move halfway towards target each round
        return current + (target - current) * 0.5
    return fn


def _constant(val: float):
    return lambda current, r: val


def test_negotiation_converges_quickly():
    fns = [_towards(10.0), _towards(12.0), _towards(11.0)]
    res = negotiate_numeric(fns, initial_value=0.0, max_rounds=20, epsilon=1e-3)
    assert res.converged is True
    assert res.final_value == pytest.approx(11.0, abs=1e-2)


def test_second_price_auction():
    bids = {"a": 10.0, "b": 12.5, "c": 9.8}
    res = second_price_auction(bids)
    assert res.winner == "b"
    assert res.price == 10.0
