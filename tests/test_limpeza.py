"""Testes das decisoes de limpeza."""

import pandas as pd
import pytest

from acidentes_trabalho.dados import limpeza


def test_marca_nao_classificado_com_variacoes_de_encoding():
    df = pd.DataFrame({"sexo": pd.array(["Feminino", "{ñ class}", "{n class}", "{ class}"],
                                        dtype="string")})

    limpo = limpeza.marcar_sentinelas(df)

    assert limpo["sexo"][0] == "Feminino"
    assert limpo["sexo"][1:].isna().all()


def test_sentinelas_convivem_com_nulos_na_coluna():
    """Combinar mascaras que ainda carregam NA quebra quando os backends diferem."""
    df = pd.DataFrame({
        "uf_empregador": pd.array(["Paraná", None, "Zerado", "{ñ class}", None], dtype="string"),
    })

    limpo = limpeza.marcar_sentinelas(df)

    assert limpo["uf_empregador"][0] == "Paraná"
    assert limpo["uf_empregador"][1:].isna().all()


def test_marca_sentinelas_em_coluna_totalmente_nula():
    df = pd.DataFrame({"cbo_descricao": pd.array([None, None], dtype="string")})

    assert limpeza.marcar_sentinelas(df)["cbo_descricao"].isna().all()


def test_marca_zerado_como_nulo():
    df = pd.DataFrame({"uf_empregador": pd.array(["Paraná", "Zerado"], dtype="string")})

    assert limpeza.marcar_sentinelas(df)["uf_empregador"].tolist() == ["Paraná", pd.NA]


def test_nao_confunde_texto_que_apenas_parece_sentinela():
    """Conter "class" ou "Zerado" no meio da palavra nao faz de um valor sentinela."""
    df = pd.DataFrame({"cbo_descricao": pd.array(
        ["Classificador de Graos", "Zerador", "Desclassificado"], dtype="string")})

    assert limpeza.marcar_sentinelas(df)["cbo_descricao"].notna().all()


def test_qualquer_valor_iniciado_por_chave_e_sentinela():
    """Nenhum valor legitimo da base comeca com chave - verificado nos 3,9 M de registros."""
    df = pd.DataFrame({"cbo_descricao": pd.array(
        ["{ñ class}", "{qualquer coisa}", "{"], dtype="string")})

    assert limpeza.marcar_sentinelas(df)["cbo_descricao"].isna().all()


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


def test_marca_sentinela_truncado_pela_largura_fixa():
    """O proprio sentinela chega cortado: "{ñ class}", "{ñ class" e ate "{ñ"."""
    df = pd.DataFrame({"indica_obito": pd.array(
        ["Não", "{ñ class}", "{ñ class", "{ñ", "{", "Sim"], dtype="string")})

    limpo = limpeza.marcar_sentinelas(df)

    assert limpo["indica_obito"].tolist()[0] == "Não"
    assert limpo["indica_obito"][1:5].isna().all()
    assert limpo["indica_obito"].tolist()[5] == "Sim"


@pytest.mark.parametrize("dtype", ["str", "string", "object", "category"])
def test_limpa_em_qualquer_dtype_de_texto(dtype):
    """object, string, str e category: todos aparecem conforme a origem dos dados."""
    df = pd.DataFrame({"sexo": pd.Series(["Feminino", "{ñ class}"], dtype=dtype)})

    limpo = limpeza.marcar_sentinelas(df)

    assert limpo["sexo"].astype("string").tolist() == ["Feminino", pd.NA]


def test_categoria_nao_guarda_o_sentinela_apos_a_limpeza():
    df = pd.DataFrame({"sexo": pd.Series(["Feminino", "{ñ class}"], dtype="category")})

    limpo = limpeza.marcar_sentinelas(df)

    assert isinstance(limpo["sexo"].dtype, pd.CategoricalDtype)
    assert "{ñ class}" not in list(limpo["sexo"].cat.categories)


def test_nao_toca_em_colunas_de_data_nem_numericas():
    df = pd.DataFrame({
        "data_acidente": pd.to_datetime(["2024-01-02"]),
        "competencia": pd.Series([pd.Period("2024-01", "M")]),
        "ano_acidente": pd.Series([2024], dtype="Int16"),
        "idade_acidente": pd.Series([34.0], dtype="Float64"),
    })

    limpo = limpeza.marcar_sentinelas(df)

    assert limpo["data_acidente"][0] == pd.Timestamp("2024-01-02")
    assert limpo["competencia"][0] == pd.Period("2024-01", "M")
    assert limpo["ano_acidente"][0] == 2024
    assert limpo["idade_acidente"][0] == 34.0
