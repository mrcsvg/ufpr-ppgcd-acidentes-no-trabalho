"""Testes das funcoes de leitura e escrita de dados."""

import pandas as pd
import pytest

from acidentes_trabalho.dados import io


def test_caminho_usa_a_camada_pedida():
    assert io.caminho("x.csv", "raw").parent.name == "raw"
    assert io.caminho("x.parquet", "processed").parent.name == "processed"


def test_caminho_rejeita_camada_invalida():
    with pytest.raises(ValueError, match="camada desconhecida"):
        io.caminho("x.csv", "inexistente")


def test_ida_e_volta_em_parquet(tmp_path, monkeypatch):
    monkeypatch.setitem(io.CAMADAS, "processed", tmp_path)
    df = pd.DataFrame({"uf": ["PR", "SP"], "cat": [10, 20]})

    destino = io.salvar_parquet(df, "amostra.parquet")

    assert destino.is_file()
    pd.testing.assert_frame_equal(io.ler_parquet("amostra.parquet"), df)


def test_ler_csv_usa_ponto_e_virgula_por_padrao(tmp_path, monkeypatch):
    monkeypatch.setitem(io.CAMADAS, "raw", tmp_path)
    (tmp_path / "cat.csv").write_text("uf;total\nPR;10\n", encoding="latin-1")

    df = io.ler_csv("cat.csv")

    assert list(df.columns) == ["uf", "total"]
    assert df.loc[0, "total"] == 10
