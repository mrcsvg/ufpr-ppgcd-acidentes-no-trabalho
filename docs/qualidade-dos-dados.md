# Qualidade dos dados

Inspeção do acervo em `gs://acidentes-no-trabalho/cats/` — 61 CSVs, 1,92 GB,
acidentes de 2018 a maio/2026.

Os números abaixo vêm da leitura integral de **6 arquivos** (222.431 registros),
um por esquema encontrado. As conclusões sobre estrutura valem para os 61, porque
o cabeçalho de todos foi verificado; as proporções valem para a amostra.

## Resumo

| Achado | Gravidade | Efeito |
|---|---|---|
| `uf_acidente` corrompida e irrecuperável | **Alta** | Não dá para localizar o acidente |
| 5 cabeçalhos diferentes, com rótulos que mentem | **Alta** | Empilhar por nome de coluna corrompe os dados |
| Data no formato `DD/MM/AAAA`, não `AAAAMMDD` | **Alta** | Contradiz o dicionário oficial |
| 3 arquivos em UTF-8, o resto em latin-1 | Média | Lidos errado, sem erro, viram mojibake |
| Descrições truncadas em 20 caracteres | Média | `cid10_descricao` truncada em 82,7% |
| Competência ≠ mês do acidente | Média | Série temporal por arquivo fica errada |
| `data_despacho_beneficio` 100% nula | Baixa | Coluna inútil |

## 1. `uf_acidente` está corrompida na origem

O achado mais sério. A coluna é inutilizável, por dois motivos somados.

**Os rótulos estão trocados**, de forma sistemática (94% a 99% de concentração):

| Rótulo gravado | UF real | Registros |
|---|---|---:|
| Maranhão | São Paulo | 76.437 |
| Rondônia | Minas Gerais | 23.621 |
| Roraima | Paraná | 18.343 |
| Tocantins | Rio de Janeiro | 13.773 |
| Pará | Pernambuco | 4.213 |
| Acre | Pará | 3.612 |
| Ceará | Distrito Federal | 2.938 |
| Pernambuco | Rondônia | 1.404 |
| Amazonas | Paraíba | 998 |
| Piauí | Sergipe | 837 |
| Amapá | Piauí | 645 |
| Alagoas | Roraima | 264 |
| Rio Grande Norte | Acre | 222 |
| Paraíba | Amapá | 181 |

**E 12 UFs não têm rótulo nenhum**: caem todas em `{ñ class}`, 32,1% dos registros.
Verificado diretamente — entre os registros com `uf_acidente = {ñ class}`, o
empregador está em:

```
Rio Grande do Sul 18.917 | Santa Catarina 14.832 | Goiás 6.574 | Bahia 5.885
Espírito Santo 5.213 | Mato Grosso 5.157 | Mato Grosso do Sul 3.819
Ceará 3.755 | Amazonas 2.194 | Rio Grande do Norte 1.517 | Maranhão 1.322
Alagoas 1.104
```

Ou seja: a coluna **não distingue esses 12 estados de forma alguma**. Nem
recodificar resolve — a informação não está lá.

**Consequência:** use `uf_empregador` e `municipio_empregador`, lembrando que
localizam **o empregador, não o acidente**. Para 98% dos registros as duas UFs
divergem, então a diferença importa. `dados.limpeza` descarta `uf_acidente` por
padrão.

## 2. Cinco cabeçalhos, quatro leiautes — e rótulos que mentem

| Leiaute | Colunas | Arquivos | Período | O que falta |
|---|---:|---:|---|---|
| `v27` | 27 | 31 | 202311–202605 | — (mais completo) |
| `v24_sem_descricao` | 24 | 17 | 202101–202305 | descrição de CBO e CID-10, afastamento |
| `v24_truncado` | 24 | 5 | 202306–202310 | despacho do benefício, emissão da CAT |
| `v25_antigo` | 25 | 8 | 2018–2020 | CNPJ, tipo de empregador |

O quinto cabeçalho é o `v25_antigo` gravado em UTF-8, com sufixos `_1`, `_2` nos
nomes repetidos — mesmo leiaute, exportação diferente.

**O perigo real são os rótulos errados.** Em `v24_sem_descricao`, a coluna 19 é
rotulada `Data Acidente` mas repete a competência; em `v24_truncado`, a coluna 24
tem o mesmo rótulo e repete a data do acidente, no lugar onde os outros arquivos
trazem `Data Emissão CAT`. Empilhar os arquivos por nome de coluna mistura
conteúdos diferentes sem gerar erro nenhum.

Por isso `dados.esquemas` mapeia **por posição**, ancorado no cabeçalho
reconhecido, e recusa cabeçalho desconhecido em vez de adivinhar.

