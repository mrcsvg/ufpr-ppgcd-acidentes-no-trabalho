"""Testes do dicionario de dados de CAT."""

from acidentes_trabalho.dados import dicionario as dic


def test_dicionario_tem_as_24_variaveis_do_arquivo_oficial():
    assert len(dic.VARIAVEIS) == 24
    assert len(dic.POR_ROTULO) == 24, "ha rotulos duplicados no dicionario"


def test_separa_datas_de_categoricas():
    datas = dic.colunas_de_data()
    categoricas = dic.colunas_categoricas()

    assert set(datas) == {
        "Data Acidente",
        "Data Afastamento",
        "Data DDB",
        "Data Nascimento",
        "Data Emissao da CAT",
    }
    assert not set(datas) & set(categoricas)
    assert len(datas) + len(categoricas) == len(dic.VARIAVEIS)


def test_toda_categorica_declara_quantas_categorias_tem():
    for variavel in dic.VARIAVEIS:
        if variavel.e_data:
            assert variavel.categorias is None
        else:
            assert variavel.categorias and variavel.categorias > 0, variavel.rotulo




def test_como_dataframe_espelha_as_variaveis():
    df = dic.como_dataframe()

    assert list(df.columns) == ["rotulo", "tipo", "categorias", "descricao"]
    assert len(df) == len(dic.VARIAVEIS)
