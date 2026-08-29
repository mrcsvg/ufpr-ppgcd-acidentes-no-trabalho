"""Leitura e escrita padronizada das camadas de dados.

As camadas seguem a convencao do repositorio:

- ``raw``: arquivo original, nunca modificado;
- ``interim``: resultado intermediario de limpeza;
- ``processed``: base final usada em analises e modelos.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from acidentes_trabalho.config import (
    DADOS_EXTERNAL,
    DADOS_INTERIM,
    DADOS_PROCESSED,
    DADOS_RAW,
)

CAMADAS = {
    "raw": DADOS_RAW,
    "interim": DADOS_INTERIM,
    "processed": DADOS_PROCESSED,
    "external": DADOS_EXTERNAL,
}

# Padroes usados nos arquivos de dados abertos brasileiros (CAT, RAIS, CNAE).
SEPARADOR_PADRAO = ";"
ENCODING_PADRAO = "latin-1"


def caminho(nome: str, camada: str = "raw") -> Path:
    """Devolve o caminho completo de ``nome`` dentro de ``camada``.

    Raises:
        ValueError: se ``camada`` nao for uma das camadas conhecidas.
    """
    if camada not in CAMADAS:
        raise ValueError(f"camada desconhecida: {camada!r}; use uma de {sorted(CAMADAS)}")
    return CAMADAS[camada] / nome


def ler_csv(nome: str, camada: str = "raw", **kwargs) -> pd.DataFrame:
    """Le um CSV de ``camada`` com separador e encoding usuais dos dados abertos.

    Qualquer argumento de ``pandas.read_csv`` pode ser sobrescrito via ``kwargs``.
    """
    opcoes = {"sep": SEPARADOR_PADRAO, "encoding": ENCODING_PADRAO, "low_memory": False}
    opcoes.update(kwargs)
    return pd.read_csv(caminho(nome, camada), **opcoes)


def ler_parquet(nome: str, camada: str = "processed", **kwargs) -> pd.DataFrame:
    """Le um arquivo Parquet de ``camada``."""
    return pd.read_parquet(caminho(nome, camada), **kwargs)


def salvar_parquet(df: pd.DataFrame, nome: str, camada: str = "processed", **kwargs) -> Path:
    """Grava ``df`` como Parquet em ``camada`` e devolve o caminho gravado."""
    destino = caminho(nome, camada)
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(destino, index=False, **kwargs)
    return destino
