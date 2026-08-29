"""Dicionario de dados dos microdados de CAT.

Transcricao do dicionario oficial publicado nos Dados Abertos da Previdencia
Social (versao de 10/02/2021), disponivel em
``docs/dicionario_cat_dadosabertos_2021-02-10.xlsx``.

O dicionario descreve as variaveis pelo rotulo usado na publicacao; o nome exato
da coluna em cada arquivo pode variar entre as competencias, entao trate
``VARIAVEIS`` como referencia de conteudo e tipo, nao como esquema rigido.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

# Formato das colunas de data nos microdados de CAT.
FORMATO_DATA = "%Y%m%d"


@dataclass(frozen=True)
class Variavel:
    """Uma variavel do dicionario de CAT."""

    rotulo: str
    tipo: str
    categorias: int | None
    descricao: str

    @property
    def e_data(self) -> bool:
        """Indica se a variavel e uma data no formato AAAAMMDD."""
        return self.tipo.startswith("data")


def _v(rotulo: str, tipo: str, categorias: int | None, descricao: str) -> Variavel:
    return Variavel(rotulo, tipo, categorias, descricao)


VARIAVEIS: tuple[Variavel, ...] = (
    _v("Agente Causador do Acidente", "categorica", 305,
       "Descricao e codigo do agente causador do acidente."),
    _v("CBO", "categorica", 2424, "Codigo Brasileiro de Ocupacao."),
    _v("CBO Descricao", "categorica", 2424, "Descricao do Codigo Brasileiro de Ocupacao."),
    _v("CID", "categorica", 15086,
       "Identificador da doenca conforme a CID-10 (Classificacao Internacional de Doencas)."),
    _v("CID Descricao", "categorica", 15086, "Descricao do codigo CID-10."),
    _v("CNAE", "categorica", 87,
       "Classificacao Nacional da Atividade Economica, no agrupamento usado no AEPS."),
    _v("CNAE Descricao", "categorica", 87, "Descricao da atividade economica (CNAE)."),
    _v("Emitente da CAT", "categorica", 5, "Quem emitiu a CAT."),
    _v("Especie do Beneficio", "categorica", 97, "Especie do beneficio previdenciario concedido."),
    _v("Filiacao do Segurado", "categorica", 4,
       "Tipo de filiacao do segurado a Previdencia Social."),
    _v("Indicador de Obito Acidente", "categorica", 2, "Indicador de obito do segurado."),
    _v("Municipio Empregador", "categorica", 5589, "Municipio do empregador."),
    _v("Natureza da Lesao", "categorica", 80, "Descricao e codigo da natureza da lesao."),
    _v("Origem do Cadastramento CAT", "categorica", 3, "Origem do cadastramento da CAT."),
    _v("Parte do Corpo Atingida", "categorica", 45, "Parte do corpo atingida no acidente."),
    _v("Sexo", "categorica", 4, "Sexo do segurado informado na CAT."),
    _v("Tipo de Acidente", "categorica", 4, "Tipo do acidente de trabalho sofrido pelo segurado."),
    _v("UF Municipio do Acidente", "categorica", 28, "Unidade da Federacao do local do acidente."),
    _v("UF Municipio Empregador", "categorica", 29,
       "Unidade da Federacao do municipio do empregador."),
    _v("Data Acidente", "data", None, "Data do acidente de trabalho registrada na CAT."),
    _v("Data Afastamento", "data", None,
       "Data em que o segurado se afastou do trabalho por causa do acidente."),
    _v("Data DDB", "data", None, "Data do despacho do beneficio."),
    _v("Data Nascimento", "data", None, "Data de nascimento do segurado."),
    _v("Data Emissao da CAT", "data", None, "Data de emissao da CAT."),
)

POR_ROTULO: dict[str, Variavel] = {v.rotulo: v for v in VARIAVEIS}


def colunas_de_data() -> tuple[str, ...]:
    """Rotulos das variaveis que sao datas no formato AAAAMMDD."""
    return tuple(v.rotulo for v in VARIAVEIS if v.e_data)


def colunas_categoricas() -> tuple[str, ...]:
    """Rotulos das variaveis categoricas."""
    return tuple(v.rotulo for v in VARIAVEIS if not v.e_data)


def converter_datas(serie: pd.Series) -> pd.Series:
    """Converte uma coluna AAAAMMDD (texto ou inteiro) em ``datetime``.

    Valores invalidos ou ausentes viram ``NaT`` em vez de levantar excecao: os
    microdados trazem datas em branco e sentinelas como ``0`` e ``99999999``.
    """
    texto = serie.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    texto = texto.where(texto.str.fullmatch(r"\d{8}"), other=pd.NA)
    return pd.to_datetime(texto, format=FORMATO_DATA, errors="coerce")


def como_dataframe() -> pd.DataFrame:
    """Devolve o dicionario de dados como um ``DataFrame``."""
    return pd.DataFrame(
        [
            {
                "rotulo": v.rotulo,
                "tipo": v.tipo,
                "categorias": v.categorias,
                "descricao": v.descricao,
            }
            for v in VARIAVEIS
        ]
    )
