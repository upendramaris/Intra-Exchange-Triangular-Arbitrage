#!/usr/bin/env bash
set -euo pipefail

ruff check .
mypy triarb
