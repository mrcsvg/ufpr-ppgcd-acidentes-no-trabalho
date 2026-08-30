"""Relatorio do estado da base consolidada.

Gera um documento em Markdown com volume, cobertura temporal, preenchimento,
cardinalidade, dominios e checagens de consistencia. E descritivo de proposito:
serve para decidir o que da para analisar, nao para responder a pergunta de
pesquisa.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from acidentes_trabalho import pipeline
from acidentes_trabalho.config import garantir_diretorios

log = logging.getLogger(__name__)

# Colunas cujo dominio cabe inteiro no relatorio.
DOMINIOS_CURTOS = ("sexo", "tipo_acidente", "indica_obito", "filiacao_segurado",
                   "emitente_cat", "origem_cadastramento", "leiaute")

# Acima disso, o relatorio mostra so as categorias mais frequentes.
LIMITE_CATEGORIAS = 12


def _tabela(df: pd.DataFrame, alinhamento: dict[str, str] | None = None) -> str:
    """Formata um DataFrame como tabela Markdown."""
    alinhamento = alinhamento or {}
    cabecalho = "| " + " | ".join(df.columns) + " |"
    regua = "|" + "|".join(
        {"d": "---:", "e": ":---"}.get(alinhamento.get(c, "e"), ":---") for c in df.columns
    ) + "|"
    linhas = [
        "| " + " | ".join(str(v) for v in linha) + " |" for linha in df.itertuples(index=False)
    ]
    return "\n".join([cabecalho, regua, *linhas])


def num(valor: float) -> str:
    """Formata um inteiro no padrao brasileiro: ``3.931.904``."""
    return f"{int(valor):,}".replace(",", ".")


def pct(parte: float, total: float, casas: int = 1) -> str:
    """Formata uma proporcao no padrao brasileiro: ``12,1%``."""
    if not total:
        return "-"
    return f"{100 * parte / total:.{casas}f}".replace(".", ",") + "%"


def _coluna_num(serie: pd.Series) -> list[str]:
    return [num(v) for v in serie]


def _coluna_pct(serie: pd.Series, total: float, casas: int = 1) -> list[str]:
    return [pct(v, total, casas) for v in serie]


def _secao_volume(df: pd.DataFrame) -> str:
    datas = df["data_acidente"].dropna()
    por_leiaute = (
        df.groupby("leiaute", observed=True)
        .agg(arquivos=("arquivo", "nunique"), registros=("arquivo", "size"))
        .reset_index()
        .sort_values("registros", ascending=False)
    )
    por_leiaute["registros"] = _coluna_num(por_leiaute["registros"])
    por_leiaute.columns = ["leiaute", "arquivos", "registros"]

    return f"""## 1. Volume e cobertura

- **{num(len(df))} registros** consolidados de **{df["arquivo"].nunique()} arquivos**.
- Acidentes de **{datas.min():%m/%Y} a {datas.max():%m/%Y}**.
- {num(df["data_acidente"].isna().sum())} registros sem data de acidente
  ({pct(df["data_acidente"].isna().sum(), len(df), 2)}).

{_tabela(por_leiaute, {"arquivos": "d", "registros": "d"})}
"""


def _secao_anos(df: pd.DataFrame) -> str:
    por_ano = (
        df.groupby("ano_acidente", observed=True)
        .size()
        .reset_index(name="registros")
        .sort_values("ano_acidente")
    )
    por_ano["% do total"] = _coluna_pct(por_ano["registros"], len(df))
    por_ano["registros"] = _coluna_num(por_ano["registros"])
    por_ano["ano_acidente"] = [str(int(a)) for a in por_ano["ano_acidente"]]
    por_ano.columns = ["ano do acidente", "registros", "% do total"]

    return f"""## 2. Registros por ano do acidente

Agrupado pela **data do acidente**, nao pela competencia do arquivo — as duas
divergem, e os arquivos misturam anos.

{_tabela(por_ano, {"registros": "d", "% do total": "d"})}
"""


def _secao_preenchimento(df: pd.DataFrame) -> str:
    resumo = pd.DataFrame({
        "coluna": df.columns,
        "nulos": [df[c].isna().sum() for c in df.columns],
        "distintos": [df[c].nunique(dropna=True) for c in df.columns],
    })
    resumo = resumo.sort_values("nulos", ascending=False)
    resumo["% nulos"] = _coluna_pct(resumo["nulos"], len(df))
    resumo["nulos"] = _coluna_num(resumo["nulos"])
    resumo["distintos"] = _coluna_num(resumo["distintos"])
    resumo = resumo[["coluna", "% nulos", "nulos", "distintos"]]

    return f"""## 3. Preenchimento e cardinalidade

Parte dos nulos e **estrutural**: a coluna nao existe em alguns leiautes, entao
todo registro vindo daqueles arquivos fica nulo. Ver secao 1 para o peso de cada
leiaute.

