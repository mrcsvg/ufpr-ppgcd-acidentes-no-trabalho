"""Conteudo do relatorio ATIVIDADE 3, preenchido com os resultados reais."""

TABELA_0 = [  # Caracterizacao
    ("Base de dados",
     "Microdados de CAT — Comunicação de Acidente de Trabalho, do Regime Geral de "
     "Previdência Social."),
    ("Fonte",
     "Dados Abertos da Previdência Social. Os 61 arquivos CSV foram disponibilizados "
     "pelo grupo em bucket do Google Cloud Storage (gs://acidentes-no-trabalho/cats/), "
     "totalizando 1,8 GB. Dicionário oficial de 10/02/2021."),
    ("Unidade de análise",
     "Uma CAT emitida — isto é, a comunicação de um acidente de trabalho sofrido por um "
     "segurado. Os registros não possuem identificador único."),
    ("Nº de observações",
     "3.931.904 linhas nos arquivos; 3.473.749 registros únicos após identificar "
     "458.155 republicações (11,7%) do mesmo registro em competências diferentes."),
    ("Nº de variáveis",
     "24 variáveis no dicionário oficial. Após unificar os cinco leiautes do acervo: "
     "25 colunas canônicas, mais 6 derivadas (código e nome do município, sigla da UF, "
     "ano, mês e idade) e 3 de proveniência (arquivo, leiaute, duplicata)."),
    ("Período",
     "Acidentes ocorridos entre janeiro de 2019 e junho de 2026. A cobertura é irregular: "
     "os arquivos são organizados por mês de emissão da CAT, não por data do acidente."),
    ("Principais variáveis",
     "data_acidente; tipo_acidente (típico, trajeto, doença); indica_obito; sexo; "
     "idade_acidente (derivada); cnae_codigo (setor econômico); cbo_codigo (ocupação); "
     "cid10_codigo (diagnóstico); natureza_lesao; parte_corpo_atingida; "
     "municipio_empregador e uf_empregador_sigla (derivada do código IBGE)."),
]

