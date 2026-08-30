"""Testes do gerador de relatorio."""

import pandas as pd

from acidentes_trabalho import relatorio


def test_numero_no_padrao_brasileiro():
    assert relatorio.num(3931904) == "3.931.904"
    assert relatorio.num(0) == "0"
    assert relatorio.num(999) == "999"


def test_percentual_no_padrao_brasileiro():
    assert relatorio.pct(121, 1000) == "12,1%"
    assert relatorio.pct(8, 3931904, 2) == "0,00%"


def test_percentual_sem_total_nao_divide_por_zero():
    assert relatorio.pct(5, 0) == "-"


def test_tabela_markdown_alinha_numeros_a_direita():
    df = pd.DataFrame({"uf": ["SP"], "registros": ["1.351.803"]})

    tabela = relatorio._tabela(df, {"registros": "d"})

    assert tabela.splitlines()[0] == "| uf | registros |"
    assert tabela.splitlines()[1] == "|:---|---:|"
    assert tabela.splitlines()[2] == "| SP | 1.351.803 |"
