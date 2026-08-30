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

### Onde o dicionário oficial diverge dos arquivos

Verificado contra os dados reais. O relatório completo está em
[`qualidade-dos-dados.md`](qualidade-dos-dados.md); o essencial:

- **O formato de data está errado no dicionário.** Ele declara `AAAAMMDD`, e
  nenhum arquivo usa isso: é `DD/MM/AAAA` para data exata e `AAAA/MM` para
  competência. Converta com `dados.datas`, nunca com o formato publicado.
- **`Data Acidente` aparece duas vezes porque são duas colunas do CSV** (posições
  2 e 23), não porque o documento se repetiu. Em alguns arquivos a coluna 2 traz
  competência, e em outros repete a data exata.
- **`UF Município do Acidente` está corrompida na origem** e não é recuperável:
  os rótulos estão trocados e 12 UFs não têm rótulo algum. Não use essa coluna.
- **`Sexo` tem mesmo 4 categorias** — Feminino, Masculino, Não Informado e
  Indeterminado, que não é sinônimo de Não Informado.
- **`Tipo de Acidente` declara 4 categorias, mas só 3 aparecem**: Típico,
  Trajeto e Doença.
- **`CNAE` tem apenas 87 categorias**: é o agrupamento do AEPS (seção/divisão),
  não a CNAE completa a 5 dígitos.
- **As descrições vêm truncadas em 20 caracteres** em `CID-10` e `CBO` (82,7% e
  63,3% dos registros). Use os códigos e cruze com tabela externa.

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

## Como ler

O caminho normal é rodar o pipeline uma vez e depois ler a base consolidada:

```bash
python -m acidentes_trabalho.pipeline
```

```python
from acidentes_trabalho import pipeline
from acidentes_trabalho.dados import limpeza

df = pipeline.carregar(colunas=["data_acidente", "sexo", "uf_empregador_sigla"])
df = limpeza.descartar_colunas_nao_confiaveis(df)
```

Por baixo, `dados.esquemas.ler` unifica os cinco cabeçalhos do acervo mapeando
**por posição** (os rótulos de coluna são inconfiáveis em parte dos arquivos),
`dados.limpeza` aplica as decisões de limpeza e `dados.derivadas` acrescenta as
variáveis calculadas.

### Colunas derivadas

| Coluna | Origem | Por quê |
|---|---|---|
| `codigo_municipio_empregador` | 6 primeiros dígitos de `municipio_empregador` | O nome vem truncado; o código não |
| `nome_municipio_empregador` | resto de `municipio_empregador` | Pode vir truncado em 20 caracteres |
| `uf_empregador_sigla` | 2 primeiros dígitos do código IBGE | UF confiável, sem depender do rótulo |
| `ano_acidente`, `mes_acidente` | `data_acidente` | Agrupamento temporal correto |
| `idade_acidente` | `data_acidente - data_nascimento` | Descarta o que cai fora de 14–100 anos |

## Decisões de limpeza

| Decisão | Justificativa | Onde está implementada |
|---|---|---|
| `{ñ class}` e `Zerado` viram nulo | São marcadores de ausência gravados como texto; sem isso entram nas contagens como categoria | `dados.limpeza.marcar_sentinelas` |
| `uf_acidente` é descartada | Rótulos trocados e 12 UFs colapsadas em `{ñ class}` — irrecuperável | `dados.limpeza.descartar_colunas_nao_confiaveis` |
| Colunas ausentes num leiaute saem nulas | Permite empilhar arquivos de leiautes diferentes sem inventar valor | `dados.esquemas.ler` |
| Colunas com rótulo que não bate com o conteúdo são descartadas | Ex.: coluna 19 do `v24_sem_descricao`, rotulada `Data Acidente`, repete a competência | `dados.esquemas` (posições `None`) |
| Idade fora de 14–100 anos vira nulo | Incompatível com vínculo formal; indica data de nascimento errada | `dados.derivadas.idade` |
| `uf_acidente` é **mantida** na base consolidada | A base é o registro fiel do acervo; o descarte é decisão de análise | `pipeline.normalizar_um` |

Registre aqui toda decisão nova que altere o conjunto de linhas ou o significado
de uma coluna, com a justificativa e onde foi implementada.
