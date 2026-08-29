.PHONY: setup test lint fmt notebook limpar

VENV := .venv
PY := $(VENV)/bin/python

setup:
	python3 -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev,notebooks]"

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check .

fmt:
	$(PY) -m ruff check --fix .
	$(PY) -m ruff format .

notebook:
	$(PY) -m jupyterlab

limpar:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
