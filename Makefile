.PHONY: setup dados relatorio figuras atividade3 apresentacao test lint fmt notebook limpar

VENV := .venv
PY := $(VENV)/bin/python

setup:
	python3 -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev,notebooks]"

dados:
	$(PY) -m acidentes_trabalho.pipeline

relatorio:
	$(PY) -m acidentes_trabalho.pipeline relatorio

figuras:
	$(PY) -m acidentes_trabalho.figuras

apresentacao:
	$(PY) reports/apresentacao/figuras_slides.py
	node reports/apresentacao/gerar_deck.js
	$(PY) reports/apresentacao/auditar_deck.py

atividade3: figuras
	$(PY) -m pip install -q python-docx
	$(PY) reports/atividade3/preencher.py

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
