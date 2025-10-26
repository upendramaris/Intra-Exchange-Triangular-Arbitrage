from __future__ import annotations

from functools import lru_cache
from typing import Dict, List

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    exchange: str = Field(default="binance")
    quote: str = Field(default="USDT")
    tri_symbols: str = Field(default="BTC,ETH,BNB", alias="TRI_SYMBOLS")
    top_levels: int = Field(default=3, ge=1)
    paper_mode: bool = Field(default=True)
    target_notional_quote: float = Field(default=10_000, gt=0)
    min_gross_edge_bps: float = Field(default=40)
    min_net_edge_bps: float = Field(default=10)
    slippage_bps: float = Field(default=5)
    fee_table_json: str = Field(default='{"binance":{"taker":0.0004,"maker":0.0002}}')
    max_leg_notional_quote: float = Field(default=20_000, gt=0)
    max_open_cycles: int = Field(default=1, ge=1)
    price_tick_buffer_bps: float = Field(default=3)
    redis_url: str = Field(default="redis://localhost:6379/0")
    db_url: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/triarb")
    admin_port: int = Field(default=8081)
    log_level: str = Field(default="INFO")
    prometheus_port: int = Field(default=9000)

    binance_api_key: str | None = None
    binance_api_secret: str | None = None
    binance_ws_base_url: str = Field(default="wss://stream.binance.com:9443", alias="BINANCE_WS_BASE_URL")

    @computed_field
    @property
    def base_symbols(self) -> List[str]:
        return [sym.strip().upper() for sym in self.tri_symbols.split(",") if sym.strip()]

    @computed_field
    @property
    def fee_table(self) -> Dict[str, Dict[str, float]]:
        import json

        return json.loads(self.fee_table_json)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
