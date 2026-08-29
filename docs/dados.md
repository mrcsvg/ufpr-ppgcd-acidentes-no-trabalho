# Dados

Os arquivos de dados **não são versionados**. Este documento registra de onde eles
vêm, como reproduzir o download e o que cada coluna significa.

## Como obter

> **A preencher** assim que a fonte for confirmada a partir do material do trabalho
> (pasta *Trabalho CAT*, no Drive).

Passos previstos:

1. Baixe os arquivos originais para `data/raw/`.
2. Não renomeie nem edite nada em `data/raw/` — essa camada é imutável.
3. Registre abaixo, para cada arquivo, a origem, a data do download e o período coberto.

| Arquivo | Fonte | Data do download | Período | Observações |
|---|---|---|---|---|
| _(a preencher)_ | | | | |

### Fontes candidatas

Fontes públicas usuais para registros de CAT no Brasil — **confirmar qual é a usada
no trabalho antes de citar como referência**:

- Dados Abertos da Previdência Social — microdados de CAT;
- AEAT (Anuário Estatístico de Acidentes do Trabalho) e AEPS (Anuário Estatístico da
  Previdência Social);
- Observatório de Segurança e Saúde no Trabalho (SmartLab), que consolida CAT com
  outras bases;
- Tabelas auxiliares: CNAE (atividade econômica), CBO (ocupação), CID-10 (diagnóstico),
  malha municipal e população do IBGE.

## Camadas

| Camada | Pasta | Papel |
|---|---|---|
| `raw` | `data/raw/` | Arquivo original, nunca modificado |
| `interim` | `data/interim/` | Resultado intermediário de limpeza |
| `processed` | `data/processed/` | Base final usada em análises e modelos |
| `external` | `data/external/` | Tabelas auxiliares (CNAE, CID, IBGE, ...) |

O caminho de leitura e escrita de cada camada está em
`acidentes_trabalho.dados.io` — use `io.ler_csv`, `io.ler_parquet` e
`io.salvar_parquet` em vez de montar caminhos à mão.

Os arquivos de dados abertos brasileiros costumam vir em CSV com separador `;` e
codificação `latin-1`; esse é o padrão de `io.ler_csv`.

## Dicionário de dados

> **A preencher** a partir do dicionário oficial da base.

| Coluna | Tipo | Descrição | Domínio / unidade |
|---|---|---|---|
| _(a preencher)_ | | | |

## Decisões de limpeza

Registre aqui toda decisão que altere o conjunto de linhas ou o significado de uma
coluna — exclusão de registros, imputação, recodificação, deduplicação — com a
justificativa e o commit em que foi implementada.

| Decisão | Justificativa | Onde está implementada |
|---|---|---|
| _(a preencher)_ | | |
