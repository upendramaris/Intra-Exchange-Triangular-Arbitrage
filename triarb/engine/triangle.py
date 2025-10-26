from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from triarb.config import get_settings


@dataclass(frozen=True)
class TriangleLeg:
    symbol: str
    from_asset: str
    to_asset: str


@dataclass
class Triangle:
    legs: Tuple[TriangleLeg, TriangleLeg, TriangleLeg]

    @property
    def symbols(self) -> List[str]:
        return [leg.symbol for leg in self.legs]


def build_triangles(quote: str, bases: List[str]) -> List[Triangle]:
    triangles: List[Triangle] = []
    for i in range(len(bases)):
        for j in range(len(bases)):
            if i == j:
                continue
            a = bases[i]
            b = bases[j]
            legs = (
                TriangleLeg(symbol=f"{a}/{quote}", from_asset=quote, to_asset=a),
                TriangleLeg(symbol=f"{b}/{a}", from_asset=a, to_asset=b),
                TriangleLeg(symbol=f"{quote}/{b}", from_asset=b, to_asset=quote),
            )
            triangles.append(Triangle(legs))
    return triangles


def triangle_edge(
    triangle: Triangle,
    book_data: Dict[str, Dict[str, float]],
    slippage_bps: float,
    fee_table: Dict[str, float],
) -> Tuple[float, float]:
    settings = get_settings()
    gross = 1.0
    for leg in triangle.legs:
        data = book_data.get(leg.symbol)
        if not data:
            return 0.0, 0.0
        if leg.from_asset == data["quote"]:
            rate = 1 / (data["ask"] * (1 + slippage_bps / 10_000))
        else:
            rate = data["bid"] * (1 - slippage_bps / 10_000)
        gross *= rate
    gross_edge = (gross - 1) * 10_000
    net_edge = gross_edge - settings.min_net_edge_bps
    return gross_edge, net_edge