TABELA_1 = [  # Diagnostico
    ("Dados ausentes",
     "Ausência majoritariamente ESTRUTURAL, não aleatória: a coluna simplesmente não "
     "existe em parte dos leiautes, e todo registro vindo daqueles arquivos fica nulo. "
     "Ignorar isso enviesa qualquer análise que use essas colunas.",
     "data_despacho_beneficio 100% nula; data_afastamento 79,6%; tipo_empregador 63,0% "
     "(só existe no leiaute v27); cbo_descricao 41,1% e cid10_descricao 37,1% (ausentes "
     "no leiaute v24_sem_descricao, que responde por 1,3 milhão de linhas). Já as "
     "variáveis centrais são quase completas: data_acidente 0,0%, sexo 0,0%, "
     "tipo_acidente 0,0%, data_nascimento 0,2%."),
    ("Duplicidades",
     "458.155 linhas (11,7%) repetem um registro já presente em outro arquivo. A causa "
     "é estrutural: os arquivos são JANELAS SOBREPOSTAS de mês de emissão, não partições "
     "disjuntas. Empilhar os 61 arquivos superconta os acidentes em 11,7%.",
     "99,7% dos grupos repetidos cruzam arquivos (repetição interna é rara). Oito "
     "arquivos são republicação integral, sem um único registro novo: 202208 (123.442 "
     "linhas), 202204 (89.602), 202508 (72.885), 202209 (70.245), 202405 (57.990), "
     "202210 (26.023), 202211 (5.112) e 202511 (205). A competência 202207 cobre "
     "emissões de jul a nov/2022 e a 202208 cobre ago a nov — contida na anterior."),
    ("Inconsistências",
     "Três inconsistências graves, todas silenciosas: (1) a coluna UF do município do "
     "acidente está corrompida na origem e é irrecuperável; (2) rótulos de coluna que "
     "não correspondem ao conteúdo em parte dos arquivos; (3) o dicionário oficial "
     "declara formato de data que nenhum arquivo usa.",
     "(1) Os rótulos de UF estão trocados de forma sistemática — São Paulo aparece como "
     "'Maranhão' (1.339.950 registros), Minas Gerais como 'Rondônia', Paraná como "
     "'Roraima' — com 94% a 99% de concentração no cruzamento com a UF derivada do "
     "código IBGE; e 12 UFs (AL, AM, BA, CE, ES, GO, MA, MS, MT, RN, RS, SC) não têm "
     "rótulo algum, caindo todas no sentinela, 32,9% da base. (2) No leiaute "
     "v24_sem_descricao a coluna 19 é rotulada 'Data Acidente' mas repete a competência; "
     "no v24_truncado a coluna 24 tem o mesmo rótulo e repete a data do acidente, onde "
     "os demais arquivos trazem a data de emissão. (3) O dicionário declara AAAAMMDD; "
     "os arquivos usam DD/MM/AAAA e AAAA/MM."),
    ("Outliers",
     "Os valores extremos relevantes estão na CONTAGEM ao longo do tempo, não nas "
     "variáveis individuais. A série mensal é dominada por artefato de publicação, e "
     "não por variação do fenômeno.",
     "Mediana de 39.182 acidentes/mês. Julho de 2025 registra 127.642 (3,3× a mediana), "
     "enquanto novembro de 2025 registra 79 e dezembro de 2025 registra 12. Em 2022 a "
     "série oscila entre 8 mil e 51 mil de um mês para o outro. Nas variáveis "
     "individuais os extremos são raros: apenas 23 idades fora de 14–100 anos e 79 CATs "
     "com emissão anterior ao acidente. A defasagem entre acidente e emissão tem mediana "
     "de 3 dias e p99 de 95 dias."),
    ("Outros",
     "Duas limitações adicionais que afetam diretamente a análise: o truncamento das "
     "descrições em 20 caracteres FRAGMENTA CATEGORIAS, e o acervo mistura cinco "
     "cabeçalhos diferentes com encodings distintos.",
     "84,7% dos códigos CNAE aparecem sob mais de uma descrição — 'Transporte "
     "Rodoviario de Carga' e 'Transporte Rodoviari' são o mesmo setor contado duas "
     "vezes; o mesmo ocorre em 27,2% dos municípios. Agrupar pela descrição, e não pelo "
     "código, produz resultado errado. O acervo tem 5 cabeçalhos (4 leiautes com 24, 25 "
     "e 27 colunas) e 3 arquivos em UTF-8 contra 58 em latin-1 — como latin-1 decodifica "
     "qualquer byte sem erro, lê-los com o encoding errado não falha, apenas corrompe o "
     "texto."),
]

