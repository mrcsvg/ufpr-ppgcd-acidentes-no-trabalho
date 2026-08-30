"""Conversao das datas dos microdados de CAT.

O dicionario oficial de 10/02/2021 declara as datas como ``AAAAMMDD``, mas
**nenhum arquivo do acervo usa esse formato**. O que aparece de fato e:

- ``DD/MM/AAAA`` para data exata, com ``00/00/0000`` marcando ausencia;
- ``AAAA/MM`` para competencia (mes de referencia), com ``0000/00`` para ausencia.

Os dois convivem no mesmo arquivo: em varios esquemas a coluna 2 traz competencia
enquanto as colunas finais trazem data exata.
"""

from __future__ import annotations

import pandas as pd

FORMATO_DATA = "%d/%m/%Y"
FORMATO_COMPETENCIA = "%Y/%m"

# Sentinelas de ausencia usadas no lugar de nulo.
SENTINELAS_DATA = frozenset({"00/00/0000", "0000/00", "", "  /  /    "})


def _limpar(serie: pd.Series) -> pd.Series:
    """Normaliza a serie para texto sem espacos nas pontas, com <NA> nas sentinelas."""
    texto = serie.astype("string").str.strip()
    return texto.where(~texto.isin(SENTINELAS_DATA) & texto.notna(), other=pd.NA)


def para_data(serie: pd.Series) -> pd.Series:
    """Converte ``DD/MM/AAAA`` em ``datetime``; invalidos e sentinelas viram ``NaT``."""
    texto = _limpar(serie)
    valido = texto.str.fullmatch(r"\d{2}/\d{2}/\d{4}").fillna(False)
    return pd.to_datetime(texto.where(valido), format=FORMATO_DATA, errors="coerce")


def para_competencia(serie: pd.Series) -> pd.Series:
    """Converte ``AAAA/MM`` no periodo mensal correspondente; invalidos viram ``NaT``."""
    texto = _limpar(serie)
    valido = texto.str.fullmatch(r"\d{4}/\d{2}").fillna(False)
    convertido = pd.to_datetime(texto.where(valido), format=FORMATO_COMPETENCIA, errors="coerce")
    return convertido.dt.to_period("M")


def e_competencia(serie: pd.Series, amostra: int = 1000) -> bool:
    """Indica se a coluna esta no formato de competencia ``AAAA/MM``.

    Decide pela primeira ocorrencia nao sentinela: os arquivos sao homogeneos
    dentro de uma mesma coluna.
    """
    texto = _limpar(serie.head(amostra)).dropna()
    if texto.empty:
        return False
    return bool(texto.str.fullmatch(r"\d{4}/\d{2}").any())
