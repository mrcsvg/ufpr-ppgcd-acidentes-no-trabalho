"""Estilo visual unico para todas as figuras do projeto."""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

from acidentes_trabalho.config import FIGURAS

DPI = 150


def aplicar_estilo() -> None:
    """Aplica os padroes de figura do projeto ao matplotlib."""
    mpl.rcParams.update(
        {
            "figure.figsize": (8, 5),
            "figure.dpi": 110,
            "savefig.dpi": DPI,
            "savefig.bbox": "tight",
            "axes.grid": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.alpha": 0.3,
            "font.size": 11,
        }
    )


def salvar_figura(nome: str, fig: plt.Figure | None = None) -> Path:
    """Salva ``fig`` (ou a figura atual) em ``reports/figuras`` e devolve o caminho."""
    fig = fig or plt.gcf()
    FIGURAS.mkdir(parents=True, exist_ok=True)
    destino = FIGURAS / nome
    fig.savefig(destino)
    return destino