TABELA_2 = [  # EXPLORE - Investigar
    ("Como o volume de acidentes evolui ao longo do tempo?",
     "data_acidente",
     "Série temporal mensal (Figura 1)",
     "A série NÃO é utilizável como está: oscila entre 8 mil e 128 mil por mês sem "
     "padrão epidemiológico. Mediana de 39.182/mês. Dois sinais se distinguem do ruído: "
     "a queda de abril de 2020 (20 mil contra ~30 mil nos meses vizinhos), compatível "
     "com o início da pandemia, e o pico de julho de 2025 (3,3× a mediana), sem "
     "explicação no fenômeno."),
    ("Onde estão localizados os empregadores?",
     "uf_empregador_sigla, codigo_municipio_empregador",
     "Barras horizontais (Figura 2)",
     "Concentração em São Paulo: 1.210.167 registros (34,9%), seguido de MG (9,8%), PR "
     "(7,9%), RS (7,8%) e SC (6,7%). 5.145 municípios distintos. 110.788 registros "
     "(3,2%) sem município válido. A distribuição acompanha o peso econômico das UFs, "
     "não uma taxa de risco."),
    ("Qual o perfil por sexo?",
     "sexo",
     "Distribuição de frequência",
     "64,7% masculino e 34,9% feminino; 0,34% não informado e 0,02% indeterminado — "
     "categorias distintas, que não devem ser fundidas."),
    ("Qual a distribuição etária, e ela difere entre homens e mulheres?",
     "idade_acidente (derivada), sexo",
     "Histograma sobreposto e medidas-resumo (Figura 3)",
     "Mediana de 35 anos (p25=26, p75=44, média 35,9). As distribuições diferem em "
     "FORMA, não apenas em posição: os homens concentram-se entre 22 e 28 anos (pico de "
     "6,9%), enquanto as mulheres formam um platô mais alto e mais tardio, entre 30 e "
     "45 anos. Mediana de 34 anos para homens e 36 para mulheres."),
    ("Que tipo de acidente predomina?",
     "tipo_acidente",
     "Distribuição de frequência",
     "Típico 73,7%, Trajeto 22,1%, Doença 3,1% e Ignorado 1,2%. O dicionário declara 4 "
     "categorias e as 4 aparecem."),
    ("Qual tipo de acidente é mais letal?",
     "tipo_acidente × indica_obito",
     "Tabela cruzada e barras (Figura 4)",
     "Inversão relevante: o acidente de TRAJETO é o menos frequente entre os dois "
     "principais, mas o mais letal — 0,877% de óbitos, contra 0,329% do típico (2,7 "
     "vezes maior). Em números absolutos, 6.743 óbitos em trajeto contra 8.421 em "
     "típicos, apesar de o típico ser 3,3 vezes mais frequente."),
    ("A letalidade difere entre homens e mulheres?",
     "sexo × indica_obito",
     "Tabela cruzada",
     "0,635% para homens contra 0,123% para mulheres — 5,2 vezes maior. A diferença é "
     "muito superior à diferença de exposição (homens são 1,9 vez mais frequentes na "
     "base), sugerindo composição ocupacional distinta e não apenas volume."),
    ("Que setores econômicos concentram maior letalidade?",
     "cnae_codigo × indica_obito",
     "Taxa de óbito por setor, com mínimo de 5 mil registros (Figura 5)",
     "Letalidade geral de 0,456%. Transporte Rodoviário de Carga lidera com 1,96% — 4,3 "
     "vezes a média — seguido de Obras de Terraplenagem (1,61%), Comércio Atacadista de "
     "Hortifrutigranjeiros (1,41%) e Extração de Pedra, Areia e Argila (1,40%). O "
     "agrupamento foi feito pelo CÓDIGO, não pela descrição: 84,7% dos códigos têm mais "
     "de uma descrição por causa do truncamento."),
    ("Que partes do corpo são mais atingidas?",
     "parte_corpo_atingida",
     "Barras horizontais (Figura 6)",
     "Concentração nas extremidades: dedo 22,7%, pé 8,4%, mão 5,3% e joelho 5,2%. As "
     "quatro primeiras categorias respondem por 41,6% dos registros."),
]

TABELA_3 = [  # REFINE - Aprofundar
    ("A UF do município do acidente tinha distribuição implausível: apenas 17 valores "
     "distintos, com Maranhão em primeiro lugar e São Paulo ausente.",
     "Cruzamento sistemático da coluna com a UF derivada do código IBGE do município do "
     "empregador, em todos os 3,9 milhões de registros.",
     "A distribuição contrariava o conhecido: São Paulo concentra a atividade econômica "
     "e não podia estar ausente. Era necessário decidir entre recodificar a coluna ou "
     "descartá-la.",
     "A coluna é IRRECUPERÁVEL. Cada rótulo mapeia para uma única UF real com 94% a 99% "
     "de concentração (São Paulo gravado como 'Maranhão', Minas como 'Rondônia'), mas 12 "
     "UFs não têm rótulo algum e colapsam no sentinela — 32,9% da base. Decisão: usar a "
     "UF derivada do código IBGE, registrando que ela localiza o EMPREGADOR, não o "
     "acidente."),
    ("O relatório automatizado acusou 11,7% de linhas duplicadas, contra 0,1% na amostra "
     "de 6 arquivos inspecionada inicialmente.",
     "Levantamento, arquivo a arquivo, do intervalo de meses de emissão coberto e da "
     "proporção de linhas já vistas em arquivos anteriores.",
     "Uma diferença de duas ordens de grandeza entre amostra e base completa indicava "
     "causa estrutural, não ruído. Descartar as duplicatas sem entendê-las poderia "
     "eliminar registros legítimos.",
     "Os arquivos são janelas SOBREPOSTAS de mês de emissão. Oito arquivos são "
     "republicação integral. Decisão: MARCAR as repetições em uma coluna booleana em vez "
     "de apagá-las, mantendo a base auditável, e oferecer o descarte no carregamento."),
    ("A série mensal de acidentes apresentava oscilações incompatíveis com o fenômeno — "
     "de 8 mil a 51 mil entre meses consecutivos de 2022.",
     "Decomposição da cobertura por mês de emissão e por arquivo, comparando com a série "
     "por data do acidente.",
     "Antes de interpretar qualquer tendência temporal era preciso separar variação do "
     "fenômeno de artefato de publicação.",
     "A irregularidade vem da cobertura: não há arquivo cobrindo as emissões de janeiro "
     "e fevereiro de 2022, e a defasagem mediana entre acidente e emissão é de apenas 3 "
     "dias — logo, os acidentes desses meses estão majoritariamente AUSENTES. Os meses "
     "finais de cada janela também estão incompletos. Consequência: análise temporal "
     "exige recorte explícito de período completo."),
    ("Após a limpeza dos marcadores de ausência, o valor '{ñ' continuava aparecendo como "
     "categoria válida em indica_obito e origem_cadastramento.",
     "Inspeção dos valores distintos de todas as colunas de texto, buscando prefixos "
     "comuns.",
     "Uma categoria espúria com 90.844 registros distorceria qualquer distribuição de "
     "frequência e qualquer taxa calculada sobre essas colunas.",
     "O próprio sentinela vem TRUNCADO pela largura fixa do campo: aparece como "
     "'{ñ class}', '{ñ class' e '{ñ', conforme a coluna. Verificou-se que nenhum valor "
     "legítimo da base começa com chave, nos 3,9 milhões de registros; a regra de "
     "limpeza passou a tratar qualquer valor iniciado por '{' como ausência."),
    ("O ranking de letalidade por setor trazia 'Transporte Rodoviario de Carga' e "
     "'Transporte Rodoviari' como setores distintos.",
     "Contagem de quantas descrições diferentes cada código de CNAE, CBO e município "
     "assume na base.",
     "Se o mesmo setor aparece sob dois rótulos, a contagem por setor está partida e o "
     "ranking de letalidade fica errado.",
     "84,7% dos códigos CNAE têm mais de uma descrição, e 27,2% dos municípios. Decisão: "
     "todo agrupamento passa a usar o CÓDIGO; a descrição serve apenas como rótulo de "
     "exibição, tomando a versão mais longa observada para cada código. Refeito o "
     "ranking, Transporte Rodoviário de Carga sobe de 1,70% para 1,96% de letalidade."),
]

