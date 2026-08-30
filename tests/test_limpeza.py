"""Testes das decisoes de limpeza."""

import pandas as pd

from acidentes_trabalho.dados import limpeza


def test_marca_nao_classificado_com_variacoes_de_encoding():
    df = pd.DataFrame({"sexo": pd.array(["Feminino", "{ñ class}", "{n class}", "{ class}"],
                                        dtype="string")})

    limpo = limpeza.marcar_sentinelas(df)

    assert limpo["sexo"][0] == "Feminino"
    assert limpo["sexo"][1:].isna().all()


def test_marca_zerado_como_nulo():
    df = pd.DataFrame({"uf_empregador": pd.array(["Paraná", "Zerado"], dtype="string")})

    assert limpeza.marcar_sentinelas(df)["uf_empregador"].tolist() == ["Paraná", pd.NA]


def test_nao_confunde_texto_parecido_com_sentinela():
    df = pd.DataFrame({"cbo_descricao": pd.array(
        ["Classificador de Graos", "Zerador", "{muito class}"], dtype="string")})

    limpo = limpeza.marcar_sentinelas(df)

    assert limpo["cbo_descricao"].notna().all()


def test_nao_altera_colunas_nao_textuais():
    df = pd.DataFrame({
        "data_acidente": pd.to_datetime(["2024-01-02"]),
        "sexo": pd.array(["{ñ class}"], dtype="string"),
    })

    limpo = limpeza.marcar_sentinelas(df)

    assert limpo["data_acidente"][0] == pd.Timestamp("2024-01-02")
    assert pd.isna(limpo["sexo"][0])


def test_marcar_sentinelas_nao_altera_o_dataframe_original():
    df = pd.DataFrame({"sexo": pd.array(["{ñ class}"], dtype="string")})

    limpeza.marcar_sentinelas(df)

    assert df["sexo"][0] == "{ñ class}"


def test_descarta_uf_do_acidente_por_estar_corrompida():
    df = pd.DataFrame({"uf_acidente": ["Maranhão"], "uf_empregador": ["São Paulo"]})

    resultado = limpeza.descartar_colunas_nao_confiaveis(df)

    assert "uf_acidente" not in resultado.columns
    assert "uf_empregador" in resultado.columns


def test_descartar_e_tolerante_a_coluna_ausente():
    df = pd.DataFrame({"uf_empregador": ["São Paulo"]})

    assert list(limpeza.descartar_colunas_nao_confiaveis(df).columns) == ["uf_empregador"]


def test_limpar_encadeia_as_decisoes():
    df = pd.DataFrame({
        "uf_acidente": pd.array(["Maranhão"], dtype="string"),
        "uf_empregador": pd.array(["Zerado"], dtype="string"),
    })

    limpo = limpeza.limpar(df)

    assert "uf_acidente" not in limpo.columns
    assert pd.isna(limpo["uf_empregador"][0])


def test_limpar_pode_preservar_as_colunas_nao_confiaveis():
    df = pd.DataFrame({"uf_acidente": pd.array(["Maranhão"], dtype="string")})

    assert "uf_acidente" in limpeza.limpar(df, descartar=False).columns
