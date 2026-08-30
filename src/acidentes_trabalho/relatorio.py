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

# Nao entram no perfil de preenchimento: descrevem a origem, nao o acidente.
COLUNAS_TECNICAS = ("duplicata",)

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


def _secao_volume(df: pd.DataFrame, unico: pd.DataFrame) -> str:
    datas = unico["data_acidente"].dropna()
    duplicadas = len(df) - len(unico)
    sem_data = int(unico["data_acidente"].isna().sum())
    por_leiaute = (
        df.groupby("leiaute", observed=True)
        .agg(arquivos=("arquivo", "nunique"), registros=("arquivo", "size"))
        .reset_index()
        .sort_values("registros", ascending=False)
    )
    por_leiaute["registros"] = _coluna_num(por_leiaute["registros"])
    por_leiaute.columns = ["leiaute", "arquivos", "registros"]

    return f"""## 1. Volume e cobertura

| | registros |
|:---|---:|
| linhas nos {df["arquivo"].nunique()} arquivos | {num(len(df))} |
| republicações (coluna `duplicata`) | {num(duplicadas)} ({pct(duplicadas, len(df))}) |
| **registros únicos** | **{num(len(unico))}** |

Acidentes de **{datas.min():%m/%Y} a {datas.max():%m/%Y}**. Sem data de acidente:
{num(sem_data)} registros ({pct(sem_data, len(unico), 2)}).

> As seções seguintes usam os **registros únicos**, salvo onde indicado — contar
> as linhas cruas superestima em {pct(duplicadas, len(df))}.

{_tabela(por_leiaute, {"arquivos": "d", "registros": "d"})}
"""


def _secao_republicacao(df: pd.DataFrame) -> str:
    por_arquivo = df.groupby("arquivo", observed=True)["duplicata"].agg(["size", "sum"])
    por_arquivo["%"] = 100 * por_arquivo["sum"] / por_arquivo["size"]
    integrais = por_arquivo[por_arquivo["%"] >= 99.9].sort_values("size", ascending=False)
    parciais = por_arquivo[(por_arquivo["%"] > 0) & (por_arquivo["%"] < 99.9)]

    tabela = integrais.reset_index()[["arquivo", "size"]].copy()
    tabela["size"] = _coluna_num(tabela["size"])
    tabela.columns = ["arquivo integralmente republicado", "linhas"]
    repetidas = int(df["duplicata"].sum())

    return f"""## 2. Republicação entre arquivos

Os arquivos do acervo **não são partições disjuntas**: cada um cobre uma janela de
*mês de emissão* da CAT, e as janelas se sobrepõem. A competência `202207`, por
exemplo, cobre emissões de julho a novembro de 2022, e a `202208` cobre agosto a
novembro — inteiramente contida na anterior.

Resultado: empilhar os arquivos conta o mesmo acidente mais de uma vez.
{num(repetidas)} linhas ({pct(repetidas, len(df))}) já haviam aparecido em um
arquivo anterior, e **{len(integrais)} arquivos são republicação integral** — não
trazem um único registro novo:

{_tabela(tabela, {"linhas": "d"})}

Outros {len(parciais)} arquivos têm sobreposição parcial. A coluna `duplicata`
marca a linha repetida sem apagá-la; use `pipeline.carregar(unicos=True)` para
contar acidentes.

A comparação é por conteúdo integral da linha. Como os registros **não têm
identificador**, duas CATs realmente distintas mas idênticas em todos os campos
(mesmo dia, município, CBO, CID, sexo, data de nascimento e CNPJ) seriam
contadas como uma só — risco baixo, mas real.
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

    return f"""## 3. Registros por ano do acidente

Agrupado pela **data do acidente**, nao pela competencia do arquivo — as duas
divergem, e os arquivos misturam anos.

{_tabela(por_ano, {"registros": "d", "% do total": "d"})}
"""


def _secao_preenchimento(df: pd.DataFrame) -> str:
    colunas = [c for c in df.columns if c not in COLUNAS_TECNICAS]
    resumo = pd.DataFrame({
        "coluna": colunas,
        "nulos": [df[c].isna().sum() for c in colunas],
        "distintos": [df[c].nunique(dropna=True) for c in colunas],
    })
    resumo = resumo.sort_values("nulos", ascending=False)
    resumo["% nulos"] = _coluna_pct(resumo["nulos"], len(df))
    resumo["nulos"] = _coluna_num(resumo["nulos"])
    resumo["distintos"] = _coluna_num(resumo["distintos"])
    resumo = resumo[["coluna", "% nulos", "nulos", "distintos"]]

    return f"""## 4. Preenchimento e cardinalidade

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
    return "## 5. Dominios das variaveis categoricas\n\n" + "\n\n".join(blocos) + "\n"


def _secao_geografia(df: pd.DataFrame) -> str:
    contagem = df["uf_empregador_sigla"].value_counts(dropna=False)
    tabela = pd.DataFrame({
        "UF": [("(nulo)" if pd.isna(v) else v) for v in contagem.index],
        "registros": contagem.to_numpy(),
    })
    tabela["%"] = _coluna_pct(tabela["registros"], len(df))
    tabela["registros"] = _coluna_num(tabela["registros"])

    municipios = df["codigo_municipio_empregador"].nunique()
    return f"""## 6. Geografia

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

    return f"""## 7. Consistencia

Sobre os registros unicos.

{_tabela(tabela, {"registros": "d", "%": "d"})}

`municipio sem codigo IBGE valido` sao as linhas cujo municipio veio como
sentinela (`Zerado` ou nao classificado) — sem municipio nao ha UF derivavel.
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
    return f"""## 8. Idade no momento do acidente

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
    unico = df[~df[pipeline.COLUNA_DUPLICATA]].reset_index(drop=True)
    log.info("relatorio: %d registros (%d unicos)", len(df), len(unico))

    corpo = "\n".join([
        "# Relatório da base consolidada de CAT",
        "",
        f"Gerado em {datetime.now(UTC):%d/%m/%Y %H:%M} UTC a partir de "
        f"`{pipeline.BASE_CONSOLIDADA.relative_to(pipeline.BASE_CONSOLIDADA.parents[2])}`.",
        "",
        "Documento **descritivo**: mostra o que a base tem e onde ela falha, para",
        "orientar o recorte da análise. Não responde à pergunta de pesquisa.",
        "",
        _secao_volume(df, unico),
        _secao_republicacao(df),
        _secao_anos(unico),
        _secao_preenchimento(unico),
        _secao_dominios(unico),
        _secao_geografia(unico),
        _secao_consistencia(unico),
        _secao_idade(unico),
        "---",
        "",
        "Gerado por `python -m acidentes_trabalho.pipeline relatorio`.",
        "",
    ])
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(corpo, encoding="utf-8")
    log.info("relatorio: %s", destino)
    return destino
