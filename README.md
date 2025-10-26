# Triangular Arbitrage Engine

High-performance, single-exchange triangular arbitrage system targeting spot markets on Binance (extensible to other venues). The stack uses asyncio-native components, FastAPI admin APIs, Redis for state, Postgres for persistence, and Prometheus metrics.

## Quickstart

```bash
cp .env.example .env
docker-compose up -d --build
make migrate
make run
```

## Features
- Native Binance WebSocket L2 ingestion with configurable depth aggregation.
- Exchange adapter interface (ccxt REST + native WS) for future Kraken/Coinbase support.
- Fee- and slippage-aware triangle math with depth-based sizing.
- Near-simultaneous three-leg execution with partial-fill handling and unwind safeguards.
- Paper/live modes, configurable per-symbol fee table, and latency-aware order sizing.
- Redis-backed order book + balance cache, Postgres persistence for opportunities/trades/fills/PNL.
- FastAPI admin server exposing health, metrics, and operational controls.
- Prometheus metrics, JSON logging, Alembic migrations, pytest coverage, docker-compose dev stack.

## Development

| Command | Description |
| ------- | ----------- |
| `make format` | Run code formatters (ruff/black placeholder) |
| `make lint` | Run linters/tests |
| `make test` | Execute pytest suite |
| `make run` | Start the bot process |
| `make api` | Launch FastAPI admin server |

See `scripts/` for the underlying shell helpers.

### Local environment overrides

Docker services resolve the Postgres host as `db`, but commands executed directly on the host (e.g. `poetry run scripts/migrate.sh`) need `localhost`. Create a `.env.local` file for host-only tweaks—anything defined there overrides the values from `.env`. You can either redefine `DB_URL` entirely or set `LOCAL_DB_URL` / `LOCAL_DB_HOST` so migrations and the app point at your local Postgres instance without touching the compose-friendly defaults.

### Binance WebSocket access

The client now cycles through the URLs defined in `BINANCE_WS_BASE_URL` and `BINANCE_WS_ALT_URLS` (comma-separated). By default we try the global endpoint first and fall back to `wss://stream.binance.us:9443` whenever the server replies with HTTP 451. If both are blocked in your region, drop your preferred relay(s) into `BINANCE_WS_ALT_URLS` or override the base URL entirely in `.env` / `.env.local`, then restart `make run`.
