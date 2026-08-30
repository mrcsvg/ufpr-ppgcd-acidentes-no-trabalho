"""Testes da leitura unificada dos CSVs de CAT.

Os fixtures reproduzem em miniatura os quatro leiautes reais do acervo, para que
os testes rodem sem depender dos arquivos de dados, que nao sao versionados.
"""

import pandas as pd
import pytest

from acidentes_trabalho.dados import esquemas

CABECALHOS = {
    "v27": (
        "Agente  Causador  Acidente;Data Acidente;CBO;CBO;CID-10;CID-10;CNAE2.0 Empregador;"
        "CNAE2.0 Empregador;Emitente CAT;Espécie do benefício;Filiação Segurado;"
        "Indica Óbito Acidente;Munic Empr;Natureza da Lesão;Origem de Cadastramento CAT;"
        "Parte Corpo Atingida;Sexo;Tipo do Acidente;UF  Munic.  Acidente;UF Munic. Empregador;"
        "Data  Afastamento;Data Despacho Benefício;Data Acidente;Data Nascimento;"
        "Data Emissão CAT;Tipo de Empregador;CNPJ/CEI Empregador"
    ),
    "v24_sem_descricao": (
        "Agente  Causador  Acidente;Data Acidente;CBO;CID-10;CNAE2.0 Empregador;"
        "CNAE2.0 Empregador;Emitente CAT;Espécie do benefício;Filiação Segurado;"
        "Indica Óbito Acidente;Munic Empr;Natureza da Lesão;Origem de Cadastramento CAT;"
        "Parte Corpo Atingida;Sexo;Tipo do Acidente;UF  Munic.  Acidente;UF Munic. Empregador;"
        "Data Acidente;Data Despacho Benefício;Data Acidente;Data Nascimento;Data Emissão CAT;"
        "CNPJ/CEI Empregador"
    ),
    "v24_truncado": (
        "Agente  Causador  Acidente;Data Acidente;CBO;CBO;CID-10;CID-10;CNAE2.0 Empregador;"
        "CNAE2.0 Empregador;Emitente CAT;Espécie do benefício;Filiação Segurado;"
        "Indica Óbito Acidente;Munic Empr;Natureza da Lesão;Origem de Cadastramento CAT;"
        "Parte Corpo Atingida;Sexo;Tipo do Acidente;UF  Munic.  Acidente;UF Munic. Empregador;"
        "Data  Afastamento;Data Acidente;Data Nascimento;Data Acidente"
    ),
    "v25_antigo": (
        "Agente  Causador  Acidente;Data Acidente;CBO;CBO;CID-10;CID-10;CNAE2.0 Empregador;"
        "CNAE2.0 Empregador;Emitente CAT;Espécie do benefício;Filiação Segurado;"
        "Indica acidente;Munic Empr;Natureza da Lesão;Origem de Cadastramento CAT;"
        "Parte Corpo Atingida;Sexo;Tipo do Acidente;UF  Munic.  Acidente;UF Munic. Empregador;"
        "Data  Afastamento;Data Despacho Benefício;Data Acidente;Data Nascimento;Data Emissão CAT"
    ),
}

