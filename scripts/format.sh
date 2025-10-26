#!/usr/bin/env bash
set -euo pipefail

ruff check --select I --fix .
black .
