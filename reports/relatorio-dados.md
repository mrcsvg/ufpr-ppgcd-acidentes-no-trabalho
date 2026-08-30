# Relatório da base consolidada de CAT

Gerado em 30/08/2026 14:08 UTC a partir de `data/processed/cat.parquet`.

Documento **descritivo**: mostra o que a base tem e onde ela falha, para
orientar o recorte da análise. Não responde à pergunta de pesquisa.

## 1. Volume e cobertura

- **3.931.904 registros** consolidados de **61 arquivos**.
- Acidentes de **01/2019 a 06/2026**.
- 8 registros sem data de acidente
  (0,00%).

| leiaute | arquivos | registros |
|:---|---:|---:|
| v27 | 31 | 1.456.506 |
| v24_sem_descricao | 17 | 1.326.202 |
| v25_antigo | 8 | 865.999 |
| v24_truncado | 5 | 283.197 |

## 2. Registros por ano do acidente

Agrupado pela **data do acidente**, nao pela competencia do arquivo — as duas
divergem, e os arquivos misturam anos.

| ano do acidente | registros | % do total |
|:---|---:|---:|
| 2019 | 474.633 | 12,1% |
| 2020 | 391.359 | 10,0% |
| 2021 | 436.201 | 11,1% |
| 2022 | 665.369 | 16,9% |
| 2023 | 603.825 | 15,4% |
| 2024 | 509.971 | 13,0% |
| 2025 | 579.723 | 14,7% |
| 2026 | 270.815 | 6,9% |

## 3. Preenchimento e cardinalidade

Parte dos nulos e **estrutural**: a coluna nao existe em alguns leiautes, entao
todo registro vindo daqueles arquivos fica nulo. Ver secao 1 para o peso de cada
leiaute.

| coluna | % nulos | nulos | distintos |
|:---|---:|---:|---:|
| data_despacho_beneficio | 100,0% | 3.931.856 | 39 |
| data_afastamento | 79,6% | 3.130.116 | 1.580 |
| tipo_empregador | 63,0% | 2.477.487 | 4 |
| competencia | 52,1% | 2.049.838 | 45 |
| cbo_descricao | 41,1% | 1.614.859 | 2.197 |
| cid10_descricao | 37,1% | 1.460.541 | 7.639 |
| uf_acidente | 32,9% | 1.293.886 | 15 |
| cnpj_cei_empregador | 29,2% | 1.149.196 | 536.585 |
| data_emissao_cat | 9,5% | 374.041 | 2.355 |
| agente_causador | 5,0% | 196.783 | 526 |
| uf_empregador_sigla | 4,5% | 177.453 | 27 |
| cnae_descricao | 4,5% | 175.832 | 978 |
| uf_empregador | 4,5% | 175.532 | 27 |
| cbo_codigo | 3,3% | 129.930 | 6.101 |
| origem_cadastramento | 3,1% | 122.143 | 2 |
| emitente_cat | 2,6% | 102.339 | 5 |
| filiacao_segurado | 2,5% | 97.825 | 3 |
| natureza_lesao | 2,4% | 94.688 | 49 |
| parte_corpo_atingida | 2,4% | 92.491 | 74 |
| indica_obito | 2,3% | 90.845 | 2 |
| cid10_codigo | 1,6% | 63.750 | 16.699 |
| idade_acidente | 0,2% | 5.982 | 84 |
| data_nascimento | 0,2% | 5.951 | 23.625 |
| municipio_empregador | 0,0% | 696 | 6.544 |
| nome_municipio_empregador | 0,0% | 696 | 6.142 |
| codigo_municipio_empregador | 0,0% | 696 | 5.145 |
| data_acidente | 0,0% | 8 | 2.671 |
| ano_acidente | 0,0% | 8 | 8 |
| mes_acidente | 0,0% | 8 | 12 |
| cnae_codigo | 0,0% | 0 | 1.177 |
| especie_beneficio | 0,0% | 0 | 11 |
| tipo_acidente | 0,0% | 0 | 4 |
| sexo | 0,0% | 0 | 4 |
| arquivo | 0,0% | 0 | 61 |
| leiaute | 0,0% | 0 | 4 |

## 4. Dominios das variaveis categoricas

### `sexo`

| valor | registros | % |
|:---|---:|---:|
| Masculino | 2.544.717 | 64,7% |
| Feminino | 1.373.364 | 34,9% |
| Não Informado | 13.088 | 0,3% |
| Indeterminado | 735 | 0,0% |

