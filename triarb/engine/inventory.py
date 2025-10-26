from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Inventory:
    balances: Dict[str, float] = field(default_factory=dict)

    def update(self, asset: str, delta: float) -> None:
        self.balances[asset] = self.balances.get(asset, 0.0) + delta

    def available(self, asset: str) -> float:
        return self.balances.get(asset, 0.0)
