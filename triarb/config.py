from __future__ import annotations

import socket
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Sequence

from sqlalchemy.engine.url import URL, make_url

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
    local_db_url: str | None = Field(default=None, alias="LOCAL_DB_URL")
    local_db_host: str | None = Field(default=None, alias="LOCAL_DB_HOST")
    admin_port: int = Field(default=8081)
    log_level: str = Field(default="INFO")
    prometheus_port: int = Field(default=9000)

    binance_api_key: str | None = None
    binance_api_secret: str | None = None
    binance_ws_base_url: str = Field(default="wss://stream.binance.com:9443", alias="BINANCE_WS_BASE_URL")
    binance_ws_alt_urls: str = Field(
        default="wss://stream.binance.us:9443",
        alias="BINANCE_WS_ALT_URLS",
        description="Comma-separated list of backup WebSocket endpoints.",
    )

    @computed_field
    @property
    def base_symbols(self) -> List[str]:
        return [sym.strip().upper() for sym in self.tri_symbols.split(",") if sym.strip()]

    @computed_field
    @property
    def fee_table(self) -> Dict[str, Dict[str, float]]:
        import json

        return json.loads(self.fee_table_json)

    @computed_field
    @property
    def binance_ws_urls(self) -> Sequence[str]:
        urls: List[str] = []
        seen: set[str] = set()

        def _add(url: str | None) -> None:
            if not url:
                return
            normalized = url.strip().rstrip("/")
            if not normalized or normalized in seen:
                return
            seen.add(normalized)
            urls.append(normalized)

        _add(self.binance_ws_base_url)
        for candidate in self.binance_ws_alt_urls.split(","):
            _add(candidate)

        return urls or ["wss://stream.binance.com:9443"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    env_files: List[str | Path] = [".env"]
    local_env = Path(".env.local")
    if local_env.exists():
        env_files.append(local_env)

    settings = Settings(_env_file=tuple(env_files), _env_file_encoding="utf-8")
    resolved_db_url = _resolve_db_url(settings)

    if resolved_db_url != settings.db_url:
        settings = settings.model_copy(update={"db_url": resolved_db_url})

    return settings


def _resolve_db_url(settings: Settings) -> str:
    if settings.local_db_url:
        return settings.local_db_url

    try:
        parsed: URL = make_url(settings.db_url)
    except Exception:
        return settings.db_url

    host = parsed.host
    if not host:
        return settings.db_url

    if _host_resolves(host):
        return settings.db_url

    preferred_host = settings.local_db_host
    if not preferred_host and host == "db":
        preferred_host = "localhost"

    if preferred_host:
        return str(parsed.set(host=preferred_host))

    return settings.db_url


def _host_resolves(host: str) -> bool:
    try:
        socket.getaddrinfo(host, None)
    except OSError:
        return False

    return True
