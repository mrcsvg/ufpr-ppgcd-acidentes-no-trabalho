"""Figuras do relatorio de analise exploratoria.

Um estilo unico para todas: marcas finas, sem moldura, grade discreta, rotulo
direto no lugar de legenda sempre que houver uma serie so. As cores vem de uma
paleta categorica validada para daltonismo; series unicas usam sempre o mesmo
azul, para que a cor nunca carregue significado por acidente.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from acidentes_trabalho import pipeline
from acidentes_trabalho.config import FIGURAS

# Paleta categorica validada (modo claro).
AZUL = "#2a78d6"
LARANJA = "#eb6834"
CINZA = "#8a8985"
TINTA = "#0b0b0b"
TINTA_SUAVE = "#52514e"

DPI = 150
TAMANHO = (9.0, 4.6)


def aplicar_estilo() -> None:
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": DPI,
        "savefig.bbox": "tight",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": CINZA,
        "axes.labelcolor": TINTA_SUAVE,
        "axes.titlecolor": TINTA,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 14,
        "axes.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": CINZA,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.6,
        "xtick.color": TINTA_SUAVE,
        "ytick.color": TINTA_SUAVE,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "font.size": 10,
        "legend.frameon": False,
        "legend.fontsize": 9,
    })


def _br(valor: float, casas: int = 0) -> str:
    """Formata no padrao brasileiro: milhar com ponto, decimal com virgula."""
    bruto = f"{valor:,.{casas}f}"
    return bruto.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _milhares(valor: float, _pos: int = 0) -> str:
    """Formata o eixo em milhares."""
    return f"{_br(valor / 1000)} mil" if valor >= 1000 else _br(valor)


def _salvar(fig: plt.Figure, nome: str, pasta: Path) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / nome
    fig.savefig(destino)
    plt.close(fig)
    return destino


def _barras_horizontais(dados: pd.Series, titulo: str, rotulo: str, sufixo: str = "") -> plt.Figure:
    """Barras horizontais ordenadas, com o valor rotulado na ponta de cada barra."""
    fig, ax = plt.subplots(figsize=(TAMANHO[0], 0.34 * len(dados) + 1.6))
    posicoes = range(len(dados))
    ax.barh(posicoes, dados.to_numpy(), color=AZUL, height=0.62)
    ax.set_yticks(list(posicoes), list(dados.index))
    ax.invert_yaxis()
    ax.set_xlabel(rotulo)
    ax.set_title(titulo)
    ax.grid(axis="y", visible=False)
    limite = dados.max()
    for i, valor in enumerate(dados.to_numpy()):
        rotulo_valor = f"{_br(valor, 2)}{sufixo}" if sufixo else _milhares(valor)
        ax.text(valor + limite * 0.012, i, rotulo_valor,
                va="center", fontsize=9, color=TINTA_SUAVE)
    ax.set_xlim(0, limite * 1.16)
    ax.spines["left"].set_color(CINZA)
    return fig


def serie_mensal(df: pd.DataFrame, pasta: Path = FIGURAS) -> Path:
    """Acidentes por mes de ocorrencia — a serie que revela o artefato de publicacao."""
    serie = (
        df.dropna(subset=["data_acidente"])
        .groupby(lambda i: df.loc[i, "data_acidente"].to_period("M"), observed=True)
        .size()
    )
    serie = serie.sort_index()
    x = [p.to_timestamp() for p in serie.index]

    fig, ax = plt.subplots(figsize=(TAMANHO[0], 4.2))
    ax.plot(x, serie.to_numpy(), color=AZUL, linewidth=2, solid_capstyle="round")
    ax.axhline(serie.median(), color=CINZA, linewidth=1, linestyle="--")
    ax.text(x[-1], serie.median(), f"mediana: {_milhares(serie.median())} ",
            va="bottom", ha="right", fontsize=8.5, color=TINTA_SUAVE)
    ax.set_title("Acidentes por mês de ocorrência")
    ax.set_ylabel("registros únicos")
    ax.yaxis.set_major_formatter(_milhares)
    ax.set_ylim(0, None)
    ax.annotate("jul/2025: 3,3× a mediana", xy=(pd.Timestamp("2025-07-01"), serie.max()),
                xytext=(pd.Timestamp("2023-02-01"), serie.max() * 0.97),
                fontsize=9, color=TINTA_SUAVE,
                arrowprops={"arrowstyle": "->", "color": CINZA, "linewidth": 1})
    ax.annotate("abr/2020: pandemia", xy=(pd.Timestamp("2020-04-01"), 20000),
                xytext=(pd.Timestamp("2019-02-01"), 66000),
                fontsize=9, color=TINTA_SUAVE,
                arrowprops={"arrowstyle": "->", "color": CINZA, "linewidth": 1})
    return _salvar(fig, "serie-mensal.png", pasta)


def idade_por_sexo(df: pd.DataFrame, pasta: Path = FIGURAS) -> Path:
    """Distribuicao etaria de homens e mulheres acidentados."""
    faixas = range(14, 76, 2)
    fig, ax = plt.subplots(figsize=TAMANHO)
    for sexo, cor in (("Masculino", AZUL), ("Feminino", LARANJA)):
        idades = df.loc[df["sexo"] == sexo, "idade_acidente"].dropna()
        pesos = [100 / len(idades)] * len(idades)
        ax.hist(idades, bins=faixas, weights=pesos, histtype="step",
                linewidth=2, color=cor, label=sexo)
    ax.set_title("Distribuição etária, por sexo")
    ax.set_xlabel("idade no momento do acidente (anos)")
    ax.set_ylabel("% dos registros do sexo")
    ax.legend(loc="upper right")
    return _salvar(fig, "idade-por-sexo.png", pasta)


def letalidade_por_tipo(df: pd.DataFrame, pasta: Path = FIGURAS) -> Path:
    """Proporcao de obitos em cada tipo de acidente."""
    com_obito = df[df["indica_obito"].notna()]
    taxa = (
        com_obito.groupby("tipo_acidente", observed=True)["indica_obito"]
        .apply(lambda s: 100 * (s == "Sim").mean())
        .sort_values(ascending=False)
    )
    taxa = taxa[taxa > 0]
    fig = _barras_horizontais(taxa, "Letalidade por tipo de acidente", "% de óbitos", "%")
    return _salvar(fig, "letalidade-por-tipo.png", pasta)


def letalidade_por_setor(df: pd.DataFrame, pasta: Path = FIGURAS, minimo: int = 5000) -> Path:
    """Setores economicos com maior letalidade, agrupados pelo CODIGO da CNAE.

    Agrupar pela descricao seria errado: ela vem truncada em parte dos arquivos e
    o mesmo setor aparece sob dois rotulos.
    """
    com_obito = df[df["indica_obito"].notna()]
    grupos = com_obito.groupby("cnae_codigo", observed=True)
    resumo = pd.DataFrame({
        "n": grupos.size(),
        "taxa": grupos["indica_obito"].apply(lambda s: 100 * (s == "Sim").mean()),
    })
    rotulos = (
        df.dropna(subset=["cnae_codigo", "cnae_descricao"])
        .groupby("cnae_codigo", observed=True)["cnae_descricao"]
        .agg(lambda s: max(s.unique(), key=len))
    )
    resumo["setor"] = rotulos
    top = resumo[resumo["n"] >= minimo].nlargest(8, "taxa").set_index("setor")["taxa"]
    fig = _barras_horizontais(
        top, f"Setores com maior letalidade (mín. {_milhares(minimo)} registros)",
        "% de óbitos", "%",
    )
    return _salvar(fig, "letalidade-por-setor.png", pasta)


def registros_por_uf(df: pd.DataFrame, pasta: Path = FIGURAS) -> Path:
    """Volume por UF do empregador, derivada do codigo IBGE do municipio."""
    contagem = df["uf_empregador_sigla"].value_counts().head(15)
    fig = _barras_horizontais(contagem, "Registros por UF do empregador", "registros únicos")
    return _salvar(fig, "registros-por-uf.png", pasta)


def parte_do_corpo(df: pd.DataFrame, pasta: Path = FIGURAS) -> Path:
    """Partes do corpo mais atingidas."""
    contagem = 100 * df["parte_corpo_atingida"].value_counts(normalize=True).head(10)
    fig = _barras_horizontais(contagem, "Parte do corpo atingida", "% dos registros", "%")
    return _salvar(fig, "parte-do-corpo.png", pasta)


# Etapas do workflow ERP: (fase, titulo, linhas do corpo).
ETAPAS_WORKFLOW = (
    ("EXPLORE", "Dados",
     ["61 CSVs no GCS", "1,8 GB · 2019–2026", "5 cabeçalhos"]),
    ("EXPLORE", "Exploração",
     ["Cabeçalho e encoding", "Formato de data", "Domínios e nulos"]),
    ("REFINE", "Decisões",
     ["Mapear por posição", "Marcar republicação", "Descartar uf_acidente", "UF via código IBGE"]),
    ("REFINE", "Análises",
     ["Univariada e bivariada", "Letalidade por setor", "Série temporal"]),
    ("PRODUCE", "Resultados",
     ["Base única: 3,47 M", "Relatório gerado", "6 figuras · 114 testes"]),
)

COR_FASE = {"EXPLORE": AZUL, "REFINE": LARANJA, "PRODUCE": "#1baf7a"}


def workflow(df: pd.DataFrame | None = None, pasta: Path = FIGURAS) -> Path:
    """Diagrama do processo, com cada etapa marcada pela fase do ERP.

    O argumento ``df`` existe so para a funcao ter a mesma assinatura das demais
    figuras e entrar na lista do relatorio; o diagrama nao depende dos dados.
    """
    n = len(ETAPAS_WORKFLOW)
    largura, vao = 9.4, 1.9
    passo = largura + vao
    fig, ax = plt.subplots(figsize=(12.4, 4.8))
    ax.set_xlim(0, n * passo)
    ax.set_ylim(0, 10)
    ax.axis("off")

    altura, base, faixa = 6.2, 3.0, 1.0
    for i, (fase, titulo, itens) in enumerate(ETAPAS_WORKFLOW):
        x = i * passo + vao / 2
        cor = COR_FASE[fase]
        ax.add_patch(plt.Rectangle((x, base), largura, altura, facecolor="white",
                                   edgecolor=cor, linewidth=1.8, zorder=2))
        ax.add_patch(plt.Rectangle((x, base + altura - faixa), largura, faixa,
                                   facecolor=cor, edgecolor=cor, linewidth=1.8, zorder=3))
        ax.text(x + largura / 2, base + altura - faixa / 2, fase, ha="center", va="center",
                fontsize=8.5, fontweight="bold", color="white", zorder=4)
        ax.text(x + largura / 2, base + altura - faixa - 0.75, titulo, ha="center",
                va="center", fontsize=11.5, fontweight="bold", color=TINTA, zorder=4)
        for j, item in enumerate(itens):
            ax.text(x + largura / 2, base + altura - faixa - 1.75 - j * 0.78, item,
                    ha="center", va="center", fontsize=8.5, color=TINTA_SUAVE, zorder=4)
        if i < n - 1:
            meio = base + altura / 2
            ax.annotate("", xy=(x + largura + vao * 0.85, meio), xytext=(x + largura + vao * 0.15,
                        meio), arrowprops={"arrowstyle": "-|>", "color": TINTA_SUAVE,
                                           "linewidth": 1.6})

    # Retorno: achados da analise obrigaram a rever decisoes de normalizacao.
    saida = 3 * passo + vao / 2 + largura / 2
    entrada = 2 * passo + vao / 2 + largura / 2
    altura_retorno = base - 1.15
    ax.plot([saida, saida, entrada, entrada], [base, altura_retorno, altura_retorno, base],
            color=CINZA, linewidth=1.4, linestyle="--", zorder=1)
    ax.annotate("", xy=(entrada, base), xytext=(entrada, altura_retorno + 0.35),
                arrowprops={"arrowstyle": "-|>", "color": CINZA, "linewidth": 1.4})
    ax.text(n * passo / 2, altura_retorno - 0.75,
            "retorno ao REFINE: o sentinela truncado e a sobreposição entre arquivos "
            "obrigaram a refazer a normalização",
            ha="center", fontsize=8.5, color=TINTA_SUAVE, style="italic")
    ax.set_title("Workflow da análise exploratória", fontsize=13, fontweight="bold",
                 loc="left", color=TINTA, pad=10)
    return _salvar(fig, "workflow.png", pasta)


FIGURAS_DO_RELATORIO = (
    workflow,
    serie_mensal,
    idade_por_sexo,
    letalidade_por_tipo,
    letalidade_por_setor,
    registros_por_uf,
    parte_do_corpo,
)


def gerar_todas(pasta: Path = FIGURAS) -> list[Path]:
    """Gera todas as figuras do relatorio a partir da base consolidada."""
    aplicar_estilo()
    df = pipeline.carregar(unicos=True)
    return [funcao(df, pasta) for funcao in FIGURAS_DO_RELATORIO]


if __name__ == "__main__":
    for caminho in gerar_todas():
        print(caminho)
