from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class AuctionResult:
    winner: Optional[str]
    price: float
    bids_sorted: List[Tuple[str, float]]


def second_price_auction(bids: Dict[str, float]) -> AuctionResult:
    """Vickrey (second-price sealed-bid) auction.

    Returns winner, price (second-highest), and sorted bids (desc).
    If fewer than 1 bid, winner is None. If exactly 1 bid, price is that bid.
    """
    if not bids:
        return AuctionResult(winner=None, price=0.0, bids_sorted=[])
    sorted_bids = sorted(bids.items(), key=lambda kv: kv[1], reverse=True)
    winner, top = sorted_bids[0]
    price = sorted_bids[1][1] if len(sorted_bids) > 1 else top
    return AuctionResult(winner=winner, price=price, bids_sorted=sorted_bids)
