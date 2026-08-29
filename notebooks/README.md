# Notebooks

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
