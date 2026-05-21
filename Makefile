.PHONY: help venv install fetch fetch-external fetch-ohlcv test reproduce clean

PY ?= python3.11
VENV = .venv
BIN = $(VENV)/bin

help:
	@echo "Targets:"
	@echo "  make install     - create venv and install requirements"
	@echo "  make fetch        - download all datasets (external series + OHLCV)"
	@echo "  make test         - run the test suite (26 tests)"
	@echo "  make reproduce    - regenerate the v6 result tables (runner + walk-forward)"
	@echo "  make clean        - remove venv and caches"

$(VENV):
	$(PY) -m venv $(VENV)

install: $(VENV)
	$(BIN)/pip install --quiet --upgrade pip
	$(BIN)/pip install --quiet -r requirements.txt
	@echo "Installed. Activate with: source $(VENV)/bin/activate"

fetch-external:
	$(BIN)/python -m src.data.fetchers.fetch_fng
	$(BIN)/python -m src.data.fetchers.fetch_dxy
	$(BIN)/python -m src.data.fetchers.fetch_funding BTCUSDT ETHUSDT

fetch-ohlcv:
	$(BIN)/python -m src.data.fetch_ohlcv BTC_USDT ETH_USDT

fetch: fetch-external fetch-ohlcv
	$(BIN)/python -m src.data.fetchers.summary

test:
	$(BIN)/python -m pytest -o addopts="" tests/ -v

reproduce:
	$(BIN)/python -m src.backtest.runner
	$(BIN)/python -m src.backtest.walkforward

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
