"""Testes da conversao de datas dos microdados de CAT."""

import pandas as pd

from acidentes_trabalho.dados import datas


def test_para_data_converte_dd_mm_aaaa():
    serie = pd.Series(["02/01/2024", "29/10/2025"])

    convertido = datas.para_data(serie)

    assert convertido[0] == pd.Timestamp("2024-01-02")
    assert convertido[1] == pd.Timestamp("2025-10-29")


def test_para_data_trata_sentinelas_e_lixo_como_nat():
    serie = pd.Series(["00/00/0000", "0000/00", "", None, "32/13/2024", "{x class}"])

    assert datas.para_data(serie).isna().all()


def test_para_data_ignora_espaco_de_preenchimento():
    assert datas.para_data(pd.Series(["  02/01/2024  "]))[0] == pd.Timestamp("2024-01-02")


def test_para_competencia_converte_aaaa_mm():
    convertido = datas.para_competencia(pd.Series(["2022/01", "2020/12"]))

    assert convertido[0] == pd.Period("2022-01", freq="M")
    assert convertido[1] == pd.Period("2020-12", freq="M")


def test_para_competencia_trata_sentinela_como_nat():
    assert datas.para_competencia(pd.Series(["0000/00", "", None])).isna().all()


def test_para_competencia_nao_aceita_data_exata():
    assert datas.para_competencia(pd.Series(["02/01/2024"])).isna().all()


def test_e_competencia_distingue_os_dois_formatos():
    assert datas.e_competencia(pd.Series(["2022/01", "2022/02"]))
    assert not datas.e_competencia(pd.Series(["02/01/2024", "03/01/2024"]))


def test_e_competencia_ignora_sentinelas_no_inicio():
    assert datas.e_competencia(pd.Series(["0000/00", "0000/00", "2020/10"]))
    assert not datas.e_competencia(pd.Series(["00/00/0000", "00/00/0000"]))
