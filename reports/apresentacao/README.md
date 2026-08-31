# Apresentação

Deck de 7 minutos sobre o workflow da análise exploratória, cobrindo os sete
tópicos exigidos na Atividade 3.

```bash
make apresentacao
```

Roda três passos: gera as figuras dedicadas (maiores e mais limpas que as do
relatório, para projeção), monta o `.pptx` e audita a geometria.

## Sobre a auditoria

O LibreOffice não funciona neste ambiente, então **não foi possível renderizar os
slides e inspecioná-los visualmente**. `auditar_deck.py` cobre por cálculo o que a
vista pegaria: elemento fora do slide, margem insuficiente, sobreposição entre
formas e texto que não cabe na caixa. Ele encontrou 13 problemas reais na primeira
versão — incluindo uma imagem invadindo os números do slide 5 em 0,57".

Ainda assim, **abra o arquivo uma vez antes de apresentar**: fontes são
substituídas pelo PowerPoint de quem projeta, e a auditoria estima larguras de
texto, não as mede.

## Estrutura

| Arquivo | O que é |
|---|---|
| `gerar_deck.js` | Monta o `.pptx` com pptxgenjs — todo o conteúdo e o layout |
| `figuras_slides.py` | Figuras em proporção 16:9, com fonte grande |
| `auditar_deck.py` | Auditoria geométrica, no lugar da inspeção visual |
| `apresentacao-cat.pptx` | O deck |

## Abrir no Google Slides

Arraste `apresentacao-cat.pptx` para o Google Drive e abra com **Apresentações
Google** — a conversão preserva texto, imagens e notas do apresentador.

## Roteiro (11 slides · ~38s cada)

| # | Slide | Tópico exigido |
|---|---|---|
| 1 | Capa | — |
| 2 | Como a análise começou | *Como a análise começou* |
| 3 | O workflow da análise | *Representação visual do tópico 6* |
| 4 | EXPLORE — conhecer os dados | *O que foi realizado no EXPLORE* |
| 5 | As 7 armadilhas que encontramos | *(resultado do EXPLORE)* |
| 6 | REFINE — a coluna que mentia | *Decisões do REFINE (1/2)* |
| 7 | REFINE — os arquivos que se repetiam | *Decisões do REFINE (2/2)* |
| 8 | PRODUCE — o que foi produzido | *O que foi produzido no PRODUCE* |
| 9 | Ferramentas em cada etapa | *Ferramentas por etapa* |
| 10 | Principais resultados | *Principais resultados* |
| 11 | Como a EDA contribui para o artigo | *Contribuição para o artigo* |

O slide 5 lista as sete armadilhas na mesma ordem de gravidade de
[`docs/qualidade-dos-dados.md`](../../docs/qualidade-dos-dados.md); as duas
primeiras, em âmbar, ganham slide próprio em seguida.

As notas do apresentador estão em cada slide (`Exibir → Anotações`) e somam ~3,2
minutos de fala roteirizada — o resto do tempo é para respirar e responder.
