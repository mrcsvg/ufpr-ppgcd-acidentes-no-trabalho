"""Decisoes de limpeza aplicadas sobre a leitura crua dos CSVs.

``dados.esquemas.ler`` entrega os arquivos como eles sao, apenas unificando o
leiaute. Toda decisao que altere o significado de um valor mora aqui, para que
fique explicita, testada e reversivel — a camada ``raw`` continua intacta.

As decisoes vem da inspecao registrada em ``docs/qualidade-dos-dados.md``.
"""

from __future__ import annotations

import re

import pandas as pd

# Marcadores de ausencia gravados como texto no lugar de nulo.
#
# O primeiro e "{n class}" (nao classificado), e ele **chega truncado** pela
# largura fixa da coluna: aparece como "{n class}", "{n class" e ate "{n",
# conforme o campo. Casar o texto inteiro deixaria passar as versoes cortadas -
# eram 90.844 registros em indica_obito e origem_cadastramento. Como nenhum valor
# legitimo da base comeca com chave (verificado nos 3,9 milhoes de registros), a
# abertura sozinha basta e resiste a qualquer truncamento.
PADRAO_NAO_CLASSIFICADO = re.compile(r"^\{")
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
    """Marca as posicoes ocupadas por um sentinela.

    Cada operando vira booleano puro antes do ``ou``: combinar mascaras que ainda
    carregam nulo levanta "boolean value of NA is ambiguous" quando elas vem de
    backends diferentes (pyarrow e numpy), o que acontece na pratica porque as
    colunas chegam de origens distintas.
    """
    texto = serie.astype("string")
    padrao = texto.str.match(PADRAO_NAO_CLASSIFICADO).fillna(False).astype(bool)
    zerado = texto.eq(SENTINELA_ZERADO).fillna(False).astype(bool)
    return padrao | zerado


def _e_texto(serie: pd.Series) -> bool:
    """Indica se a coluna guarda texto, em qualquer dos dtypes que o pandas usa.

    Testar o nome do dtype nao serve: ele ja foi ``object``, virou ``string`` e em
    pandas 3 e ``str`` - e uma coluna vinda do Parquet chega como ``category``.
    Uma verificacao presa a um desses nomes falha em silencio nas outras.
    """
    return pd.api.types.is_string_dtype(serie)


def marcar_sentinelas(df: pd.DataFrame) -> pd.DataFrame:
    """Troca os marcadores de ausencia gravados como texto por nulo.

    Sao eles ``{n class}`` (nao classificado, inclusive truncado) e ``Zerado``.
    Sem isso eles entram nas contagens como se fossem categoria.
    """
    limpo = df.copy()
    for coluna in limpo.columns:
        if not _e_texto(limpo[coluna]):
            continue
        serie = limpo[coluna]
        if isinstance(serie.dtype, pd.CategoricalDtype):
            # Nao da para gravar nulo numa categoria que nao existe: volta a
            # texto, limpa, e recategoriza sem o sentinela.
            serie = serie.astype("string")
            limpo[coluna] = serie.where(~_e_sentinela(serie), other=pd.NA).astype("category")
        else:
            limpo[coluna] = serie.where(~_e_sentinela(serie), other=pd.NA)
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