TABELA_4 = [  # REFINE - Novas questoes
    ("Qual padrão chamou atenção?",
     "O acidente de TRAJETO é o mais letal. Ele responde por 22,1% dos registros, contra "
     "73,7% do acidente típico, mas sua letalidade é 2,7 vezes maior (0,877% contra "
     "0,329%). Somado a isso, o setor de Transporte Rodoviário de Carga aparece como o "
     "mais letal entre todos, com 1,96% — 4,3 vezes a média geral."),
    ("Que hipótese ou explicação pode ser levantada?",
     "Os dois achados podem compartilhar o mesmo mecanismo: o TRÂNSITO. O acidente de "
     "trajeto ocorre em via pública, fora do ambiente controlado da empresa, sem os "
     "equipamentos de proteção e os protocolos que reduzem a gravidade dentro do "
     "estabelecimento; e o transporte rodoviário tem a via pública como o próprio local "
     "de trabalho. A hipótese é que a exposição ao trânsito, e não o setor ou o "
     "deslocamento em si, seja o fator associado à maior letalidade."),
    ("Que evidência sustenta essa hipótese?",
     "A convergência entre as duas análises independentes: a taxa por tipo de acidente e "
     "a taxa por setor econômico apontam para o mesmo mecanismo. Reforça a hipótese o "
     "fato de que outros setores do topo do ranking também envolvem via pública ou "
     "veículos — Obras de Terraplenagem (1,61%), Extração de Pedra, Areia e Argila "
     "(1,40%) e Comércio Varejista de Combustíveis (1,21%). A base tem volume suficiente "
     "para sustentar a comparação: 15.646 óbitos em 3,4 milhões de registros."),
    ("Qual é a principal limitação da evidência?",
     "A evidência é ASSOCIATIVA e não permite calcular risco. Três limitações se somam: "
     "(1) não há denominador de exposição — a base registra acidentes, não trabalhadores "
     "expostos nem horas trabalhadas, de modo que 'letalidade' aqui é a proporção de "
     "óbitos ENTRE OS ACIDENTES COMUNICADOS, não a probabilidade de morrer no setor; "
     "(2) a base contém apenas acidentes COMUNICADOS, e a subnotificação é conhecida e "
     "provavelmente desigual entre setores, o que enviesa a comparação; (3) o local do "
     "acidente é desconhecido, pois a única variável geográfica confiável é a do "
     "empregador."),
    ("Que nova pergunta surgiu?",
     "Duas. Primeira: a maior letalidade do trajeto se mantém quando se controla o setor "
     "econômico, ou é o transporte rodoviário que a produz? Um cruzamento tipo × CNAE "
     "responderia. Segunda, e mais estrutural: é possível estimar o RISCO, e não apenas "
     "a proporção de óbitos, incorporando um denominador externo de vínculos "
     "empregatícios — RAIS ou CAGED — por setor e UF?"),
]

