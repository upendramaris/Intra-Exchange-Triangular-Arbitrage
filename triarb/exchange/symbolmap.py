from itertools import permutations
from typing import List, Tuple


def generate_pairs(bases: List[str], quote: str) -> List[str]:
    """Return all unique symbols necessary to build triangles among bases with the quote."""
    symbols = {f"{base}/{quote}" for base in bases}
    for a, b in permutations(bases, 2):
        symbols.add(f"{a}/{b}")
    return sorted(symbols)


def enumerate_cycles(bases: List[str], quote: str) -> List[Tuple[str, str, str]]:
    cycles = []
    for a, b in permutations(bases, 2):
        if a == b:
            continue
        cycles.append((f"{quote}/{a}", f"{a}/{b}", f"{b}/{quote}"))
    return cycles
