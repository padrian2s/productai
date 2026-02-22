#!/usr/bin/env bash
set -euo pipefail

# ProductAI — Run Script
# Usage: ./run.sh [--port PORT] [--reload]

PORT="${PORT:-8000}"
RELOAD=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --port) PORT="$2"; shift 2 ;;
        --reload) RELOAD="--reload"; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Check for API key
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "WARNING: ANTHROPIC_API_KEY is not set."
    echo "AI features will not work without it."
    echo "  export ANTHROPIC_API_KEY=your-key-here"
    echo ""
fi

echo "Starting ProductAI on http://localhost:${PORT}"
echo "Press Ctrl+C to stop"
echo ""

uv run uvicorn productai.app:app --host 0.0.0.0 --port "$PORT" $RELOAD