TABELA_5 = [  # PRODUCE - Sintese
    ("Os arquivos do acervo se sobrepõem: 11,7% dos registros são republicação, e a "
     "cobertura temporal é irregular.",
     "458.155 de 3.931.904 linhas repetem registro anterior; 8 arquivos não trazem um "
     "único registro novo. Não há arquivo cobrindo as emissões de jan–fev/2022, e a "
     "série mensal oscila de 8 mil a 128 mil sem padrão epidemiológico.",
     "Determina o que é possível analisar. Qualquer contagem — por ano, UF ou setor — "
     "sai inflada em 11,7% se os arquivos forem simplesmente empilhados, e séries "
     "temporais exigem recorte explícito de períodos completos.",
     "A identificação de republicação é feita por igualdade integral da linha, pois os "
     "registros não têm identificador. Duas CATs realmente distintas e idênticas em "
     "todos os campos seriam contadas como uma só."),
    ("O acidente de trajeto é 2,7 vezes mais letal que o típico, e o transporte "
     "rodoviário de carga é o setor mais letal da base.",
     "Letalidade de 0,877% no trajeto contra 0,329% no típico; 6.743 óbitos em trajeto "
     "apesar de o típico ser 3,3 vezes mais frequente. Transporte Rodoviário de Carga "
     "atinge 1,96%, contra média geral de 0,456%.",
     "Aponta um mecanismo comum — a exposição ao trânsito — que atravessa a "
     "classificação por tipo de acidente e a classificação por setor, e sugere um "
     "recorte concreto para o artigo.",
     "É associação, não risco: a base não traz denominador de exposição, e a "
     "subnotificação de acidentes é provavelmente desigual entre setores."),
    ("A variável de UF do acidente está corrompida na origem e é irrecuperável; a "
     "geografia só pode ser analisada pelo empregador.",
     "Os rótulos estão trocados de forma sistemática (São Paulo gravado como 'Maranhão', "
     "1.339.950 registros) e 12 UFs — entre elas RS, SC, BA e GO — não têm rótulo algum, "
     "colapsando em 32,9% da base.",
     "Restringe diretamente o escopo do artigo: qualquer recorte que dependa de ONDE o "
     "acidente ocorreu precisa ser reformulado para 'onde está o empregador'.",
     "A UF do empregador não é substituto adequado: nas linhas em que ambas as "
     "informações existem, elas divergem na maioria dos casos — acidentes de trajeto e "
     "trabalho em campo ocorrem longe da sede."),
]