## 3. Formato de data: o dicionário oficial está errado

O dicionário de 10/02/2021 declara `AAAAMMDD`. **Nenhum arquivo usa esse formato.**
O que existe:

- `DD/MM/AAAA` para data exata, ausência marcada como `00/00/0000`;
- `AAAA/MM` para competência, ausência marcada como `0000/00`.

Os dois convivem no mesmo arquivo. Conversão correta em `dados.datas`.

## 4. Encoding misto

Três arquivos (`cat-comp10-11-12-2020`, `cat-competencia-04-05-06-2020`,
`cat-competencia-07-08-09-2020`) são UTF-8; os outros 58, latin-1. Como latin-1
decodifica qualquer byte sem erro, ler um UTF-8 como latin-1 **não falha** — só
entrega `EspÃ©cie` no lugar de `Espécie`. `dados.esquemas.detectar_encoding` testa
UTF-8 estrito antes de aceitar latin-1.

## 5. Descrições truncadas

Os campos vêm com largura fixa, preenchidos com espaço, e cortados:

| Coluna | Largura máx. | % no limite |
|---|---:|---:|
| `cid10_descricao` | 20 | 82,7% |
| `cbo_descricao` | 20 | 63,3% |
| `cnae_descricao` | 45 | 0,9% |
| `agente_causador` | 45 | 0,6% |

`cid10_descricao` e `cbo_descricao` estão cortadas na maioria dos registros
(`'T13.9 Traum Ne do Me'`, `'841815-Oper. Máquina'`). **Use os códigos**
(`cid10_codigo`, `cbo_codigo`) e cruze com uma tabela externa em `data/external/`;
as descrições servem só para conferência visual.

## 6. Competência não é o mês do acidente

Os arquivos são agrupados pela competência de processamento da CAT, não pela data
do acidente. `cat-comp01-02-03-2020.csv` (1º trimestre de 2020) contém acidentes
de **maio/2019 a outubro/2020**. Contar acidentes por mês usando o nome do arquivo
produz série temporal errada — agrupe por `data_acidente`.

Isso também significa que os meses mais recentes estão **incompletos**: acidentes
de 2026 ainda serão registrados em competências futuras. Os arquivos `202511` e
`202512` têm 0,1 MB (≈200 registros) contra 20–30 MB dos meses normais.

## 7. Preenchimento das colunas

Percentual de nulos na amostra de 6 arquivos:

| Coluna | Nulos | Observação |
|---|---:|---|
| `data_despacho_beneficio` | 100,0% | inútil na amostra |
| `data_afastamento` | 99,1% | quase sempre `00/00/0000` |
| `tipo_empregador` | 96,6% | só existe no `v27` |
| `cnpj_cei_empregador` | 94,3% | ausente no `v24_truncado` e no `v25_antigo` |
| `competencia` | 61,2% | só onde a coluna 2 traz `AAAA/MM` |
| `data_emissao_cat` | 23,8% | ausente no `v24_truncado` |
| `cid10_descricao` / `cbo_descricao` | 2,3% | ausentes no `v24_sem_descricao` |

Boa parte é estrutural (a coluna não existe naquele leiaute), não falta de
preenchimento — por isso a proporção depende de quais arquivos entram na análise.

## 8. Domínios observados

- `sexo`: Feminino, Masculino, Não Informado, **Indeterminado** — as 4 categorias
  do dicionário; as duas últimas não são a mesma coisa.
- `tipo_acidente`: Típico, Trajeto, Doença — 3 valores, e o dicionário declara 4.
- `indica_obito`: Sim, Não.
- `{ñ class}` aparece em 12 colunas: `cbo_descricao` (10,1%), `cid10_descricao`
  (3,9%), `agente_causador` (3,7%), `cnae_descricao` (2,1%) e outras.
- `Zerado` aparece em `uf_acidente` e `uf_empregador` (≈2.800 registros cada).

`dados.limpeza.marcar_sentinelas` converte os dois em nulo — sem isso eles entram
nas contagens como se fossem categoria.

## 9. Duplicatas

153 linhas idênticas em 222.431 (0,1%), considerando todas as colunas de conteúdo.
Como os registros não têm identificador, não dá para saber se são o mesmo acidente
contado duas vezes ou dois acidentes iguais no mesmo dia. Volume baixo, mas
decida explicitamente antes de contar.

## Como reproduzir

```python
import pandas as pd
from acidentes_trabalho.config import DADOS_RAW
from acidentes_trabalho.dados import esquemas, limpeza

df = pd.concat([esquemas.ler(c) for c in DADOS_RAW.glob("*.csv")], ignore_index=True)
df = limpeza.limpar(df)
```
