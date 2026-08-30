"""Decisoes de limpeza aplicadas sobre a leitura crua dos CSVs.

``dados.esquemas.ler`` entrega os arquivos como eles sao, apenas unificando o
leiaute. Toda decisao que altere o significado de um valor mora aqui, para que
fique explicita, testada e reversivel — a camada ``raw`` continua intacta.

As decisoes vem da inspecao registrada em ``docs/qualidade-dos-dados.md``.
"""

from __future__ import annotations

import re

import pandas as pd

# Marcadores de ausencia gravados como texto no lugar de nulo. O primeiro aparece
# com o caractere de "nao" corrompido de varias formas conforme o encoding, entao
# e casado por padrao.
PADRAO_NAO_CLASSIFICADO = re.compile(r"^\{.{0,2}\s*class\}$")
SENTINELA_ZERADO = "Zerado"

# uf_acidente esta corrompida na origem e nao e recuperavel:
#   - os rotulos estao trocados (Sao Paulo aparece como "Maranhao", Minas Gerais
#     como "Rondonia", Parana como "Roraima", ...), de forma sistematica;
#   - 12 UFs nao tem rotulo algum e caem todas em "{n class}", entre elas Rio
#     Grande do Sul, Santa Catarina, Bahia, Goias, Espirito Santo, Mato Grosso,
#     Mato Grosso do Sul e Ceara.
# Ou seja, a coluna nao distingue esses 12 estados de forma alguma. Use
# uf_empregador e municipio_empregador, lembrando que localizam o empregador, e
# nao o acidente.
COLUNAS_NAO_CONFIAVEIS = ("uf_acidente",)


def _e_sentinela(serie: pd.Series) -> pd.Series:
    texto = serie.astype("string")
    return texto.str.match(PADRAO_NAO_CLASSIFICADO).fillna(False) | (texto == SENTINELA_ZERADO)


def marcar_sentinelas(df: pd.DataFrame) -> pd.DataFrame:
    """Troca os marcadores de ausencia gravados como texto por nulo.

    Sao eles ``{n class}`` (nao classificado, com variacoes de encoding) e
    ``Zerado``. Sem isso eles entram nas contagens como se fossem categorias.
    """
    limpo = df.copy()
    for coluna in limpo.columns:
        if limpo[coluna].dtype == "object" or str(limpo[coluna].dtype) == "string":
            limpo[coluna] = limpo[coluna].where(~_e_sentinela(limpo[coluna]), other=pd.NA)
    return limpo


def descartar_colunas_nao_confiaveis(df: pd.DataFrame) -> pd.DataFrame:
    """Remove as colunas corrompidas na origem (ver ``COLUNAS_NAO_CONFIAVEIS``)."""
    return df.drop(columns=[c for c in COLUNAS_NAO_CONFIAVEIS if c in df.columns])


def limpar(df: pd.DataFrame, descartar: bool = True) -> pd.DataFrame:
    """Aplica as decisoes de limpeza do projeto na ordem definida.

    Args:
        df: saida de ``dados.esquemas.ler``.
        descartar: se ``True``, remove tambem as colunas nao confiaveis.
    """
    limpo = marcar_sentinelas(df)
    return descartar_colunas_nao_confiaveis(limpo) if descartar else limpo