{_tabela(resumo, {"% nulos": "d", "nulos": "d", "distintos": "d"})}
"""


def _secao_dominios(df: pd.DataFrame) -> str:
    blocos = []
    for coluna in DOMINIOS_CURTOS:
        if coluna not in df.columns:
            continue
        contagem = df[coluna].value_counts(dropna=False).head(LIMITE_CATEGORIAS)
        tabela = pd.DataFrame({
            "valor": [("(nulo)" if pd.isna(v) else v) for v in contagem.index],
            "registros": contagem.to_numpy(),
        })
        tabela["%"] = _coluna_pct(tabela["registros"], len(df))
        tabela["registros"] = _coluna_num(tabela["registros"])
        total = df[coluna].nunique(dropna=True)
        extra = f" (mostrando {LIMITE_CATEGORIAS} de {total})" if total > LIMITE_CATEGORIAS else ""
        blocos.append(f"### `{coluna}`{extra}\n\n{_tabela(tabela, {'registros': 'd', '%': 'd'})}")
    return "## 4. Dominios das variaveis categoricas\n\n" + "\n\n".join(blocos) + "\n"


def _secao_geografia(df: pd.DataFrame) -> str:
    contagem = df["uf_empregador_sigla"].value_counts(dropna=False)
    tabela = pd.DataFrame({
        "UF": [("(nulo)" if pd.isna(v) else v) for v in contagem.index],
        "registros": contagem.to_numpy(),
    })
    tabela["%"] = _coluna_pct(tabela["registros"], len(df))
    tabela["registros"] = _coluna_num(tabela["registros"])

    municipios = df["codigo_municipio_empregador"].nunique()
    return f"""## 5. Geografia

A UF vem do **codigo IBGE do municipio do empregador**, nao do rotulo de texto —
o codigo esta sempre intacto, enquanto o nome chega truncado em parte dos
arquivos.

> **Nao use `uf_acidente`.** A coluna esta corrompida na origem: os rotulos estao
> trocados e 12 UFs nao tem rotulo algum. Ela permanece na base so para que o
> diagnostico possa ser conferido — ver `docs/qualidade-dos-dados.md`.
> Use `limpeza.descartar_colunas_nao_confiaveis` ao carregar para analise.

`uf_empregador_sigla` localiza **o empregador, nao o acidente**.

- {num(municipios)} municipios distintos.

{_tabela(tabela, {"registros": "d", "%": "d"})}
"""


def _secao_consistencia(df: pd.DataFrame) -> str:
    hoje = pd.Timestamp.now().normalize()
    verificacoes = {
        "acidente sem data": df["data_acidente"].isna(),
        "acidente com data no futuro": df["data_acidente"] > hoje,
        "nascimento sem data": df["data_nascimento"].isna(),
        "nascimento posterior ao acidente": df["data_nascimento"] > df["data_acidente"],
        "idade fora de 14-100 anos": df["idade_acidente"].isna() & df["data_nascimento"].notna()
        & df["data_acidente"].notna(),
        "CAT emitida antes do acidente": df["data_emissao_cat"] < df["data_acidente"],
        "municipio sem codigo IBGE valido": df["uf_empregador_sigla"].isna(),
    }
    tabela = pd.DataFrame({
        "verificacao": list(verificacoes),
        "registros": [int(v.sum()) for v in verificacoes.values()],
    })
    tabela["%"] = _coluna_pct(tabela["registros"], len(df), 2)
    tabela["registros"] = _coluna_num(tabela["registros"])

    chave = [c for c in df.columns if c not in ("arquivo", "leiaute")]
    duplicadas = int(df.duplicated(subset=chave).sum())

    return f"""## 6. Consistencia

{_tabela(tabela, {"registros": "d", "%": "d"})}

**Duplicatas:** {num(duplicadas)} linhas identicas ({pct(duplicadas, len(df), 2)}),
comparando todas as colunas de conteudo. Os registros nao tem identificador,
entao nao da para distinguir o mesmo acidente contado duas vezes de dois
acidentes iguais no mesmo dia — decida explicitamente antes de contar.
"""


def _secao_idade(df: pd.DataFrame) -> str:
    idade = df["idade_acidente"].dropna()
    if idade.empty:
        return "## 7. Idade\n\nSem idade calculavel.\n"
    quantis = idade.quantile([0.05, 0.25, 0.5, 0.75, 0.95])
    valores = [idade.min(), *quantis.to_numpy(), idade.max(), idade.mean()]
    tabela = pd.DataFrame({
        "medida": ["minimo", "p5", "p25", "mediana", "p75", "p95", "maximo", "media"],
        "anos": [f"{v:.1f}".replace(".", ",") for v in valores],
    })
    return f"""## 7. Idade no momento do acidente

Calculada de `data_acidente - data_nascimento`, descartando o que cai fora de
14 a 100 anos. Disponivel para {num(len(idade))} registros ({pct(len(idade), len(df))}).

{_tabela(tabela, {"anos": "d"})}
"""


def gerar(destino: Path | None = None) -> Path:
    """Gera o relatorio a partir da base consolidada e devolve o caminho.

    O destino e resolvido na chamada: um valor padrao seria fixado na definicao
    da funcao e ignoraria qualquer mudanca de configuracao posterior.
    """
    destino = destino or pipeline.ARQUIVO_RELATORIO
    garantir_diretorios()
    df = pipeline.carregar()
    log.info("relatorio: %d registros carregados", len(df))

    corpo = "\n".join([
        "# Relatório da base consolidada de CAT",
        "",
        f"Gerado em {datetime.now(UTC):%d/%m/%Y %H:%M} UTC a partir de "
        f"`{pipeline.BASE_CONSOLIDADA.relative_to(pipeline.BASE_CONSOLIDADA.parents[2])}`.",
        "",
        "Documento **descritivo**: mostra o que a base tem e onde ela falha, para",
        "orientar o recorte da análise. Não responde à pergunta de pesquisa.",
        "",
        _secao_volume(df),
        _secao_anos(df),
        _secao_preenchimento(df),
        _secao_dominios(df),
        _secao_geografia(df),
        _secao_consistencia(df),
        _secao_idade(df),
        "---",
        "",
        "Gerado por `python -m acidentes_trabalho.pipeline relatorio`.",
        "",
    ])
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(corpo, encoding="utf-8")
    log.info("relatorio: %s", destino)
    return destino