# Uma linha de dados por leiaute, com o mesmo acidente descrito em cada arranjo.
LINHAS = {
    "v27": (
        "Queda;02/01/2024;322205;Tec. Enfermagem;S610;Ferim de Dedos;8610;Atendimento;"
        "Empregador;Pa;Empregado;Não;316860-Teófilo Otoni;Corte;Internet;Dedo;Feminino;"
        "Típico;Minas Gerais;Minas Gerais;28/12/2023;00/00/0000;02/01/2024;13/02/1995;"
        "02/01/2024;Cnpj/Cgc;25104902000107"
    ),
    "v24_sem_descricao": (
        "Queda;2022/01;322205;S610;8610;Atendimento;Empregador;Pa;Empregado;Não;"
        "316860-Teófilo Otoni;Corte;Internet;Dedo;Feminino;Típico;Minas Gerais;Minas Gerais;"
        "2022/01;0000/00;20/01/2022;13/02/1995;01/03/2022;25104902000107"
    ),
    "v24_truncado": (
        "Queda;23/08/2023;322205;Tec. Enfermagem;S610;Ferim de Dedos;8610;Atendimento;"
        "Empregador;Pa;Empregado;Não;316860-Teófilo Otoni;Corte;Internet;Dedo;Feminino;"
        "Típico;Minas Gerais;Minas Gerais;00/00/0000;23/08/2023;13/02/1995;23/08/2023"
    ),
    "v25_antigo": (
        "Queda;2020/01;322205;Tec. Enfermagem;S610;Ferim de Dedos;8610;Atendimento;"
        "Empregador;Pa;Empregado;Não;316860-Teófilo Otoni;Corte;Internet;Dedo;Feminino;"
        "Típico;Minas Gerais;Minas Gerais;0000/00;0000/00;01/01/2020;13/02/1995;02/01/2020"
    ),
}


def escrever(tmp_path, leiaute, encoding="latin-1", nome="cat.csv", linhas=1):
    """Grava um CSV em miniatura no leiaute pedido e devolve o caminho."""
    conteudo = "\r\n".join([CABECALHOS[leiaute], *[LINHAS[leiaute]] * linhas]) + "\r\n"
    caminho = tmp_path / nome
    caminho.write_bytes(conteudo.encode(encoding))
    return caminho


@pytest.mark.parametrize("leiaute", list(CABECALHOS))
def test_identifica_cada_leiaute_do_acervo(tmp_path, leiaute):
    assert esquemas.identificar_leiaute(escrever(tmp_path, leiaute)).nome == leiaute


def test_identifica_leiaute_com_bom_e_sufixo_numerico(tmp_path):
    """O arquivo UTF-8 do acervo traz BOM e nomes desambiguados (CBO_1, CID-10_2)."""
    cabecalho = CABECALHOS["v25_antigo"].split(";")
    for posicao, sufixo in ((3, "_1"), (5, "_2"), (7, "_3"), (22, "_4")):
        cabecalho[posicao] += sufixo
    conteudo = ";".join(cabecalho) + "\r\n" + LINHAS["v25_antigo"] + "\r\n"
    caminho = tmp_path / "antigo_utf8.csv"
    caminho.write_bytes(b"\xef\xbb\xbf" + conteudo.encode("utf-8"))

    assert esquemas.detectar_encoding(caminho) == "utf-8-sig"
    assert esquemas.identificar_leiaute(caminho).nome == "v25_antigo"


def test_detecta_latin1_quando_nao_ha_bom(tmp_path):
    assert esquemas.detectar_encoding(escrever(tmp_path, "v27")) == "latin-1"


def test_acentuacao_correta_nos_dois_encodings(tmp_path):
    latin = esquemas.ler(escrever(tmp_path, "v27", nome="a.csv"))
    utf8 = esquemas.ler(escrever(tmp_path, "v27", encoding="utf-8", nome="b.csv"))

    assert latin["municipio_empregador"][0] == "316860-Teófilo Otoni"
    assert utf8["municipio_empregador"][0] == "316860-Teófilo Otoni"


def test_cabecalho_desconhecido_e_recusado(tmp_path):
    caminho = tmp_path / "estranho.csv"
    caminho.write_text("a;b;c\n1;2;3\n", encoding="latin-1")

    with pytest.raises(esquemas.LeiauteDesconhecido, match="3 colunas"):
        esquemas.ler(caminho)


@pytest.mark.parametrize("leiaute", list(CABECALHOS))
def test_saida_tem_sempre_as_mesmas_colunas(tmp_path, leiaute):
    df = esquemas.ler(escrever(tmp_path, leiaute))

    assert list(df.columns) == [
        *esquemas.COLUNAS_CANONICAS,
        *esquemas.COLUNAS_PROVENIENCIA,
    ]