### `tipo_acidente`

| valor | registros | % |
|:---|---:|---:|
| Típico | 2.856.117 | 72,6% |
| Trajeto | 866.607 | 22,0% |
| Doença | 118.614 | 3,0% |
| Ignorado | 90.566 | 2,3% |

### `indica_obito`

| valor | registros | % |
|:---|---:|---:|
| Não | 3.823.345 | 97,2% |
| (nulo) | 90.845 | 2,3% |
| Sim | 17.714 | 0,5% |

### `filiacao_segurado`

| valor | registros | % |
|:---|---:|---:|
| Empregado | 3.823.536 | 97,2% |
| (nulo) | 97.825 | 2,5% |
| Trabalhador Avulso | 8.903 | 0,2% |
| Segurado Especial | 1.640 | 0,0% |

### `emitente_cat`

| valor | registros | % |
|:---|---:|---:|
| Empregador | 3.713.309 | 94,4% |
| (nulo) | 102.339 | 2,6% |
| Segurado/Dependente | 64.116 | 1,6% |
| Sindicato | 32.120 | 0,8% |
| Médico | 10.865 | 0,3% |
| Autoridade Pública | 9.155 | 0,2% |

### `origem_cadastramento`

| valor | registros | % |
|:---|---:|---:|
| Internet | 3.809.758 | 96,9% |
| (nulo) | 122.143 | 3,1% |
| Prisma | 3 | 0,0% |

### `leiaute`

| valor | registros | % |
|:---|---:|---:|
| v27 | 1.456.506 | 37,0% |
| v24_sem_descricao | 1.326.202 | 33,7% |
| v25_antigo | 865.999 | 22,0% |
| v24_truncado | 283.197 | 7,2% |

## 5. Geografia

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
| SP | 1.351.803 | 34,4% |
| MG | 380.605 | 9,7% |
| PR | 306.088 | 7,8% |
| RS | 302.336 | 7,7% |
| SC | 261.664 | 6,7% |
| RJ | 245.310 | 6,2% |
| (nulo) | 177.453 | 4,5% |
| GO | 108.035 | 2,7% |
| BA | 100.057 | 2,5% |
| ES | 87.502 | 2,2% |
| PE | 78.316 | 2,0% |
| MT | 76.836 | 2,0% |
| CE | 76.674 | 2,0% |
| MS | 60.370 | 1,5% |
| PA | 55.397 | 1,4% |
| DF | 55.224 | 1,4% |
| AM | 40.179 | 1,0% |
| RN | 25.613 | 0,7% |
| MA | 25.405 | 0,6% |
| RO | 21.646 | 0,6% |
| AL | 21.609 | 0,5% |
| PB | 20.771 | 0,5% |
| SE | 13.972 | 0,4% |
| TO | 12.712 | 0,3% |
| PI | 12.475 | 0,3% |
| RR | 5.070 | 0,1% |
| AC | 4.748 | 0,1% |
| AP | 4.034 | 0,1% |

## 6. Consistencia

| verificacao | registros | % |
|:---|---:|---:|
| acidente sem data | 8 | 0,00% |
| acidente com data no futuro | 0 | 0,00% |
| nascimento sem data | 5.951 | 0,15% |
| nascimento posterior ao acidente | 0 | 0,00% |
| idade fora de 14-100 anos | 23 | 0,00% |
| CAT emitida antes do acidente | 79 | 0,00% |
| municipio sem codigo IBGE valido | 177.453 | 4,51% |

**Duplicatas:** 458.155 linhas identicas (11,65%),
comparando todas as colunas de conteudo. Os registros nao tem identificador,
entao nao da para distinguir o mesmo acidente contado duas vezes de dois
acidentes iguais no mesmo dia — decida explicitamente antes de contar.

## 7. Idade no momento do acidente

Calculada de `data_acidente - data_nascimento`, descartando o que cai fora de
14 a 100 anos. Disponivel para 3.925.922 registros (99,8%).

| medida | anos |
|:---|---:|
| minimo | 14,0 |
| p5 | 20,0 |
| p25 | 26,0 |
| mediana | 35,0 |
| p75 | 44,0 |
| p95 | 57,0 |
| maximo | 100,0 |
| media | 36,0 |

---

Gerado por `python -m acidentes_trabalho.pipeline relatorio`.
