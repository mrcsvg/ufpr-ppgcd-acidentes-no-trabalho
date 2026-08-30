# Acidentes no Trabalho — análise de dados de CAT

Projeto de análise de dados sobre **acidentes de trabalho no Brasil**, a partir de
registros de **CAT (Comunicação de Acidente de Trabalho)**.

Trabalho do **PPGCD/UFPR** — Programa de Pós-Graduação em Ciência de Dados,
Universidade Federal do Paraná.

> **Status:** esqueleto do projeto. A fonte já está definida — microdados de CAT dos
> Dados Abertos da Previdência Social, com dicionário em [`docs/dados.md`](docs/dados.md).
> A pergunta de pesquisa e o recorte da análise ainda serão definidos
> (ver `docs/enunciado.md`).

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
make dados     # roda o pipeline completo: baixa, normaliza, consolida, relata
make test      # roda os testes
make lint      # roda o ruff
make notebook  # abre o JupyterLab
```

## O pipeline

Quatro etapas, cada uma retomável de forma independente:

```
baixar      bucket GCS             ->  data/raw/*.csv          61 arquivos, 1,8 GB
normalizar  data/raw/*.csv         ->  data/interim/*.parquet  unifica 5 esquemas
consolidar  data/interim/*.parquet ->  data/processed/cat.parquet
relatorio   data/processed         ->  reports/relatorio-dados.md
```

```bash
python -m acidentes_trabalho.pipeline              # tudo (~2 min)
python -m acidentes_trabalho.pipeline normalizar   # só uma etapa
python -m acidentes_trabalho.pipeline --refazer    # ignora o que já está pronto
```

A base consolidada tem **3.473.749 registros únicos** de acidentes entre 2019 e
2026, em 94 MB de Parquet (contra 1,8 GB de CSV). A consolidação grava em fluxo,
um arquivo por vez, então roda em máquina modesta.

> **Os arquivos do acervo se sobrepõem.** 11,7% das linhas são republicação do
> mesmo registro em outra competência — 8 arquivos não trazem nada novo. A coluna
> `duplicata` marca as repetições sem apagá-las: **use `unicos=True` para contar
> acidentes**, senão o resultado vem inflado.

> `--refazer` é necessário depois de alterar `esquemas`, `limpeza` ou
> `derivadas`: o pipeline compara datas de arquivo, e mudança de código não
> invalida os intermediários sozinha.

Sem o `make`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,notebooks]"
pytest
```

## Dados

Os dados **não são versionados** neste repositório. Eles ficam em um bucket do
Google Cloud Storage (projeto `ufpr-ppgcd`); copie `.env.example` para `.env`,
preencha `BUCKET_CAT` e baixe:

```bash
python -m acidentes_trabalho.dados.gcs --listar        # o que há no bucket
python -m acidentes_trabalho.dados.gcs cat_2023.csv    # baixa para data/raw/
```

As instruções completas, incluindo credenciais e URLs assinadas, estão em
[`docs/dados.md`](docs/dados.md).

Dentro do código, use sempre os caminhos de `acidentes_trabalho.config` em vez de
caminhos relativos — assim os scripts funcionam de qualquer diretório:

```python
from acidentes_trabalho.config import DADOS_RAW, SEED
from acidentes_trabalho.dados import io

df = io.ler_csv("cat_2023.csv")          # lê de data/raw/ com sep=";" e latin-1
io.salvar_parquet(df, "cat.parquet")     # grava em data/processed/
```

> **Atenção:** os 61 arquivos do acervo **não compartilham um esquema único** —
> são 5 cabeçalhos diferentes, e em parte deles os rótulos de coluna não
> correspondem ao conteúdo. Nunca empilhe os CSVs por nome de coluna. Use
> `dados.esquemas.ler`, que mapeia por posição:

```python
from acidentes_trabalho import pipeline
from acidentes_trabalho.dados import limpeza

df = pipeline.carregar(unicos=True)             # sem as republicações
df = pipeline.carregar(colunas=["sexo", "ano_acidente"], unicos=True)
df = limpeza.descartar_colunas_nao_confiaveis(df)   # remove uf_acidente
```

As armadilhas dos dados — incluindo uma coluna corrompida na origem e um formato
de data que contradiz o dicionário oficial — estão levantadas em
[`docs/qualidade-dos-dados.md`](docs/qualidade-dos-dados.md). **Leia antes de
analisar.**

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
