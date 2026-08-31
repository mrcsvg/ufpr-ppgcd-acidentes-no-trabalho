"""Figuras dedicadas a apresentacao.

As figuras do relatorio sao densas demais para projecao. Estas repetem os mesmos
dados com menos elementos, fonte maior e proporcao 16:9, para serem lidas do
fundo da sala.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from acidentes_trabalho import pipeline
from acidentes_trabalho.figuras import AZUL, CINZA, LARANJA, TINTA, TINTA_SUAVE, _br

PASTA = Path(__file__).resolve().parent / "figuras"
AMBAR = LARANJA
DPI = 200


def estilo_slide() -> None:
    plt.rcParams.update({
        "savefig.dpi": DPI,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": CINZA,
        "axes.labelcolor": TINTA_SUAVE,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": CINZA,
        "grid.alpha": 0.22,
        "grid.linewidth": 0.8,
        "xtick.color": TINTA_SUAVE,
        "ytick.color": TINTA_SUAVE,
        "font.size": 15,
        "axes.labelsize": 15,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "legend.fontsize": 14,
        "legend.frameon": False,
    })


def eixo_br(casas: int = 1):
    """Formatador de eixo no padrao brasileiro (virgula decimal)."""
    return lambda valor, _pos=0: _br(valor, casas)


def _salvar(fig, nome):
    PASTA.mkdir(parents=True, exist_ok=True)
    destino = PASTA / nome
    fig.savefig(destino)
    plt.close(fig)
    print(destino)
    return destino


def esquemas_por_arquivo():
    """Quantos arquivos usam cada leiaute — o problema de partida."""
    dados = [("27 colunas", 31), ("24 colunas\n(sem descrições)", 17),
             ("25 colunas\n(2018–2020)", 8), ("24 colunas\n(truncado)", 5)]
    rotulos = [d[0] for d in dados]
    valores = [d[1] for d in dados]

    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    barras = ax.bar(range(len(valores)), valores, color=AZUL, width=0.58)
    barras[3].set_color(AMBAR)
    barras[1].set_color(AMBAR)
    ax.set_xticks(range(len(valores)), rotulos)
    ax.set_ylabel("arquivos")
    ax.set_ylim(0, max(valores) * 1.22)
    ax.grid(axis="x", visible=False)
    ax.yaxis.set_major_formatter(eixo_br(0))
    for i, valor in enumerate(valores):
        ax.text(i, valor + 1.1, str(valor), ha="center", fontsize=19,
                fontweight="bold", color=TINTA)
    ax.set_title("61 arquivos, 4 formatos incompatíveis", fontsize=18,
                 fontweight="bold", loc="left", color=TINTA, pad=16)
    return _salvar(fig, "esquemas.png")


def uf_trocada(df):
    """A distribuicao gravada contra a real — a armadilha mais cara."""
    sub = df.dropna(subset=["uf_acidente", "uf_empregador_sigla"])
    gravado = df["uf_acidente"].fillna("sem rótulo").value_counts().head(6)
    real = df["uf_empregador_sigla"].value_counts().head(6)

    fig, eixos = plt.subplots(1, 2, figsize=(11.5, 4.6))
    for ax, serie, titulo, cor in (
        (eixos[0], gravado, "O que a coluna diz", AMBAR),
        (eixos[1], real, "O que os dados mostram", AZUL),
    ):
        posicoes = range(len(serie))
        ax.barh(posicoes, serie.to_numpy() / 1e6, color=cor, height=0.62)
        ax.set_yticks(list(posicoes), list(serie.index))
        ax.invert_yaxis()
        ax.set_xlabel("milhões de registros")
        ax.set_title(titulo, fontsize=17, fontweight="bold", loc="left",
                     color=TINTA, pad=12)
        ax.grid(axis="y", visible=False)
        ax.set_xlim(0, max(gravado.max(), real.max()) / 1e6 * 1.20)
        ax.xaxis.set_major_formatter(eixo_br(1))
        for i, valor in enumerate(serie.to_numpy() / 1e6):
            ax.text(valor * 1.03, i, f"{_br(valor, 1)}", va="center",
                    fontsize=13, color=TINTA_SUAVE)
    fig.tight_layout(w_pad=3)
    del sub
    return _salvar(fig, "uf-trocada.png")


def republicacao(df):
    """Quanto de cada arquivo ja tinha aparecido antes."""
    por_arquivo = df.groupby("arquivo", observed=True)["duplicata"].agg(["size", "sum"])
    por_arquivo["pct"] = 100 * por_arquivo["sum"] / por_arquivo["size"]
    top = por_arquivo.nlargest(10, "pct").sort_values("pct")
    nomes = [n.replace("D.SDA.PDA.005.CAT.", "").replace(".csv", "") for n in top.index]

    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    cores = [AMBAR if p >= 99.9 else AZUL for p in top["pct"]]
    ax.barh(range(len(top)), top["pct"], color=cores, height=0.66)
    ax.set_yticks(range(len(top)), nomes)
    ax.set_xlabel("% das linhas já publicadas em outro arquivo")
    ax.set_xlim(0, 118)
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(eixo_br(0))
    for i, pct in enumerate(top["pct"]):
        ax.text(pct + 2, i, f"{_br(pct, 0)}%", va="center", fontsize=13,
                color=TINTA_SUAVE)
    ax.set_title("8 arquivos não trazem um único registro novo", fontsize=18,
                 fontweight="bold", loc="left", color=TINTA, pad=16)
    return _salvar(fig, "republicacao.png")


def letalidade(df):
    """Tipo de acidente e setor, lado a lado — o achado principal."""
    com_obito = df[df["indica_obito"].notna()]
    por_tipo = (
        com_obito.groupby("tipo_acidente", observed=True)["indica_obito"]
        .apply(lambda s: 100 * (s == "Sim").mean())
        .sort_values(ascending=False)
    )
    por_tipo = por_tipo[por_tipo > 0].head(3)

    grupos = com_obito.groupby("cnae_codigo", observed=True)
    setor = pd.DataFrame({
        "n": grupos.size(),
        "taxa": grupos["indica_obito"].apply(lambda s: 100 * (s == "Sim").mean()),
    })
    rotulos = (
        df.dropna(subset=["cnae_codigo", "cnae_descricao"])
        .groupby("cnae_codigo", observed=True)["cnae_descricao"]
        .agg(lambda s: max(s.unique(), key=len))
    )
    setor["setor"] = rotulos
    top = setor[setor["n"] >= 5000].nlargest(4, "taxa").set_index("setor")["taxa"]
    top.index = [s if len(s) < 34 else s[:32] + "…" for s in top.index]
    media = 100 * (com_obito["indica_obito"] == "Sim").mean()

    fig, eixos = plt.subplots(1, 2, figsize=(12.0, 4.6))
    for ax, serie, titulo in (
        (eixos[0], por_tipo, "Por tipo de acidente"),
        (eixos[1], top.sort_values(), "Por setor econômico"),
    ):
        posicoes = range(len(serie))
        cores = [AMBAR if v == serie.max() else AZUL for v in serie]
        ax.barh(posicoes, serie.to_numpy(), color=cores, height=0.6)
        ax.set_yticks(list(posicoes), list(serie.index))
        if titulo.endswith("acidente"):
            ax.invert_yaxis()
        ax.axvline(media, color=CINZA, linewidth=1.4, linestyle="--")
        ax.set_xlabel("% de óbitos entre os acidentes")
        ax.set_title(titulo, fontsize=17, fontweight="bold", loc="left",
                     color=TINTA, pad=12)
        ax.grid(axis="y", visible=False)
        # Escala propria em cada painel: compartilhar o limite achatava o da esquerda.
        limite = serie.max() * 1.34
        ax.set_xlim(0, limite)
        # Passo redondo conforme a escala: 0,2 / 0,5 / 0,8 confunde mais que ajuda.
        passo = 0.25 if limite < 1.5 else 0.5
        ax.set_xticks([x * passo for x in range(int(limite / passo) + 1)])
        ax.xaxis.set_major_formatter(eixo_br(2 if limite < 1.5 else 1))
        for i, valor in enumerate(serie.to_numpy()):
            ax.text(valor + limite * 0.03, i, f"{_br(valor, 2)}%", va="center",
                    fontsize=14, color=TINTA_SUAVE)
        # O rotulo da media vai no topo da linha, dentro dos eixos.
        ax.text(media + limite * 0.02, ax.get_ylim()[1], f"média {_br(media, 2)}%",
                fontsize=12, color=TINTA_SUAVE, va="top", ha="left")
    fig.tight_layout(w_pad=3.2)
    return _salvar(fig, "letalidade.png")


def main() -> int:
    estilo_slide()
    esquemas_por_arquivo()

    bruta = pipeline.carregar(colunas=["arquivo", "duplicata"])
    republicacao(bruta)
    del bruta

    geo = pipeline.carregar(colunas=["uf_acidente", "uf_empregador_sigla"], unicos=True)
    uf_trocada(geo)
    del geo

    letal = pipeline.carregar(
        colunas=["tipo_acidente", "indica_obito", "cnae_codigo", "cnae_descricao"],
        unicos=True,
    )
    letalidade(letal)
    return 0


if __name__ == "__main__":
    sys.exit(main())
