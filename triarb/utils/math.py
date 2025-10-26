from __future__ import annotations


def bps_to_ratio(bps: float) -> float:
    return bps / 10_000


def apply_bps(value: float, bps: float) -> float:
    return value * (1 + bps_to_ratio(bps))


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