TABELA_6 = [  # Relacao com o artigo
    ("A pergunta de investigação permanece adequada?",
     "Depende do recorte adotado pelo grupo, e a EDA impõe duas restrições concretas. "
     "Perguntas sobre PERFIL (quem se acidenta, em que setor, com que lesão, com que "
     "desfecho) permanecem plenamente viáveis. Perguntas sobre EVOLUÇÃO TEMPORAL exigem "
     "recorte explícito de anos completos. Perguntas sobre a LOCALIZAÇÃO DO ACIDENTE "
     "precisam ser reformuladas para localização do empregador — a variável do acidente "
     "não é utilizável."),
    ("Quais variáveis devem ser priorizadas?",
     "As de melhor preenchimento e maior poder discriminante: tipo_acidente, "
     "indica_obito, sexo, idade_acidente, cnae_codigo, cbo_codigo, cid10_codigo, "
     "natureza_lesao, parte_corpo_atingida e uf_empregador_sigla. Devem ser evitadas: "
     "uf_acidente (corrompida), data_despacho_beneficio (100% nula), data_afastamento "
     "(79,6% nula) e todas as colunas de DESCRIÇÃO, substituídas pelos códigos "
     "correspondentes."),
    ("Quais limitações dos dados devem ser consideradas?",
     "Cinco, em ordem de impacto: (1) sobreposição entre arquivos, que superconta 11,7% "
     "se ignorada; (2) cobertura temporal irregular, com lacuna em jan–fev/2022 e meses "
     "recentes incompletos; (3) UF do acidente irrecuperável; (4) ausência de "
     "denominador de exposição, que impede calcular risco e permite apenas proporções "
     "entre acidentes comunicados; (5) subnotificação — a base só contém acidentes "
     "COMUNICADOS, e a propensão a comunicar varia entre setores e portes de empresa."),
    ("Há necessidade de dados complementares?",
     "Sim, e é a necessidade mais relevante identificada. Sem um denominador de "
     "exposição — número de vínculos por setor e UF, da RAIS ou do CAGED — o trabalho "
     "fica restrito a descrever a composição dos acidentes, sem poder afirmar onde o "
     "risco é maior. São dados públicos e articuláveis pelo código CNAE, já disponível "
     "na base. Tabelas auxiliares de CNAE, CBO e CID-10 também são necessárias, para "
     "recuperar as descrições que chegam truncadas."),
    ("Que análise deverá ser aprofundada?",
     "O cruzamento entre tipo de acidente e setor econômico, para testar se a maior "
     "letalidade do trajeto persiste quando o setor é controlado ou se é produzida pelo "
     "transporte rodoviário. É a análise que decide entre duas explicações concorrentes "
     "para o principal achado da EDA."),
    ("Qual será o próximo passo do artigo?",
     "Fixar o recorte — período de anos completos, com ou sem denominador externo — e, a "
     "partir dele, executar o cruzamento tipo × setor. A infraestrutura já está pronta: "
     "o pipeline reproduz a base consolidada em cerca de dois minutos a partir dos "
     "arquivos originais, e o relatório descritivo é regerado por um comando."),
]

TABELA_7 = [  # Ferramentas
    ("Python 3.11", "pandas, PyArrow",
     "Leitura, normalização e consolidação dos 61 arquivos; base final em Parquet, "
     "gravada em fluxo para não exigir os 3,9 milhões de registros em memória."),
    ("Python", "matplotlib",
     "Figuras da análise exploratória, com paleta categórica validada para daltonismo."),
    ("Python", "pytest, ruff",
     "114 testes automatizados e verificação de estilo. Os testes usam CSVs em "
     "miniatura, reproduzindo os cinco leiautes reais, e rodam sem depender dos dados."),
    ("Shell / Cloud", "Google Cloud Storage (API pública), urllib",
     "Sincronização dos arquivos do bucket, com repetição em caso de queda e conferência "
     "do tamanho recebido contra o anunciado."),
    ("Git / GitHub", "git",
     "Versionamento do código, da documentação e das decisões de limpeza. Os dados não "
     "são versionados; o pipeline os reconstrói."),
    ("Documentação", "Markdown",
     "Registro das armadilhas dos dados (docs/qualidade-dos-dados.md) e relatório "
     "descritivo regerado automaticamente (reports/relatorio-dados.md)."),
]

FIGURAS = [
    ("serie-mensal.png", "Figura 1 — Acidentes por mês de ocorrência. A irregularidade da "
     "série é artefato da cobertura por mês de emissão, não variação do fenômeno."),
    ("registros-por-uf.png", "Figura 2 — Registros por UF do empregador, derivada do código "
     "IBGE do município."),
    ("idade-por-sexo.png", "Figura 3 — Distribuição etária por sexo. As curvas diferem em "
     "forma: homens concentram-se entre 22 e 28 anos; mulheres formam platô mais tardio."),
    ("letalidade-por-tipo.png", "Figura 4 — Letalidade por tipo de acidente. O trajeto é o "
     "mais letal, apesar de menos frequente que o típico."),
    ("letalidade-por-setor.png", "Figura 5 — Setores com maior letalidade, agrupados pelo "
     "código da CNAE."),
    ("parte-do-corpo.png", "Figura 6 — Partes do corpo mais atingidas."),
]

LEGENDA_WORKFLOW = ("Figura 7 — Workflow da análise exploratória, com cada etapa marcada "
                    "pela fase do ciclo ERP. A seta tracejada indica o retorno ao REFINE "
                    "provocado por achados da etapa de análise.")
