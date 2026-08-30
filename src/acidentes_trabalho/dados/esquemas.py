"""Leitura unificada dos CSVs de CAT, que nao compartilham um esquema unico.

Os 61 arquivos do acervo trazem cinco cabecalhos diferentes, que se reduzem a
quatro leiautes de colunas (dois deles diferem so no encoding). Alem de variar o
numero de colunas, **os rotulos mentem em alguns arquivos**: ha colunas rotuladas
``Data Acidente`` que repetem a competencia, e leiautes em que ``Data Despacho
Beneficio`` e ``Data Emissao CAT`` sumiram e o rotulo remanescente nao corresponde
ao conteudo.

Por isso o mapeamento e **posicional**, ancorado no cabecalho reconhecido, e nao
por nome de coluna. Colunas ausentes em um leiaute saem como nulas, para que todos
os arquivos empilhem no mesmo formato.
"""

from __future__ import annotations

import codecs
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from acidentes_trabalho.dados import datas

SEPARADOR = ";"

# Colunas canonicas de data, convertidas com DD/MM/AAAA.
COLUNAS_DATA = (
    "data_acidente",
    "data_afastamento",
    "data_despacho_beneficio",
    "data_nascimento",
    "data_emissao_cat",
)

# Colunas de proveniencia acrescentadas na leitura.
COLUNAS_PROVENIENCIA = ("arquivo", "leiaute")


@dataclass(frozen=True)
class Leiaute:
    """Um arranjo de colunas encontrado no acervo.

    ``colunas`` mapeia cada posicao do CSV ao nome canonico; ``None`` descarta a
    posicao (coluna redundante ou com rotulo que nao corresponde ao conteudo).
    """

    nome: str
    colunas: tuple[str | None, ...]
    observacao: str

    @property
    def n_colunas(self) -> int:
        return len(self.colunas)


# Posicao 1 (indice 0) e sempre o agente causador; a posicao 2 traz ora a
# competencia (AAAA/MM), ora uma repeticao da data do acidente - resolvida na
# leitura, nao aqui.
_COMUM_INICIO = ("agente_causador", "competencia")

V27 = Leiaute(
    nome="v27",
    colunas=(
        *_COMUM_INICIO,
        "cbo_codigo", "cbo_descricao",
        "cid10_codigo", "cid10_descricao",
        "cnae_codigo", "cnae_descricao",
        "emitente_cat", "especie_beneficio", "filiacao_segurado", "indica_obito",
        "municipio_empregador", "natureza_lesao", "origem_cadastramento",
        "parte_corpo_atingida", "sexo", "tipo_acidente",
        "uf_acidente", "uf_empregador",
        "data_afastamento", "data_despacho_beneficio", "data_acidente",
        "data_nascimento", "data_emissao_cat",
        "tipo_empregador", "cnpj_cei_empregador",
    ),
    observacao="Leiaute mais completo: unico com tipo_empregador.",
)

V24_SEM_DESCRICAO = Leiaute(
    nome="v24_sem_descricao",
    colunas=(
        *_COMUM_INICIO,
        "cbo_codigo",
        "cid10_codigo",
        "cnae_codigo", "cnae_descricao",
        "emitente_cat", "especie_beneficio", "filiacao_segurado", "indica_obito",
        "municipio_empregador", "natureza_lesao", "origem_cadastramento",
        "parte_corpo_atingida", "sexo", "tipo_acidente",
        "uf_acidente", "uf_empregador",
        None,  # rotulada "Data Acidente", repete a competencia da posicao 2
        "data_despacho_beneficio", "data_acidente",
        "data_nascimento", "data_emissao_cat",
        "cnpj_cei_empregador",
    ),
    observacao="Sem descricao de CBO e CID-10, e sem data de afastamento.",
)

V24_TRUNCADO = Leiaute(
    nome="v24_truncado",
    colunas=(
        *_COMUM_INICIO,
        "cbo_codigo", "cbo_descricao",
        "cid10_codigo", "cid10_descricao",
        "cnae_codigo", "cnae_descricao",
        "emitente_cat", "especie_beneficio", "filiacao_segurado", "indica_obito",
        "municipio_empregador", "natureza_lesao", "origem_cadastramento",
        "parte_corpo_atingida", "sexo", "tipo_acidente",
        "uf_acidente", "uf_empregador",
        "data_afastamento", "data_acidente",
        "data_nascimento",
        None,  # rotulada "Data Acidente", repete a data do acidente
    ),
    observacao="Exportacao truncada: perdeu despacho do beneficio e emissao da CAT.",
)

