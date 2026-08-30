# Qualidade dos dados

Inspeção do acervo em `gs://acidentes-no-trabalho/cats/` — 61 CSVs, 1,92 GB,
acidentes de 2018 a maio/2026.

Os números vêm da base consolidada completa: **3.931.904 registros** dos 61
arquivos. O perfil descritivo (preenchimento, domínios, distribuições) fica em
[`../reports/relatorio-dados.md`](../reports/relatorio-dados.md), regerado pelo
pipeline; aqui ficam as **armadilhas estruturais**, que não mudam a cada rodada.

## Resumo

| Achado | Gravidade | Efeito |
|---|---|---|
| Arquivos se sobrepõem: 11,7% são republicação | **Alta** | Empilhar superconta os acidentes |
| `uf_acidente` corrompida e irrecuperável | **Alta** | Não dá para localizar o acidente |
| 5 cabeçalhos diferentes, com rótulos que mentem | **Alta** | Empilhar por nome de coluna corrompe os dados |
| Data no formato `DD/MM/AAAA`, não `AAAAMMDD` | **Alta** | Contradiz o dicionário oficial |
| 3 arquivos em UTF-8, o resto em latin-1 | Média | Lidos errado, sem erro, viram mojibake |
| Descrições truncadas em 20 caracteres | Média | `cid10_descricao` truncada em 82,7% |
| Competência ≠ mês do acidente | Média | Série temporal por arquivo fica errada |
| `data_despacho_beneficio` 100% nula | Baixa | Coluna inútil |

## 1. Os arquivos se sobrepõem

Cada arquivo cobre uma janela de **mês de emissão** da CAT, e as janelas **não são
disjuntas**. A competência `202207` cobre emissões de julho a novembro de 2022; a
`202208` cobre agosto a novembro — inteiramente contida na anterior.

Consequência direta: **empilhar os 61 arquivos conta o mesmo acidente mais de uma
vez**. São 458.155 linhas repetidas em 3.931.904 (11,7%), restando 3.473.749
registros únicos. Oito arquivos não trazem um único registro novo:

```
202208 (123.442) · 202204 (89.602) · 202508 (72.885) · 202209 (70.245)
202405 (57.990) · 202210 (26.023) · 202211 (5.112) · 202511 (205)
```

Outros 34 têm sobreposição parcial. Note que 99,7% dos grupos de linhas repetidas
cruzam arquivos — repetição dentro de um mesmo arquivo é rara.

A consolidação marca a repetição na coluna `duplicata` em vez de apagar a linha,
para que a base siga sendo o registro fiel do acervo. Para **contar** acidentes,
use `pipeline.carregar(unicos=True)`.

Como os registros não têm identificador, a comparação é pelo conteúdo integral da
linha: duas CATs realmente distintas, mas idênticas em todos os campos — mesmo
dia, município, CBO, CID, sexo, data de nascimento e CNPJ — seriam contadas como
uma só. O risco é baixo, e é o preço de não ter chave.

## 2. `uf_acidente` está corrompida na origem

O achado mais sério. A coluna é inutilizável, por dois motivos somados.

**Os rótulos estão trocados**, de forma sistemática. Cruzando com a UF derivada
do código IBGE do município (que é confiável), cada rótulo aponta para uma única
UF real, com 94% a 99% de concentração:

| Rótulo gravado | UF real | Registros |
|---|---|---:|
| Maranhão | SP | 1.339.950 |
| Rondônia | MG | 382.882 |
| Roraima | PR | 305.683 |
| Tocantins | RJ | 247.940 |
| Pará | PE | 77.582 |
| Acre | PA | 56.061 |
| Ceará | DF | 53.875 |
| Pernambuco | RO | 21.987 |
| Amazonas | PB | 21.242 |
| Piauí | SE | 14.188 |
| Sergipe | TO | 13.122 |
| Amapá | PI | 12.766 |
| Alagoas | RR | 5.343 |
| Rio Grande Norte | AC | 4.824 |
| Paraíba | AP | 4.086 |

