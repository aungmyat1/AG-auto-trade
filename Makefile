.PHONY: install test gate lint clean

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

gate:
	@echo "Usage: python scripts/run_gate.py <trades.csv> --n-trials <N>"
	@echo "Example: python scripts/run_gate.py data/A1_backtest.csv --instrument GC --n-trials 15"

lint:
	ruff check ag/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -name "*.pyc" -delete 2>/dev/null; \
	rm -rf .pytest_cache .coverage; true
