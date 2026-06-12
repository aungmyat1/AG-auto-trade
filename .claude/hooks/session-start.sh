#!/bin/bash
# SessionStart hook — make fresh Claude Code web containers test-ready.
# Idempotent: skips install when deps are already importable.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

if ! python3 -c "import numpy, pandas, scipy, pytest, ruff" 2>/dev/null; then
  pip install -q -e ".[dev]"
fi

echo "AG session ready: $(python3 -c 'import numpy, pandas, scipy; print(f"numpy {numpy.__version__}, pandas {pandas.__version__}, scipy {scipy.__version__}")') | run tests: python3 -m pytest tests/ -q"