**E 12 UFs não têm rótulo nenhum.** Caem todas no sentinela `{ñ class}` — 32,9%
dos registros (1.293.886). São elas:

```
AL · AM · BA · CE · ES · GO · MA · MS · MT · RN · RS · SC
```

Rio Grande do Sul e Santa Catarina, juntos, respondem por mais de 560 mil
registros na base. A coluna **não distingue esses 12 estados de forma alguma** —
nem recodificar resolve, porque a informação não está lá.

**Consequência:** use `uf_empregador_sigla`, derivada do código IBGE do
município, lembrando que localiza **o empregador, não o acidente**.
`uf_acidente` fica na base consolidada apenas para que este diagnóstico possa ser
conferido; `limpeza.descartar_colunas_nao_confiaveis` a remove na análise.

## 3. Cinco cabeçalhos, quatro leiautes — e rótulos que mentem

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

## 4. Formato de data: o dicionário oficial está errado

O dicionário de 10/02/2021 declara `AAAAMMDD`. **Nenhum arquivo usa esse formato.**
O que existe:

- `DD/MM/AAAA` para data exata, ausência marcada como `00/00/0000`;
- `AAAA/MM` para competência, ausência marcada como `0000/00`.

Os dois convivem no mesmo arquivo. Conversão correta em `dados.datas`.

## 5. Encoding misto

Três arquivos (`cat-comp10-11-12-2020`, `cat-competencia-04-05-06-2020`,
`cat-competencia-07-08-09-2020`) são UTF-8; os outros 58, latin-1. Como latin-1
decodifica qualquer byte sem erro, ler um UTF-8 como latin-1 **não falha** — só
entrega `EspÃ©cie` no lugar de `Espécie`. `dados.esquemas.detectar_encoding` testa
UTF-8 estrito antes de aceitar latin-1.

## 6. Descrições truncadas

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

## 7. Competência não é o mês do acidente

Os arquivos são agrupados pela competência de processamento da CAT, não pela data
do acidente. `cat-comp01-02-03-2020.csv` (1º trimestre de 2020) contém acidentes
de **maio/2019 a outubro/2020**. Contar acidentes por mês usando o nome do arquivo
produz série temporal errada — agrupe por `data_acidente`.

Isso também significa que os meses mais recentes estão **incompletos**: acidentes
de 2026 ainda serão registrados em competências futuras. Os arquivos `202511` e
`202512` têm 0,1 MB (≈200 registros) contra 20–30 MB dos meses normais.

## 8. Preenchimento das colunas

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

## 9. Domínios observados

- `sexo`: Feminino (34,9%), Masculino (64,7%), Não Informado, **Indeterminado** —
  as 4 categorias do dicionário; as duas últimas não são a mesma coisa.
- `tipo_acidente`: Típico (72,6%), Trajeto (22,0%), Doença (3,0%) e **Ignorado**
  (2,3%) — as 4 do dicionário.
- `indica_obito`: Não (97,2%), Sim (0,5%).
- `especie_beneficio` traz 11 valores distintos, contra as 97 espécies declaradas
  no dicionário.

### O sentinela também vem truncado

`{ñ class}` (não classificado) é cortado pela largura fixa do campo, e aparece
como `{ñ class}`, `{ñ class` e até `{ñ`, conforme a coluna. Uma limpeza que casse
o texto inteiro deixa passar as versões cortadas — foi o que aconteceu na
primeira versão deste projeto: 90.844 registros seguiram com `{ñ` em
`indica_obito` e `{ñ class` em `origem_cadastramento`, contados como se fossem
categoria válida.

Como **nenhum valor legítimo da base começa com chave** (verificado nos 3.931.904
registros), `limpeza` trata qualquer valor iniciado por `{` como ausência. Vale
também para `Zerado`, que aparece nas colunas de UF.

## Como reproduzir

```bash
python -m acidentes_trabalho.pipeline
```

```python
from acidentes_trabalho import pipeline
from acidentes_trabalho.dados import limpeza

df = pipeline.carregar(unicos=True)                 # sem as republicações
df = limpeza.descartar_colunas_nao_confiaveis(df)   # sem uf_acidente
```
