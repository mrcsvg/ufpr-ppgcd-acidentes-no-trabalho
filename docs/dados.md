# Dados

Os arquivos de dados **não são versionados**. Este documento registra de onde eles
vêm, como reproduzir o download e o que cada coluna significa.

## Fonte

**Microdados de CAT (Comunicação de Acidente de Trabalho)** — Dados Abertos da
Previdência Social.

O dicionário oficial usado como referência está versionado em
[`dicionario_cat_dadosabertos_2021-02-10.xlsx`](dicionario_cat_dadosabertos_2021-02-10.xlsx)
(versão de 10/02/2021) e transcrito em código em
`acidentes_trabalho.dados.dicionario`.

## Como obter

Os arquivos do trabalho estão em um bucket do **Google Cloud Storage**, no projeto
`ufpr-ppgcd`. Defina o bucket em `.env` (a partir de `.env.example`):

```
BUCKET_CAT=nome-do-bucket
```

E baixe para `data/raw/`:

```bash
# lista o que existe no bucket (exige credencial)
python -m acidentes_trabalho.dados.gcs --listar

# baixa um ou mais objetos
python -m acidentes_trabalho.dados.gcs cat_2023.csv cat_2024.csv
python -m acidentes_trabalho.dados.gcs gs://nome-do-bucket/cat/2023.csv
```

### Credenciais

O download tenta primeiro o acesso autenticado e, se não houver credencial nem a
biblioteca instalada, cai para HTTPS direto — que funciona com objeto público ou
com URL assinada.

| Situação | O que fazer |
|---|---|
| Você tem acesso ao projeto `ufpr-ppgcd` | `gcloud auth application-default login` e `pip install -e ".[gcs]"` |
| Conta de serviço | Aponte `GOOGLE_APPLICATION_CREDENTIALS` para o JSON da chave |
| Sem credencial | Use uma URL assinada (`gcloud storage sign-url`), que o download aceita direto |

**Não versione chaves de conta de serviço.** O `.gitignore` já bloqueia
`credentials.json`, `token.json`, `*.pem` e `.env`.

Depois de baixar:

1. Não renomeie nem edite nada em `data/raw/` — essa camada é imutável.
2. Registre abaixo, para cada arquivo, a origem, a data do download e o período coberto.

| Arquivo | Fonte | Data do download | Período | Observações |
|---|---|---|---|---|
| _(a preencher)_ | | | | |

Os arquivos de dados abertos brasileiros costumam vir em CSV com separador `;` e
codificação `latin-1`; esse é o padrão de `io.ler_csv`.

## Dicionário de dados

24 variáveis. `Nº cat.` é o número de categorias distintas declarado no dicionário
oficial.

### Datas

Todas no formato **AAAAMMDD**. Use `dicionario.converter_datas` para convertê-las —
a função devolve `NaT` para vazios e sentinelas (`0`, `99999999`, datas inexistentes)
em vez de quebrar.

| Variável | Descrição |
|---|---|
| Data Acidente | Data do acidente de trabalho registrada na CAT |
| Data Afastamento | Data em que o segurado se afastou do trabalho por causa do acidente |
| Data DDB | Data do Despacho do Benefício |
| Data Nascimento | Data de nascimento do segurado |
| Data Emissão da CAT | Data de emissão da CAT |

### Categóricas

| Variável | Nº cat. | Descrição |
|---|---:|---|
| Agente Causador do Acidente | 305 | Descrição e código do agente causador do acidente |
| CBO | 2424 | Código Brasileiro de Ocupação |
| CBO Descrição | 2424 | Descrição do CBO |
| CID | 15086 | Identificador da doença conforme a CID-10 |
| CID Descrição | 15086 | Descrição do código CID-10 |
| CNAE | 87 | Classificação Nacional da Atividade Econômica, no agrupamento do AEPS |
| CNAE Descrição | 87 | Descrição da atividade econômica |
| Emitente da CAT | 5 | Quem emitiu a CAT |
| Espécie do Benefício | 97 | Espécie do benefício previdenciário concedido |
| Filiação do Segurado | 4 | Tipo de filiação do segurado à Previdência Social |
| Indicador de Óbito Acidente | 2 | Indicador de óbito do segurado |
| Município Empregador | 5589 | Município do empregador |
| Natureza da Lesão | 80 | Descrição e código da natureza da lesão |
| Origem do Cadastramento CAT | 3 | Origem do cadastramento da CAT |
| Parte do Corpo Atingida | 45 | Parte do corpo atingida no acidente |
| Sexo | 4 | Sexo do segurado informado na CAT |
| Tipo de Acidente | 4 | Tipo do acidente de trabalho sofrido pelo segurado |
| UF Município do Acidente | 28 | Unidade da Federação do local do acidente |
| UF Município Empregador | 29 | Unidade da Federação do município do empregador |

### Observações sobre o dicionário oficial

Pontos do arquivo original que valem atenção na hora de ler os dados:

- **`Data Acidente` aparece duas vezes** na planilha (linhas 2 e 23), com a mesma
  descrição — é duplicação do próprio arquivo, não duas variáveis distintas.
- **`Sexo` tem 4 categorias**, não 2; e **`Indicador de Óbito Acidente` tem 2**.
  Confirmar os domínios reais nos dados antes de recodificar.
- **`UF Município do Acidente` (28) e `UF Município Empregador` (29)** têm mais
  categorias do que as 27 UFs — provavelmente incluem código de ignorado/exterior.
- **`CNAE` tem apenas 87 categorias**: é o agrupamento do AEPS (seção/divisão),
  não a CNAE completa a 5 dígitos.
- Código e descrição vêm em colunas separadas (`CBO`/`CBO Descrição` etc.) e
  declaram a mesma cardinalidade — dá para validar a consistência entre as duas.

## Camadas

| Camada | Pasta | Papel |
|---|---|---|
| `raw` | `data/raw/` | Arquivo original, nunca modificado |
| `interim` | `data/interim/` | Resultado intermediário de limpeza |
| `processed` | `data/processed/` | Base final usada em análises e modelos |
| `external` | `data/external/` | Tabelas auxiliares (CNAE, CBO, CID, IBGE, ...) |

O caminho de leitura e escrita de cada camada está em
`acidentes_trabalho.dados.io` — use `io.ler_csv`, `io.ler_parquet` e
`io.salvar_parquet` em vez de montar caminhos à mão.

## Decisões de limpeza

Registre aqui toda decisão que altere o conjunto de linhas ou o significado de uma
coluna — exclusão de registros, imputação, recodificação, deduplicação — com a
justificativa e o commit em que foi implementada.

| Decisão | Justificativa | Onde está implementada |
|---|---|---|
| _(a preencher)_ | | |
