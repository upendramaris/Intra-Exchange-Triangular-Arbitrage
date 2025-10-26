from dataclasses import dataclass
from typing import List

from triarb.engine.signals import Opportunity


@dataclass
class SimulationResult:
    opportunities: List[Opportunity]
    executed: int


def simulate(opportunities: List[Opportunity]) -> SimulationResult:
    executed = sum(1 for opp in opportunities if opp.net_bps > 0)
    return SimulationResult(opportunities=opportunities, executed=executed)
