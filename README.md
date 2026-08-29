# Acidentes no Trabalho — análise de dados de CAT

Projeto de análise de dados sobre **acidentes de trabalho no Brasil**, a partir de
registros de **CAT (Comunicação de Acidente de Trabalho)**.

Trabalho do **PPGCD/UFPR** — Programa de Pós-Graduação em Ciência de Dados,
Universidade Federal do Paraná.

> **Status:** esqueleto do projeto. A pergunta de pesquisa, o recorte dos dados e o
> escopo da análise ainda serão definidos a partir do material em `docs/enunciado.md`.

## Estrutura do repositório

```
.
├── data/                     # dados (não versionados — ver docs/dados.md)
│   ├── raw/                  # original, imutável
│   ├── interim/              # intermediário, resultado de limpeza
│   ├── processed/            # base final usada nas análises
│   └── external/             # fontes auxiliares (CNAE, CID, IBGE, ...)
├── docs/                     # enunciado, dicionário de dados, decisões
├── notebooks/                # exploração — numerados na ordem de execução
├── referencias/              # artigos e material de apoio (não versionado)
├── reports/figuras/          # figuras geradas (não versionadas)
├── src/acidentes_trabalho/   # código reaproveitável
│   ├── config.py             # caminhos e semente do projeto
│   ├── dados/                # leitura, escrita e limpeza
│   ├── features/             # variáveis derivadas
│   ├── modelos/              # treino e avaliação
│   └── viz/                  # estilo e gráficos
└── tests/                    # testes automatizados
```

A regra é simples: **notebook explora, `src/` consolida**. Assim que um trecho de
código passa a ser reutilizado, ele migra do notebook para um módulo em `src/` e
ganha um teste.

## Como começar

Requer Python 3.11 ou superior.

```bash
make setup     # cria .venv e instala o pacote em modo editável
make test      # roda os testes
make lint      # roda o ruff
make notebook  # abre o JupyterLab
```

Sem o `make`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,notebooks]"
pytest
```

## Dados

Os dados **não são versionados** neste repositório. Antes de rodar qualquer análise,
baixe os arquivos para `data/raw/` seguindo as instruções em
[`docs/dados.md`](docs/dados.md).

Dentro do código, use sempre os caminhos de `acidentes_trabalho.config` em vez de
caminhos relativos — assim os scripts funcionam de qualquer diretório:

```python
from acidentes_trabalho.config import DADOS_RAW, SEED
from acidentes_trabalho.dados import io

df = io.ler_csv("cat_2023.csv")          # lê de data/raw/ com sep=";" e latin-1
io.salvar_parquet(df, "cat.parquet")     # grava em data/processed/
```

## Reprodutibilidade

- Semente única do projeto em `config.SEED` (padrão `42`, sobrescrita pela variável
  de ambiente `SEED`).
- Dependências fixadas em `pyproject.toml`.
- Notebooks numerados (`01_`, `02_`, ...) e executáveis do início ao fim, na ordem.
- Nada em `data/` é editado à mão: toda transformação nasce de código versionado.

## Convenções

- Código, nomes de função e docstrings em **português**, sem acentos em identificadores.
- Mensagens de commit no imperativo e em português.
- Cada função que sai do notebook para `src/` chega acompanhada de teste.
