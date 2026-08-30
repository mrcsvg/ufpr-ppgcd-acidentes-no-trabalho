"""Testes das variaveis derivadas."""

import pandas as pd

from acidentes_trabalho.dados import derivadas


def test_extrai_codigo_e_nome_do_municipio():
    serie = pd.Series(["316860-Teófilo Otoni", "354730-Santana de Pa"], dtype="string")

    assert derivadas.codigo_municipio(serie).tolist() == ["316860", "354730"]
    assert derivadas.nome_municipio(serie).tolist() == ["Teófilo Otoni", "Santana de Pa"]


def test_codigo_do_municipio_sobrevive_ao_nome_truncado():
    """O nome vem cortado em 20 caracteres, mas o codigo nunca."""
    serie = pd.Series(
        ["241200-São Gonçalo do", "241200-São Gonçalo do Amarante-Rn"], dtype="string"
    )

    assert derivadas.codigo_municipio(serie).nunique() == 1


def test_uf_vem_do_codigo_e_nao_do_rotulo():
    serie = pd.Series(["316860-x", "354730-y", "410690-z", "430010-w"], dtype="string")

    assert derivadas.uf_do_codigo_municipio(serie).tolist() == ["MG", "SP", "PR", "RS"]


def test_uf_invalida_vira_nulo_em_vez_de_sigla_inventada():
    serie = pd.Series(["999999-x", "sem codigo", None], dtype="string")

    assert derivadas.uf_do_codigo_municipio(serie).isna().all()


def test_cobre_as_27_unidades_da_federacao():
    assert len(derivadas.UF_POR_CODIGO) == 27
    assert len(set(derivadas.UF_POR_CODIGO.values())) == 27


def test_idade_em_anos_completos():
    acidente = pd.to_datetime(pd.Series(["2024-01-02", "2024-01-02"]))
    nascimento = pd.to_datetime(pd.Series(["1995-02-13", "1995-01-01"]))

    assert derivadas.idade(acidente, nascimento).tolist() == [28.0, 29.0]


def test_idade_implausivel_vira_nulo():
    acidente = pd.to_datetime(pd.Series(["2024-01-02"] * 4))
    nascimento = pd.to_datetime(pd.Series(["2020-01-01", "1850-01-01", "2015-01-01", "1990-01-01"]))

    resultado = derivadas.idade(acidente, nascimento)

    assert resultado.isna().tolist() == [True, True, True, False]


def test_idade_no_limite_legal_de_14_anos_e_mantida():
    """14 anos e o minimo para aprendiz no Brasil: e valor plausivel, nao erro."""
    acidente = pd.to_datetime(pd.Series(["2024-01-02", "2024-01-02"]))
    nascimento = pd.to_datetime(pd.Series(["2010-01-01", "2010-06-01"]))

    resultado = derivadas.idade(acidente, nascimento)

    assert resultado[0] == 14
    assert pd.isna(resultado[1]), "13 anos fica fora"


def test_idade_com_data_ausente_vira_nulo():
    acidente = pd.to_datetime(pd.Series(["2024-01-02", None]))
    nascimento = pd.to_datetime(pd.Series([None, "1990-01-01"]))

    assert derivadas.idade(acidente, nascimento).isna().all()


def test_acrescentar_adiciona_as_colunas_esperadas():
    df = pd.DataFrame({
        "municipio_empregador": pd.array(["316860-Teófilo Otoni"], dtype="string"),
        "data_acidente": pd.to_datetime(["2024-03-15"]),
        "data_nascimento": pd.to_datetime(["1990-01-01"]),
    })

    novo = derivadas.acrescentar(df)

    assert novo["codigo_municipio_empregador"][0] == "316860"
    assert novo["uf_empregador_sigla"][0] == "MG"
    assert novo["ano_acidente"][0] == 2024
    assert novo["mes_acidente"][0] == 3
    assert novo["idade_acidente"][0] == 34
    assert "municipio_empregador" in novo.columns, "as colunas originais sao preservadas"
