# Relatório da base consolidada de CAT

Gerado em 30/08/2026 14:15 UTC a partir de `data/processed/cat.parquet`.

Documento **descritivo**: mostra o que a base tem e onde ela falha, para
orientar o recorte da análise. Não responde à pergunta de pesquisa.

## 1. Volume e cobertura

| | registros |
|:---|---:|
| linhas nos 61 arquivos | 3.931.904 |
| republicações (coluna `duplicata`) | 458.155 (11,7%) |
| **registros únicos** | **3.473.749** |

Acidentes de **01/2019 a 06/2026**. Sem data de acidente: 8 registros (0,00%).

> As seções seguintes usam os **registros únicos**, salvo onde indicado — contar
> as linhas cruas superestima em 11,7%.

| leiaute | arquivos | registros |
|:---|---:|---:|
| v27 | 31 | 1.456.506 |
| v24_sem_descricao | 17 | 1.326.202 |
| v25_antigo | 8 | 865.999 |
| v24_truncado | 5 | 283.197 |

## 2. Republicação entre arquivos

Os arquivos do acervo **não são partições disjuntas**: cada um cobre uma janela de
*mês de emissão* da CAT, e as janelas se sobrepõem. A competência `202207`, por
exemplo, cobre emissões de julho a novembro de 2022, e a `202208` cobre agosto a
novembro — inteiramente contida na anterior.

Resultado: empilhar os arquivos conta o mesmo acidente mais de uma vez. 458.155 linhas (11,7%) já haviam aparecido em um arquivo anterior, e **8 arquivos são republicação integral** — não trazem um único registro novo:

| arquivo integralmente republicado | linhas |
|:---|---:|
| D.SDA.PDA.005.CAT.202208.csv | 123.442 |
| D.SDA.PDA.005.CAT.202204.csv | 89.602 |
| D.SDA.PDA.005.CAT.202508.csv | 72.885 |
| D.SDA.PDA.005.CAT.202209.csv | 70.245 |
| D.SDA.PDA.005.CAT.202405.csv | 57.990 |
| D.SDA.PDA.005.CAT.202210.csv | 26.023 |
| D.SDA.PDA.005.CAT.202211.csv | 5.112 |
| D.SDA.PDA.005.CAT.202511.csv | 205 |

Outros 34 arquivos têm sobreposição parcial. A coluna `duplicata` marca a linha repetida sem apagá-la; use `pipeline.carregar(unicos=True)` para contar acidentes.

A comparação é por conteúdo integral da linha. Como os registros **não têm
identificador**, duas CATs realmente distintas mas idênticas em todos os campos
(mesmo dia, município, CBO, CID, sexo, data de nascimento e CNPJ) seriam
contadas como uma só — risco baixo, mas real.

## 3. Registros por ano do acidente

Agrupado pela **data do acidente**, nao pela competencia do arquivo — as duas
divergem, e os arquivos misturam anos.

| ano do acidente | registros | % do total |
|:---|---:|---:|
| 2019 | 474.414 | 13,7% |
| 2020 | 391.013 | 11,3% |
| 2021 | 435.980 | 12,6% |
| 2022 | 339.775 | 9,8% |
| 2023 | 603.743 | 17,4% |
| 2024 | 451.981 | 13,0% |
| 2025 | 506.280 | 14,6% |
| 2026 | 270.555 | 7,8% |

## 4. Preenchimento e cardinalidade

Parte dos nulos e **estrutural**: a coluna nao existe em alguns leiautes, entao
todo registro vindo daqueles arquivos fica nulo. Ver secao 1 para o peso de cada
leiaute.

| coluna | % nulos | nulos | distintos |
|:---|---:|---:|---:|
| data_despacho_beneficio | 100,0% | 3.473.705 | 39 |
| data_afastamento | 79,1% | 2.747.140 | 1.580 |
| tipo_empregador | 61,9% | 2.150.806 | 4 |
| competencia | 55,2% | 1.917.782 | 45 |
| cbo_descricao | 36,6% | 1.272.635 | 2.197 |
| cnpj_cei_empregador | 33,1% | 1.148.565 | 536.585 |
| uf_acidente | 32,8% | 1.139.065 | 15 |
| cid10_descricao | 32,6% | 1.131.746 | 7.639 |
| data_emissao_cat | 9,3% | 323.080 | 2.355 |
| agente_causador | 3,8% | 131.874 | 526 |
| cnae_descricao | 3,2% | 112.215 | 978 |
| uf_empregador_sigla | 3,2% | 110.788 | 27 |
| uf_empregador | 3,1% | 109.017 | 27 |
| cbo_codigo | 2,9% | 100.864 | 6.101 |
| origem_cadastramento | 1,9% | 67.687 | 2 |
| cid10_codigo | 1,5% | 50.966 | 16.699 |
| emitente_cat | 1,4% | 48.694 | 5 |
| filiacao_segurado | 1,3% | 45.282 | 3 |
| natureza_lesao | 1,3% | 43.791 | 49 |
| parte_corpo_atingida | 1,2% | 41.596 | 74 |
| indica_obito | 1,2% | 39.950 | 2 |
| idade_acidente | 0,2% | 5.740 | 84 |
| data_nascimento | 0,2% | 5.709 | 23.625 |
| municipio_empregador | 0,0% | 647 | 6.544 |
| nome_municipio_empregador | 0,0% | 647 | 6.142 |
| codigo_municipio_empregador | 0,0% | 647 | 5.145 |
| data_acidente | 0,0% | 8 | 2.671 |
| ano_acidente | 0,0% | 8 | 8 |
| mes_acidente | 0,0% | 8 | 12 |
| cnae_codigo | 0,0% | 0 | 1.177 |
| especie_beneficio | 0,0% | 0 | 11 |
| tipo_acidente | 0,0% | 0 | 4 |
| sexo | 0,0% | 0 | 4 |
| arquivo | 0,0% | 0 | 53 |
| leiaute | 0,0% | 0 | 4 |

