"""Caminhos e configuracao central do projeto.

Todos os caminhos sao derivados da raiz do repositorio, para que scripts e
notebooks funcionem independentemente do diretorio de trabalho atual.
"""

from __future__ import annotations

import os
from pathlib import Path

# .../src/acidentes_trabalho/config.py -> sobe 3 niveis ate a raiz do repositorio.
RAIZ = Path(__file__).resolve().parents[2]

DADOS = RAIZ / "data"
DADOS_RAW = DADOS / "raw"
DADOS_INTERIM = DADOS / "interim"
DADOS_PROCESSED = DADOS / "processed"
DADOS_EXTERNAL = DADOS / "external"

NOTEBOOKS = RAIZ / "notebooks"
RELATORIOS = RAIZ / "reports"
FIGURAS = RELATORIOS / "figuras"
DOCS = RAIZ / "docs"

# Todos os diretorios de dados/saida que o projeto espera encontrar.
DIRETORIOS = (
    DADOS_RAW,
    DADOS_INTERIM,
    DADOS_PROCESSED,
    DADOS_EXTERNAL,
    FIGURAS,
)

# Semente unica para qualquer amostragem, split ou modelo do projeto.
SEED = int(os.getenv("SEED", "42"))


def garantir_diretorios() -> None:
    """Cria os diretorios de dados e saida caso ainda nao existam."""
    for diretorio in DIRETORIOS:
        diretorio.mkdir(parents=True, exist_ok=True)
