"""Variaveis derivadas das colunas originais.

Tudo aqui e calculado a partir do que ja existe na base, sem fonte externa. O
caso mais util e o codigo do municipio: ``municipio_empregador`` vem como
``"316860-Teofilo Otoni"`` e o nome chega truncado em parte dos arquivos, mas o
codigo IBGE de 6 digitos esta sempre intacto - e seus dois primeiros digitos sao
o codigo da UF, o que da uma UF confiavel sem depender do rotulo.
"""

from __future__ import annotations

import pandas as pd

# Codigo IBGE de UF -> sigla. Cobre as 27 unidades da federacao.
UF_POR_CODIGO = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}

# Limites de plausibilidade para a idade no momento do acidente. Abaixo de 14 anos
# o vinculo formal e vedado no Brasil, e acima de 100 e quase certamente erro de
# digitacao na data de nascimento.
IDADE_MINIMA = 14
IDADE_MAXIMA = 100


def codigo_municipio(serie: pd.Series) -> pd.Series:
    """Extrai o codigo IBGE de 6 digitos de ``"316860-Teofilo Otoni"``."""
    return serie.astype("string").str.extract(r"^(\d{6})", expand=False)


def nome_municipio(serie: pd.Series) -> pd.Series:
    """Extrai o nome de ``"316860-Teofilo Otoni"``, que pode vir truncado."""
    nome = serie.astype("string").str.extract(r"^\d{6}-(.+)$", expand=False)
    return nome.str.strip()


def uf_do_codigo_municipio(serie: pd.Series) -> pd.Series:
    """Devolve a sigla da UF a partir do codigo do municipio.

    Codigo invalido ou UF inexistente viram nulo, em vez de sigla inventada.
    """
    codigo_uf = codigo_municipio(serie).str[:2]
    return codigo_uf.map(UF_POR_CODIGO).astype("string")


def idade(data_acidente: pd.Series, data_nascimento: pd.Series) -> pd.Series:
    """Idade em anos completos na data do acidente.

    Valores fora de ``[IDADE_MINIMA, IDADE_MAXIMA]`` viram nulo: sao incompativeis
    com vinculo formal de trabalho e indicam data de nascimento errada.
    """
    dias = (data_acidente - data_nascimento).dt.days
    anos = (dias / 365.25).floordiv(1)
    return anos.where(anos.between(IDADE_MINIMA, IDADE_MAXIMA)).astype("Float64")


def acrescentar(df: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta as colunas derivadas ao DataFrame normalizado."""
    novo = df.copy()
    novo["codigo_municipio_empregador"] = codigo_municipio(df["municipio_empregador"])
    novo["nome_municipio_empregador"] = nome_municipio(df["municipio_empregador"])
    novo["uf_empregador_sigla"] = uf_do_codigo_municipio(df["municipio_empregador"])
    novo["ano_acidente"] = df["data_acidente"].dt.year.astype("Int16")
    novo["mes_acidente"] = df["data_acidente"].dt.month.astype("Int8")
    novo["idade_acidente"] = idade(df["data_acidente"], df["data_nascimento"])
    return novo