## 5. Dominios das variaveis categoricas

### `sexo`

| valor | registros | % |
|:---|---:|---:|
| Masculino | 2.248.468 | 64,7% |
| Feminino | 1.212.743 | 34,9% |
| Não Informado | 11.806 | 0,3% |
| Indeterminado | 732 | 0,0% |

### `tipo_acidente`

| valor | registros | % |
|:---|---:|---:|
| Típico | 2.558.827 | 73,7% |
| Trajeto | 768.792 | 22,1% |
| Doença | 106.296 | 3,1% |
| Ignorado | 39.834 | 1,1% |

### `indica_obito`

| valor | registros | % |
|:---|---:|---:|
| Não | 3.418.153 | 98,4% |
| (nulo) | 39.950 | 1,2% |
| Sim | 15.646 | 0,5% |

### `filiacao_segurado`

| valor | registros | % |
|:---|---:|---:|
| Empregado | 3.419.264 | 98,4% |
| (nulo) | 45.282 | 1,3% |
| Trabalhador Avulso | 7.750 | 0,2% |
| Segurado Especial | 1.453 | 0,0% |

### `emitente_cat`

| valor | registros | % |
|:---|---:|---:|
| Empregador | 3.328.762 | 95,8% |
| Segurado/Dependente | 52.623 | 1,5% |
| (nulo) | 48.694 | 1,4% |
| Sindicato | 27.702 | 0,8% |
| Médico | 8.959 | 0,3% |
| Autoridade Pública | 7.009 | 0,2% |

### `origem_cadastramento`

| valor | registros | % |
|:---|---:|---:|
| Internet | 3.406.059 | 98,1% |
| (nulo) | 67.687 | 1,9% |
| Prisma | 3 | 0,0% |

### `leiaute`

| valor | registros | % |
|:---|---:|---:|
| v27 | 1.324.813 | 38,1% |
| v24_sem_descricao | 1.000.371 | 28,8% |
| v25_antigo | 865.434 | 24,9% |
| v24_truncado | 283.131 | 8,2% |

## 6. Geografia

A UF vem do **codigo IBGE do municipio do empregador**, nao do rotulo de texto —
o codigo esta sempre intacto, enquanto o nome chega truncado em parte dos
arquivos.

> **Nao use `uf_acidente`.** A coluna esta corrompida na origem: os rotulos estao
> trocados e 12 UFs nao tem rotulo algum. Ela permanece na base so para que o
> diagnostico possa ser conferido — ver `docs/qualidade-dos-dados.md`.
> Use `limpeza.descartar_colunas_nao_confiaveis` ao carregar para analise.

`uf_empregador_sigla` localiza **o empregador, nao o acidente**.

- 5.145 municipios distintos.

| UF | registros | % |
|:---|---:|---:|
| SP | 1.210.167 | 34,8% |
| MG | 340.962 | 9,8% |
| PR | 274.651 | 7,9% |
| RS | 272.447 | 7,8% |
| SC | 233.576 | 6,7% |
| RJ | 219.762 | 6,3% |
| (nulo) | 110.788 | 3,2% |
| GO | 97.161 | 2,8% |
| BA | 89.109 | 2,6% |
| ES | 78.516 | 2,3% |
| PE | 69.661 | 2,0% |
| MT | 69.491 | 2,0% |
| CE | 68.285 | 2,0% |
| MS | 54.295 | 1,6% |
| PA | 49.735 | 1,4% |
| DF | 49.195 | 1,4% |
| AM | 35.576 | 1,0% |
| RN | 22.936 | 0,7% |
| MA | 22.633 | 0,7% |
| RO | 19.470 | 0,6% |
| AL | 19.354 | 0,6% |
| PB | 18.511 | 0,5% |
| SE | 12.625 | 0,4% |
| TO | 11.412 | 0,3% |
| PI | 11.077 | 0,3% |
| RR | 4.576 | 0,1% |
| AC | 4.225 | 0,1% |
| AP | 3.553 | 0,1% |

## 7. Consistencia

Sobre os registros unicos.

| verificacao | registros | % |
|:---|---:|---:|
| acidente sem data | 8 | 0,00% |
| acidente com data no futuro | 0 | 0,00% |
| nascimento sem data | 5.709 | 0,16% |
| nascimento posterior ao acidente | 0 | 0,00% |
| idade fora de 14-100 anos | 23 | 0,00% |
| CAT emitida antes do acidente | 79 | 0,00% |
| municipio sem codigo IBGE valido | 110.788 | 3,19% |

`municipio sem codigo IBGE valido` sao as linhas cujo municipio veio como
sentinela (`Zerado` ou nao classificado) — sem municipio nao ha UF derivavel.

## 8. Idade no momento do acidente

Calculada de `data_acidente - data_nascimento`, descartando o que cai fora de
14 a 100 anos. Disponivel para 3.468.009 registros (99,8%).

| medida | anos |
|:---|---:|
| minimo | 14,0 |
| p5 | 20,0 |
| p25 | 26,0 |
| mediana | 35,0 |
| p75 | 44,0 |
| p95 | 57,0 |
| maximo | 100,0 |
| media | 35,9 |

---

Gerado por `python -m acidentes_trabalho.pipeline relatorio`.
