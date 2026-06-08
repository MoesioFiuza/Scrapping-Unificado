#!/usr/bin/env bash
# Build do frontend para produção (subpath /scraper/)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"
npm ci
npm run build
echo "Build concluído em frontend/dist (base /scraper/)"