@pytest.mark.parametrize("leiaute", list(CABECALHOS))
def test_data_do_acidente_sai_correta_em_todos_os_leiautes(tmp_path, leiaute):
    esperado = {
        "v27": "2024-01-02",
        "v24_sem_descricao": "2022-01-20",
        "v24_truncado": "2023-08-23",
        "v25_antigo": "2020-01-01",
    }[leiaute]

    df = esquemas.ler(escrever(tmp_path, leiaute))

    assert df["data_acidente"][0] == pd.Timestamp(esperado)


def test_competencia_so_e_lida_onde_a_coluna_2_realmente_a_traz(tmp_path):
    com = esquemas.ler(escrever(tmp_path, "v24_sem_descricao"))
    sem = esquemas.ler(escrever(tmp_path, "v27"))

    assert com["competencia"][0] == pd.Period("2022-01", freq="M")
    assert pd.isna(sem["competencia"][0]), "coluna 2 do v27 repete a data, nao e competencia"


def test_colunas_ausentes_no_leiaute_saem_nulas(tmp_path):
    df = esquemas.ler(escrever(tmp_path, "v24_sem_descricao"))

    assert pd.isna(df["cbo_descricao"][0])
    assert pd.isna(df["cid10_descricao"][0])
    assert pd.isna(df["tipo_empregador"][0])
    # A posicao 19 e rotulada "Data Acidente" e repete a competencia: nao vira afastamento.
    assert pd.isna(df["data_afastamento"][0])


def test_coluna_repetida_do_v24_truncado_nao_vira_emissao(tmp_path):
    df = esquemas.ler(escrever(tmp_path, "v24_truncado"))

    assert pd.isna(df["data_emissao_cat"][0])
    assert pd.isna(df["data_despacho_beneficio"][0])


def test_sentinela_de_data_vira_nulo(tmp_path):
    df = esquemas.ler(escrever(tmp_path, "v27"))

    assert pd.isna(df["data_despacho_beneficio"][0])
    assert df["data_afastamento"][0] == pd.Timestamp("2023-12-28")


def test_proveniencia_registra_arquivo_e_leiaute(tmp_path):
    df = esquemas.ler(escrever(tmp_path, "v27", nome="D.SDA.PDA.005.CAT.202401.csv"))

    assert df["arquivo"][0] == "D.SDA.PDA.005.CAT.202401.csv"
    assert df["leiaute"][0] == "v27"


def test_leiautes_empilham_no_mesmo_formato(tmp_path):
    partes = [
        esquemas.ler(escrever(tmp_path, leiaute, nome=f"{leiaute}.csv"))
        for leiaute in CABECALHOS
    ]

    juntos = pd.concat(partes, ignore_index=True)

    assert len(juntos) == len(CABECALHOS)
    assert juntos["data_acidente"].notna().all()
    assert set(juntos["leiaute"]) == set(CABECALHOS)


def test_nrows_limita_a_leitura(tmp_path):
    caminho = escrever(tmp_path, "v27", linhas=10)

    assert len(esquemas.ler(caminho, nrows=3)) == 3
    assert len(esquemas.ler(caminho)) == 10


def test_normalizar_nome_remove_bom_acento_e_sufixo():
    assert esquemas.normalizar_nome("﻿Agente  Causador  Acidente") == "agente causador acidente"
    assert esquemas.normalizar_nome("Espécie do benefício") == "especie do beneficio"
    assert esquemas.normalizar_nome("Data Acidente_4") == "data acidente"


def test_detecta_utf8_sem_bom(tmp_path):
    """latin-1 decodifica qualquer byte, entao UTF-8 precisa ser testado antes."""
    caminho = escrever(tmp_path, "v27", encoding="utf-8")

    assert esquemas.detectar_encoding(caminho) == "utf-8"


def test_nao_confunde_latin1_com_utf8(tmp_path):
    caminho = escrever(tmp_path, "v27", encoding="latin-1")

    assert esquemas.detectar_encoding(caminho) == "latin-1"
    assert esquemas.ler(caminho)["municipio_empregador"][0] == "316860-Teófilo Otoni"
