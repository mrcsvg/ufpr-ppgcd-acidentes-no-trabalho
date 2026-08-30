"""Testes do pipeline de normalizacao e consolidacao.

Usam os mesmos CSVs em miniatura de ``test_esquemas``, redirecionando as pastas
do projeto para ``tmp_path`` — nenhum teste toca os dados reais nem a rede.
"""

import pandas as pd
import pyarrow.parquet as pq
import pytest

from acidentes_trabalho import pipeline
from tests.test_esquemas import CABECALHOS, escrever


@pytest.fixture
def projeto(tmp_path, monkeypatch):
    """Aponta as pastas do pipeline para tmp_path e devolve os caminhos."""
    raw, interim, processed = tmp_path / "raw", tmp_path / "interim", tmp_path / "processed"
    for pasta in (raw, interim, processed):
        pasta.mkdir()
    monkeypatch.setattr(pipeline, "DADOS_RAW", raw)
    monkeypatch.setattr(pipeline, "DADOS_INTERIM", interim)
    monkeypatch.setattr(pipeline, "DADOS_PROCESSED", processed)
    # Constantes fixadas na importacao: sem redirecionar, o teste escreveria na
    # base real do projeto.
    monkeypatch.setattr(pipeline, "BASE_CONSOLIDADA", processed / "cat.parquet")
    monkeypatch.setattr(pipeline, "ARQUIVO_RELATORIO", tmp_path / "relatorio.md")
    monkeypatch.setattr(pipeline, "garantir_diretorios", lambda: None)
    return raw, interim, processed


def povoar(raw, leiautes=tuple(CABECALHOS), linhas=3):
    for leiaute in leiautes:
        escrever(raw, leiaute, nome=f"{leiaute}.csv", linhas=linhas)


def test_normalizar_gera_um_parquet_por_csv(projeto):
    raw, interim, _ = projeto
    povoar(raw)

    destinos = pipeline.normalizar()

    assert len(destinos) == len(CABECALHOS)
    assert sorted(p.name for p in interim.glob("*.parquet")) == sorted(
        f"{leiaute}.parquet" for leiaute in CABECALHOS
    )


def test_normalizar_pula_o_que_ja_esta_atualizado(projeto):
    raw, interim, _ = projeto
    povoar(raw, ["v27"])
    pipeline.normalizar()
    marca = (interim / "v27.parquet").stat().st_mtime_ns

    pipeline.normalizar()

    assert (interim / "v27.parquet").stat().st_mtime_ns == marca


def test_normalizar_refaz_quando_pedido(projeto):
    raw, interim, _ = projeto
    povoar(raw, ["v27"])
    pipeline.normalizar()
    marca = (interim / "v27.parquet").stat().st_mtime_ns

    pipeline.normalizar(refazer=True)

    assert (interim / "v27.parquet").stat().st_mtime_ns != marca


def test_normalizar_acrescenta_as_derivadas(projeto):
    raw, interim, _ = projeto
    povoar(raw, ["v27"], linhas=1)

    pipeline.normalizar()
    df = pd.read_parquet(interim / "v27.parquet")

    assert df["uf_empregador_sigla"][0] == "MG"
    assert df["codigo_municipio_empregador"][0] == "316860"
    assert df["ano_acidente"][0] == 2024


def test_consolidar_empilha_leiautes_diferentes(projeto):
    raw, _, processed = projeto
    povoar(raw, linhas=2)
    pipeline.normalizar()

    destino = pipeline.consolidar(processed / "cat.parquet")
    df = pd.read_parquet(destino)

    assert len(df) == 2 * len(CABECALHOS)
    assert set(df["leiaute"]) == set(CABECALHOS)
    assert df["data_acidente"].notna().all()


def test_consolidar_preserva_as_colunas_de_todos_os_leiautes(projeto):
    raw, _, processed = projeto
    povoar(raw)
    pipeline.normalizar()

    df = pd.read_parquet(pipeline.consolidar(processed / "cat.parquet"))

    # tipo_empregador so existe no v27; as demais linhas ficam nulas, nao somem
    assert "tipo_empregador" in df.columns
    assert df.loc[df["leiaute"] == "v27", "tipo_empregador"].notna().all()
    assert df.loc[df["leiaute"] != "v27", "tipo_empregador"].isna().all()


def test_consolidar_sem_intermediarios_avisa_o_que_falta(projeto):
    _, _, processed = projeto

    with pytest.raises(FileNotFoundError, match="normalizar"):
        pipeline.consolidar(processed / "cat.parquet")


def test_consolidar_grava_um_arquivo_por_vez(projeto):
    """A base nao cabe na memoria: cada intermediario vira um grupo de linhas."""
    raw, _, processed = projeto
    povoar(raw, linhas=2)
    pipeline.normalizar()

    destino = pipeline.consolidar(processed / "cat.parquet")

    assert pq.ParquetFile(destino).num_row_groups == len(CABECALHOS)


def test_carregar_le_apenas_as_colunas_pedidas(projeto):
    raw, _, processed = projeto
    povoar(raw, ["v27"])
    pipeline.normalizar()
    destino = pipeline.consolidar(processed / "cat.parquet")

    df = pipeline.carregar(colunas=["sexo", "ano_acidente"], caminho=destino)

    assert list(df.columns) == ["sexo", "ano_acidente"]


def test_carregar_sem_base_avisa_para_rodar_o_pipeline(projeto):
    _, _, processed = projeto

    with pytest.raises(FileNotFoundError, match="pipeline"):
        pipeline.carregar(caminho=processed / "nao-existe.parquet")


def test_sentinelas_nao_sobrevivem_ao_pipeline(projeto, tmp_path):
    """Regressao: o sentinela truncado ("{ñ") passava batido e virava categoria."""
    raw, _, processed = projeto
    linha = (
        "Queda;02/01/2024;322205;{ñ class;S610;Ferim;8610;Atendimento;"
        "Empregador;Pa;Empregado;{ñ;316860-Teófilo Otoni;Corte;Internet;Dedo;Feminino;"
        "Típico;Minas Gerais;Minas Gerais;28/12/2023;00/00/0000;02/01/2024;13/02/1995;"
        "02/01/2024;Cnpj/Cgc;25104902000107"
    )
    (raw / "v27.csv").write_bytes(
        (CABECALHOS["v27"] + "\r\n" + linha + "\r\n").encode("latin-1")
    )

    pipeline.normalizar()
    df = pd.read_parquet(pipeline.consolidar(processed / "cat.parquet"))

    assert pd.isna(df["indica_obito"][0])
    assert pd.isna(df["cbo_descricao"][0])
    assert df["sexo"][0] == "Feminino"


def test_cli_normalizar_com_refazer(projeto, capsys):
    raw, interim, _ = projeto
    povoar(raw, ["v27"])
    pipeline._main(["normalizar"])
    marca = (interim / "v27.parquet").stat().st_mtime_ns

    pipeline._main(["normalizar", "--refazer"])

    assert (interim / "v27.parquet").stat().st_mtime_ns != marca


def test_cli_consolidar_imprime_o_caminho(projeto, capsys):
    raw, _, processed = projeto
    povoar(raw, ["v27"])
    pipeline._main(["normalizar"])
    pipeline._main(["consolidar"])

    saida = capsys.readouterr().out
    assert "cat.parquet" in saida
    assert str(processed) in saida, "a etapa deve gravar na pasta do teste, nao na do projeto"
