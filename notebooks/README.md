# Notebooks

## `01_consolidacao_e_eda.ipynb`

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mrcsvg/ufpr-ppgcd-acidentes-no-trabalho/blob/claude/novo-projeto-o7g3f2/notebooks/01_consolidacao_e_eda.ipynb)

Notebook de apresentação: sai dos 61 CSVs crus e chega à base consolidada, demonstrando
ao vivo cada armadilha dos dados, e termina na análise exploratória. Roda no Colab sem
instalação local — a primeira célula clona o repositório e instala o pacote.

É verificado por `tests/test_notebook.py`, que confere que o JSON é válido, que toda
célula de código compila, que não há saídas gravadas e que o link do Colab aponta para o
arquivo certo.

## Convenções para novos notebooks

Numere os notebooks na ordem em que devem ser executados:

```
01_exploracao_inicial.ipynb
02_limpeza.ipynb
03_analise_descritiva.ipynb
04_modelagem.ipynb
```

Convenções:

- Cada notebook roda do início ao fim, sem depender de estado deixado por outro.
- Importe os caminhos de `acidentes_trabalho.config` em vez de usar caminhos relativos.
- Quando um trecho de código passar a ser reutilizado, mova-o para `src/acidentes_trabalho/`
  e escreva um teste — o notebook então apenas o importa.
- Figuras que entram no relatório são salvas com `viz.estilo.salvar_figura`.

Início típico de um notebook:

```python
from acidentes_trabalho.config import SEED
from acidentes_trabalho.dados import io
from acidentes_trabalho.viz.estilo import aplicar_estilo, salvar_figura

aplicar_estilo()
```