V25_ANTIGO = Leiaute(
    nome="v25_antigo",
    colunas=(
        *_COMUM_INICIO,
        "cbo_codigo", "cbo_descricao",
        "cid10_codigo", "cid10_descricao",
        "cnae_codigo", "cnae_descricao",
        "emitente_cat", "especie_beneficio", "filiacao_segurado", "indica_obito",
        "municipio_empregador", "natureza_lesao", "origem_cadastramento",
        "parte_corpo_atingida", "sexo", "tipo_acidente",
        "uf_acidente", "uf_empregador",
        "data_afastamento", "data_despacho_beneficio", "data_acidente",
        "data_nascimento", "data_emissao_cat",
    ),
    observacao="Arquivos antigos (2018-2020): sem CNPJ e sem tipo de empregador.",
)

LEIAUTES = (V27, V24_SEM_DESCRICAO, V24_TRUNCADO, V25_ANTIGO)

# Todas as colunas canonicas, na ordem do leiaute mais completo.
COLUNAS_CANONICAS: tuple[str, ...] = tuple(c for c in V27.colunas if c)


def _sem_acento(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def normalizar_nome(coluna: str) -> str:
    """Reduz um rotulo de coluna a uma forma comparavel entre arquivos.

    Remove BOM, acentos e o sufixo ``_N`` que uma das exportacoes acrescentou para
    desambiguar nomes repetidos, e colapsa espacos.
    """
    texto = coluna.replace("﻿", "").strip()
    texto = re.sub(r"_\d+$", "", texto)
    texto = _sem_acento(texto).lower()
    return re.sub(r"\s+", " ", texto)


# Assinatura (cabecalho normalizado) de cada leiaute conhecido.
_ASSINATURAS: dict[tuple[str, ...], Leiaute] = {}


def _registrar(leiaute: Leiaute, cabecalho: str) -> None:
    _ASSINATURAS[tuple(normalizar_nome(c) for c in cabecalho.split(SEPARADOR))] = leiaute


_registrar(
    V27,
    "Agente  Causador  Acidente;Data Acidente;CBO;CBO;CID-10;CID-10;CNAE2.0 Empregador;"
    "CNAE2.0 Empregador;Emitente CAT;Espécie do benefício;Filiação Segurado;"
    "Indica Óbito Acidente;Munic Empr;Natureza da Lesão;Origem de Cadastramento CAT;"
    "Parte Corpo Atingida;Sexo;Tipo do Acidente;UF  Munic.  Acidente;UF Munic. Empregador;"
    "Data  Afastamento;Data Despacho Benefício;Data Acidente;Data Nascimento;"
    "Data Emissão CAT;Tipo de Empregador;CNPJ/CEI Empregador",
)
_registrar(
    V24_SEM_DESCRICAO,
    "Agente  Causador  Acidente;Data Acidente;CBO;CID-10;CNAE2.0 Empregador;"
    "CNAE2.0 Empregador;Emitente CAT;Espécie do benefício;Filiação Segurado;"
    "Indica Óbito Acidente;Munic Empr;Natureza da Lesão;Origem de Cadastramento CAT;"
    "Parte Corpo Atingida;Sexo;Tipo do Acidente;UF  Munic.  Acidente;UF Munic. Empregador;"
    "Data Acidente;Data Despacho Benefício;Data Acidente;Data Nascimento;Data Emissão CAT;"
    "CNPJ/CEI Empregador",
)
_registrar(
    V24_TRUNCADO,
    "Agente  Causador  Acidente;Data Acidente;CBO;CBO;CID-10;CID-10;CNAE2.0 Empregador;"
    "CNAE2.0 Empregador;Emitente CAT;Espécie do benefício;Filiação Segurado;"
    "Indica Óbito Acidente;Munic Empr;Natureza da Lesão;Origem de Cadastramento CAT;"
    "Parte Corpo Atingida;Sexo;Tipo do Acidente;UF  Munic.  Acidente;UF Munic. Empregador;"
    "Data  Afastamento;Data Acidente;Data Nascimento;Data Acidente",
)
_registrar(
    V25_ANTIGO,
    "Agente  Causador  Acidente;Data Acidente;CBO;CBO;CID-10;CID-10;CNAE2.0 Empregador;"
    "CNAE2.0 Empregador;Emitente CAT;Espécie do benefício;Filiação Segurado;"
    "Indica acidente;Munic Empr;Natureza da Lesão;Origem de Cadastramento CAT;"
    "Parte Corpo Atingida;Sexo;Tipo do Acidente;UF  Munic.  Acidente;UF Munic. Empregador;"
    "Data  Afastamento;Data Despacho Benefício;Data Acidente;Data Nascimento;Data Emissão CAT",
)


class LeiauteDesconhecido(ValueError):
    """O cabecalho do arquivo nao corresponde a nenhum leiaute conhecido."""


def detectar_encoding(caminho: Path, amostra: int = 1_000_000) -> str:
    """Descobre o encoding do arquivo: ``utf-8-sig``, ``utf-8`` ou ``latin-1``.

    Tres arquivos do acervo sao UTF-8 com BOM; os demais sao latin-1. A distincao
    importa porque latin-1 decodifica qualquer byte sem erro: ler um arquivo UTF-8
    como latin-1 nao falha, so entrega texto corrompido ("EspÃ©cie"). Por isso a
    ordem e: BOM, depois UTF-8 estrito, e latin-1 apenas como ultimo recurso.

    A amostra e decodificada de forma incremental, entao um caractere multibyte
    cortado no fim do trecho lido nao e confundido com erro de encoding.
    """
    with Path(caminho).open("rb") as arquivo:
        inicio = arquivo.read(amostra)

    if inicio.startswith(codecs.BOM_UTF8):
        return "utf-8-sig"
    try:
        codecs.getincrementaldecoder("utf-8")().decode(inicio, final=False)
    except UnicodeDecodeError:
        return "latin-1"
    return "utf-8"


def ler_cabecalho(caminho: Path) -> list[str]:
    """Le apenas a primeira linha do arquivo, ja decodificada."""
    encoding = detectar_encoding(caminho)
    with Path(caminho).open("r", encoding=encoding, newline="") as arquivo:
        return arquivo.readline().strip().split(SEPARADOR)


def identificar_leiaute(caminho: Path) -> Leiaute:
    """Descobre qual leiaute o arquivo usa, pelo cabecalho.

    Raises:
        LeiauteDesconhecido: se o cabecalho nao for um dos quatro conhecidos.
    """
    assinatura = tuple(normalizar_nome(c) for c in ler_cabecalho(caminho))
    leiaute = _ASSINATURAS.get(assinatura)
    if leiaute is None:
        raise LeiauteDesconhecido(
            f"{Path(caminho).name}: cabecalho com {len(assinatura)} colunas nao reconhecido"
        )
    return leiaute


def ler(caminho: Path | str, nrows: int | None = None) -> pd.DataFrame:
    """Le um CSV de CAT e devolve o DataFrame no formato canonico.

    Todas as colunas canonicas estao presentes, mesmo as ausentes no leiaute do
    arquivo (nesse caso, nulas). As datas ja vem convertidas, o texto de
    preenchimento e removido e duas colunas de proveniencia sao acrescentadas:
    ``arquivo`` e ``leiaute``.
    """
    caminho = Path(caminho)
    leiaute = identificar_leiaute(caminho)

    bruto = pd.read_csv(
        caminho,
        sep=SEPARADOR,
        encoding=detectar_encoding(caminho),
        header=None,
        skiprows=1,  # o cabecalho e descartado: o mapeamento e posicional
        names=range(leiaute.n_colunas),
        dtype="string",
        nrows=nrows,
        na_filter=False,
    )

    df = pd.DataFrame(index=bruto.index)
    for posicao, nome in enumerate(leiaute.colunas):
        if nome and nome not in df.columns:
            # Os campos vem preenchidos com espaco ate a largura fixa da coluna.
            texto = bruto[posicao].str.strip()
            df[nome] = texto.where(texto != "", other=pd.NA)

    for coluna in COLUNAS_CANONICAS:
        if coluna not in df.columns:
            # dtype explicito: sem ele a coluna vazia vira object e contamina o Parquet
            df[coluna] = pd.Series(pd.NA, index=df.index, dtype="string")

    # A posicao 2 traz competencia em alguns leiautes e uma repeticao da data do
    # acidente em outros; so vale como competencia no primeiro caso.
    bruta_competencia = df["competencia"]
    df["competencia"] = (
        datas.para_competencia(bruta_competencia)
        if datas.e_competencia(bruta_competencia)
        else pd.NaT
    )

    for coluna in COLUNAS_DATA:
        df[coluna] = datas.para_data(df[coluna])

    df["arquivo"] = caminho.name
    df["leiaute"] = leiaute.nome
    return df[[*COLUNAS_CANONICAS, *COLUNAS_PROVENIENCIA]]
