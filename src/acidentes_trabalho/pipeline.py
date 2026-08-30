"""Pipeline que transforma os CSVs crus em uma base unica consolidada.

Quatro etapas, cada uma retomavel de forma independente::

    baixar      bucket GCS            -> data/raw/*.csv
    normalizar  data/raw/*.csv        -> data/interim/*.parquet
    consolidar  data/interim/*.parquet-> data/processed/cat.parquet
    relatorio   data/processed        -> reports/relatorio-dados.md

A consolidacao grava em fluxo, um arquivo por vez, sem nunca carregar a base
inteira na memoria: sao milhoes de registros e o pipeline precisa rodar num
notebook comum, nao so numa maquina grande.

Uso::

    python -m acidentes_trabalho.pipeline              # tudo
    python -m acidentes_trabalho.pipeline normalizar   # so uma etapa
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from acidentes_trabalho.config import (
    DADOS_INTERIM,
    DADOS_PROCESSED,
    DADOS_RAW,
    RELATORIOS,
    garantir_diretorios,
)
from acidentes_trabalho.dados import derivadas, esquemas, gcs, limpeza

log = logging.getLogger(__name__)

PREFIXO_BUCKET = "cats/"

# Coluna acrescentada na consolidacao marcando as republicacoes.
COLUNA_DUPLICATA = "duplicata"

# Colunas que nao entram na comparacao de conteudo: dizem de onde a linha veio,
# nao o que ela registra.
COLUNAS_PROVENIENCIA = ("arquivo", "leiaute", COLUNA_DUPLICATA)
BASE_CONSOLIDADA = DADOS_PROCESSED / "cat.parquet"
ARQUIVO_RELATORIO = RELATORIOS / "relatorio-dados.md"

# Colunas de baixa cardinalidade, guardadas como dicionario no Parquet. Reduz o
# arquivo em varias vezes e acelera os agrupamentos do relatorio.
COLUNAS_CATEGORICAS = (
    "agente_causador", "cbo_descricao", "cid10_descricao", "cnae_codigo",
    "cnae_descricao", "emitente_cat", "especie_beneficio", "filiacao_segurado",
    "indica_obito", "natureza_lesao", "origem_cadastramento", "parte_corpo_atingida",
    "sexo", "tipo_acidente", "uf_acidente", "uf_empregador", "uf_empregador_sigla",
    "tipo_empregador", "leiaute", "arquivo",
)


def baixar(bucket: str | None = None, refazer: bool = False) -> list[Path]:
    """Etapa 1: traz do bucket todos os CSVs que ainda faltam em ``data/raw``."""
    garantir_diretorios()
    caminhos = gcs.sincronizar(bucket, PREFIXO_BUCKET, DADOS_RAW, refazer=refazer)
    log.info("baixar: %d arquivos em %s", len(caminhos), DADOS_RAW)
    return caminhos


def normalizar_um(origem: Path, destino: Path | None = None) -> Path:
    """Normaliza um CSV: unifica o leiaute, limpa e acrescenta as derivadas."""
    destino = destino or DADOS_INTERIM / f"{origem.stem}.parquet"
    destino.parent.mkdir(parents=True, exist_ok=True)

    df = esquemas.ler(origem)
    # descartar=False: a base consolidada e o registro fiel do acervo, e manter a
    # coluna corrompida permite conferir o diagnostico em vez de ter que confiar
    # nele. O descarte e decisao de analise - use limpeza.limpar() ao carregar.
    df = limpeza.limpar(df, descartar=False)
    df = derivadas.acrescentar(df)
    _aplicar_categorias(df).to_parquet(destino, index=False)
    return destino


def normalizar(refazer: bool = False) -> list[Path]:
    """Etapa 2: normaliza cada CSV de ``data/raw`` em um Parquet de ``data/interim``.

    Pula os que ja estao normalizados e mais novos que a origem, para que o
    pipeline possa ser retomado depois de uma interrupcao. A comparacao olha so
    as datas dos arquivos: **mudanca no codigo de normalizacao nao invalida os
    intermediarios**, entao use ``refazer=True`` (ou ``--refazer``) depois de
    alterar ``esquemas``, ``limpeza`` ou ``derivadas``.
    """
    garantir_diretorios()
    destinos = []
    for origem in sorted(DADOS_RAW.glob("*.csv")):
        destino = DADOS_INTERIM / f"{origem.stem}.parquet"
        if not refazer and destino.exists() and destino.stat().st_mtime >= origem.stat().st_mtime:
            log.debug("normalizar: %s ja atualizado", destino.name)
        else:
            normalizar_um(origem, destino)
            log.info("normalizar: %s", destino.name)
        destinos.append(destino)
    return destinos


def _aplicar_categorias(df: pd.DataFrame) -> pd.DataFrame:
    """Converte as colunas de baixa cardinalidade para ``category``."""
    convertido = df.copy()
    for coluna in COLUNAS_CATEGORICAS:
        if coluna in convertido.columns:
            convertido[coluna] = convertido[coluna].astype("category")
    return convertido


def _esquema_unificado(caminhos: list[Path]) -> pa.Schema:
    """Monta um esquema Arrow valido para todos os arquivos.

    Cada Parquet intermediario carrega o dicionario de categorias do proprio
    arquivo, e eles diferem entre si. Para empilhar sem conflito, as colunas de
    dicionario voltam a ser texto simples no esquema comum.
    """
    campos: dict[str, pa.DataType] = {}
    for caminho in caminhos:
        for campo in pq.read_schema(caminho):
            tipo = pa.string() if pa.types.is_dictionary(campo.type) else campo.type
            campos.setdefault(campo.name, tipo)
    return pa.schema([pa.field(nome, tipo) for nome, tipo in campos.items()])


def _lotes(caminhos: list[Path], esquema: pa.Schema) -> Iterator[pa.Table]:
    for caminho in caminhos:
        tabela = pq.read_table(caminho)
        for nome in esquema.names:
            if nome not in tabela.column_names:
                tabela = tabela.append_column(
                    nome, pa.nulls(tabela.num_rows, esquema.field(nome).type)
                )
        yield tabela.select(esquema.names).cast(esquema)


def _marcar_republicacoes(caminhos: list[Path], esquema: pa.Schema) -> list[pd.Series]:
    """Aponta, para cada arquivo, quais linhas ja apareceram em um arquivo anterior.

    Os arquivos do acervo sao **janelas sobrepostas de mes de emissao**, nao
    particoes disjuntas: a competencia 202208 cobre emissoes de agosto a novembro
    de 2022, e a 202207 ja cobria julho a novembro — o arquivo inteiro e
    republicacao. Empilhar tudo superconta os registros repetidos.

    A deteccao usa hash de 64 bits do conteudo da linha, para nao precisar da base
    inteira em memoria: guarda-se um inteiro por linha em vez do registro todo. Em
    3,9 milhoes de linhas a chance de duas diferentes colidirem e da ordem de
    1 em 2 milhoes, aceitavel para marcar (nao apagar) uma linha.
    """
    conteudo = [c for c in esquema.names if c not in COLUNAS_PROVENIENCIA]
    hashes, tamanhos = [], []
    for tabela in _lotes(caminhos, esquema):
        df = tabela.select(conteudo).to_pandas()
        hashes.append(pd.util.hash_pandas_object(df, index=False).to_numpy())
        tamanhos.append(len(df))

    juntos = pd.Series(np.concatenate(hashes)) if hashes else pd.Series(dtype="uint64")
    repetida = juntos.duplicated(keep="first")

    marcas, inicio = [], 0
    for tamanho in tamanhos:
        marcas.append(repetida.iloc[inicio : inicio + tamanho].reset_index(drop=True))
        inicio += tamanho
    return marcas


def consolidar(destino: Path | None = None) -> Path:
    """Etapa 3: empilha os Parquet intermediarios em uma base unica.

    Grava em fluxo, um arquivo por vez, entao o consumo de memoria acompanha o
    maior arquivo e nao o total.

    O destino e resolvido na chamada, e nao como valor padrao do argumento: um
    default e avaliado uma unica vez, na definicao da funcao, e congelaria o
    caminho de saida mesmo que a configuracao mudasse depois.
    """
    destino = destino or BASE_CONSOLIDADA
    garantir_diretorios()
    caminhos = sorted(DADOS_INTERIM.glob("*.parquet"))
    if not caminhos:
        raise FileNotFoundError(f"nada em {DADOS_INTERIM}: rode a etapa 'normalizar' antes")

    destino.parent.mkdir(parents=True, exist_ok=True)
    esquema = _esquema_unificado(caminhos)
    marcas = _marcar_republicacoes(caminhos, esquema)
    esquema_saida = esquema.append(pa.field(COLUNA_DUPLICATA, pa.bool_()))

    total = duplicadas = 0
    with pq.ParquetWriter(destino, esquema_saida, compression="zstd") as escritor:
        for tabela, marca in zip(_lotes(caminhos, esquema), marcas, strict=True):
            tabela = tabela.append_column(
                COLUNA_DUPLICATA, pa.array(marca.to_numpy(), type=pa.bool_())
            )
            escritor.write_table(tabela)
            total += tabela.num_rows
            duplicadas += int(marca.sum())
    log.info(
        "consolidar: %d registros em %s (%d republicacoes marcadas, %.1f%%)",
        total, destino, duplicadas, 100 * duplicadas / total if total else 0,
    )
    return destino


def carregar(
    colunas: list[str] | None = None,
    caminho: Path | None = None,
    *,
    unicos: bool = False,
) -> pd.DataFrame:
    """Le a base consolidada; ``colunas`` limita a leitura ao necessario.

    Args:
        unicos: se ``True``, descarta as republicacoes marcadas em
            ``duplicata`` — o que quase sempre e o que se quer ao **contar**
            acidentes, ja que os arquivos do acervo se sobrepoem.
    """
    caminho = caminho or BASE_CONSOLIDADA
    if not caminho.exists():
        raise FileNotFoundError(f"{caminho} nao existe: rode o pipeline antes")

    pedidas = colunas
    if unicos and colunas is not None and COLUNA_DUPLICATA not in colunas:
        pedidas = [*colunas, COLUNA_DUPLICATA]

    df = pq.read_table(caminho, columns=pedidas).to_pandas()
    if unicos:
        df = df[~df[COLUNA_DUPLICATA]].reset_index(drop=True)
        if colunas is not None:
            df = df[colunas]
    return df


def executar(bucket: str | None = None, refazer: bool = False) -> Path:
    """Roda as quatro etapas em sequencia e devolve o caminho da base."""
    from acidentes_trabalho import relatorio

    baixar(bucket, refazer=refazer)
    normalizar(refazer=refazer)
    consolidar()
    relatorio.gerar()
    return BASE_CONSOLIDADA


def _main(argv: list[str] | None = None) -> int:
    import argparse

    from acidentes_trabalho import relatorio

    etapas = {
        "baixar": lambda refazer: baixar(refazer=refazer),
        "normalizar": normalizar,
        "consolidar": lambda refazer: consolidar(),
        "relatorio": lambda refazer: relatorio.gerar(),
        "tudo": lambda refazer: executar(refazer=refazer),
    }

    parser = argparse.ArgumentParser(
        prog="python -m acidentes_trabalho.pipeline",
        description="Baixa, normaliza e consolida os microdados de CAT.",
    )
    parser.add_argument("etapa", nargs="?", default="tudo", choices=sorted(etapas))
    parser.add_argument(
        "--refazer",
        action="store_true",
        help="ignora o que ja esta pronto; necessario apos mudar o codigo de normalizacao",
    )
    parser.add_argument("-v", "--verboso", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verboso else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    resultado = etapas[args.etapa](args.refazer)
    if isinstance(resultado, Path):
        print(resultado)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
