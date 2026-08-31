/**
 * Apresentação de 5 minutos sobre a consolidação e a EDA dos microdados de CAT.
 *
 * Rodar:  node reports/apresentacao/gerar_deck.js
 */
const path = require("path");
const PptxGenJS = require("pptxgenjs");

const RAIZ = path.resolve(__dirname, "..", "..");
const FIG = (nome) => path.join(__dirname, "figuras", nome);
const FIG_RELATORIO = (nome) => path.join(RAIZ, "reports", "figuras", nome);
const SAIDA = path.join(__dirname, "apresentacao-cat.pptx");

// Paleta: carvão dominante, âmbar de sinalização como acento (o tema é segurança
// do trabalho), azul vindo da paleta validada das figuras.
const CARVAO = "1C1C1E";
const BRANCO = "FFFFFF";
const AMBAR = "EB6834";
const AZUL = "2A78D6";
const TINTA = "1C1C1E";
const MUDO = "6B6A66";
const SUAVE = "F4F4F2";

const SERIF = "Cambria";
const SANS = "Calibri";

// Canvas padrão 16:9 = 10" × 5.625".
const L = 0.55;             // margem esquerda
const LARG = 10 - 2 * L;    // largura útil
const pres = new PptxGenJS();
pres.layout = "LAYOUT_16x9";
pres.author = "PPGCD/UFPR";
pres.title = "Acidentes de trabalho — consolidação e EDA";

/** Proporções reais das imagens, para não distorcer. */
const PROPORCAO = {
  "esquemas.png": 1.736,
  "letalidade.png": 2.703,
  "republicacao.png": 1.728,
  "uf-trocada.png": 2.586,
  "workflow.png": 2.346,
};

/** Insere a imagem centrada horizontalmente, com altura derivada da proporção. */
function imagem(slide, arquivo, { x, y, w, caminho }) {
  const h = w / PROPORCAO[arquivo];
  slide.addImage({ path: caminho || FIG(arquivo), x, y, w, h });
  return y + h;
}

function titulo(slide, texto, { cor = TINTA, y = 0.42 } = {}) {
  slide.addText(texto, {
    x: L, y, w: LARG, h: 0.62,
    fontFace: SERIF, fontSize: 30, bold: true, color: cor,
    align: "left", isTextBox: true, margin: 0,
  });
}

function selo(slide, numero, { x, y }) {
  slide.addShape(pres.ShapeType.ellipse, {
    x, y, w: 0.34, h: 0.34, fill: { color: AMBAR }, line: { color: AMBAR },
  });
  slide.addText(String(numero), {
    x, y, w: 0.34, h: 0.34,
    fontFace: SANS, fontSize: 15, bold: true, color: BRANCO,
    align: "center", valign: "middle", isTextBox: true, margin: 0,
  });
}

/* ------------------------------------------------------------------ 1. Capa */
{
  const s = pres.addSlide();
  s.background = { color: CARVAO };
  s.addText("De 61 arquivos a uma base única", {
    x: L, y: 1.05, w: 9.0, h: 1.35,
    fontFace: SERIF, fontSize: 40, bold: true, color: BRANCO,
    isTextBox: true, margin: 0,
  });
  s.addText("Análise exploratória dos microdados de CAT · Comunicação de Acidente de Trabalho", {
    x: L, y: 2.42, w: 8.9, h: 0.4,
    fontFace: SANS, fontSize: 16, color: "C9C8C4", isTextBox: true, margin: 0,
  });
  [["3,47 mi", "acidentes"], ["2019–2026", "período"], ["7", "armadilhas"]]
    .forEach(([valor, rotulo], i) => {
      const x = L + i * 2.55;
      s.addText(valor, {
        x, y: 3.15, w: 2.4, h: 0.62,
        fontFace: SERIF, fontSize: 30, bold: true, color: AMBAR,
        isTextBox: true, margin: 0,
      });
      s.addText(rotulo, {
        x, y: 3.78, w: 2.4, h: 0.34,
        fontFace: SANS, fontSize: 13, color: "C9C8C4", isTextBox: true, margin: 0,
      });
    });
  s.addText("PPGCD/UFPR · Atividade 3", {
    x: L, y: 4.72, w: LARG, h: 0.34,
    fontFace: SANS, fontSize: 12, color: MUDO, isTextBox: true, margin: 0,
  });
  s.addNotes(
    "Trabalhamos com os microdados de CAT: toda comunicação de acidente de trabalho " +
    "registrada na Previdência. Em sete minutos vamos percorrer o workflow que " +
    "construímos, as decisões que tomamos e o que os dados revelaram."
  );
}

/* --------------------------------------------- 2. Como a análise começou */
{
  const s = pres.addSlide();
  titulo(s, "Como a análise começou");

  const passos = [
    ["Uma pasta compartilhada", "61 arquivos CSV, 1,8 GB, sem documentação além de um dicionário de 2021"],
    ["Uma pergunta ampla", "quem se acidenta no trabalho no Brasil, em que setores, com que gravidade"],
    ["Um obstáculo imediato", "antes de qualquer análise, era preciso descobrir o que havia nos arquivos"],
  ];
  passos.forEach(([forte, resto], i) => {
    const y = 1.35 + i * 1.02;
    selo(s, i + 1, { x: L, y: y + 0.02 });
    s.addText(forte, {
      x: L + 0.5, y, w: 3.0, h: 0.34,
      fontFace: SANS, fontSize: 15, bold: true, color: TINTA,
      isTextBox: true, margin: 0,
    });
    s.addText(resto, {
      x: L + 3.6, y: y + 0.02, w: 5.3, h: 0.72,
      fontFace: SANS, fontSize: 13, color: MUDO, isTextBox: true, margin: 0,
    });
  });

  s.addText(
    "A primeira pergunta não foi sobre acidentes. Foi: estes arquivos têm o mesmo formato?",
    {
      x: L, y: 4.62, w: LARG, h: 0.5,
      fontFace: SANS, fontSize: 14, italic: true, color: AMBAR,
      isTextBox: true, margin: 0,
    }
  );
  s.addNotes(
    "Recebemos uma pasta com 61 arquivos e um dicionário oficial de 2021. A pergunta " +
    "de partida era ampla. Mas descobrimos logo que antes de analisar era preciso " +
    "entender o que estava nos arquivos — e essa virou a maior parte do trabalho."
  );
}

/* ------------------------------------------------------- 3. O workflow ERP */
{
  const s = pres.addSlide();
  titulo(s, "O workflow da análise");
  imagem(s, "workflow.png", { x: 0.72, y: 1.15, w: 8.55, caminho: FIG_RELATORIO("workflow.png") });
  s.addText(
    "A seta tracejada é a parte honesta: voltamos ao REFINE duas vezes, porque a " +
    "análise revelou problemas que a exploração inicial não pegou.",
    {
      x: L, y: 4.9, w: LARG, h: 0.55,
      fontFace: SANS, fontSize: 13.5, italic: true, color: AMBAR,
      isTextBox: true, margin: 0,
    }
  );
  s.addNotes(
    "Este é o workflow. Cinco etapas, marcadas pela fase do ciclo ERP: explorar, " +
    "refinar, produzir. O importante é que ele não foi linear — a seta tracejada " +
    "mostra os retornos. Vamos percorrer cada fase."
  );
}

/* ---------------------------------------------------------- 4. EXPLORE */
{
  const s = pres.addSlide();
  titulo(s, "EXPLORE — conhecer os dados");

  const itens = [
    ["Cabeçalho de cada arquivo", "sem baixar 1,8 GB: requisições HTTP Range de 3 KB"],
    ["Encoding e formato de data", "conferidos contra o dado, não contra o dicionário"],
    ["Domínios, nulos, cardinalidade", "relatório descritivo gerado automaticamente"],
  ];
  itens.forEach(([forte, resto], i) => {
    const y = 1.32 + i * 0.9;
    selo(s, i + 1, { x: L, y: y + 0.02 });
    s.addText(forte, {
      x: L + 0.5, y, w: 3.9, h: 0.32,
      fontFace: SANS, fontSize: 14, bold: true, color: TINTA,
      isTextBox: true, margin: 0,
    });
    s.addText(resto, {
      x: L + 0.5, y: y + 0.31, w: 4.0, h: 0.48,
      fontFace: SANS, fontSize: 12, color: MUDO, isTextBox: true, margin: 0,
    });
  });

  imagem(s, "esquemas.png", { x: 5.2, y: 1.22, w: 4.25 });

  s.addText(
    "Descoberta: 61 arquivos, 4 formatos incompatíveis — e rótulos de coluna que não " +
    "correspondem ao conteúdo. Empilhar por nome não dá erro; dá resultado errado.",
    {
      x: L, y: 4.35, w: LARG, h: 0.6,
      fontFace: SANS, fontSize: 13.5, color: TINTA, isTextBox: true, margin: 0,
    }
  );
  s.addNotes(
    "No EXPLORE, começamos pelo cabeçalho de cada arquivo — usando requisições Range, " +
    "para não baixar tudo. Encontramos cinco cabeçalhos, quatro formatos. E, pior, " +
    "colunas cujo rótulo não corresponde ao conteúdo. Isso definiu toda a arquitetura: " +
    "o leitor mapeia por posição, não por nome."
  );
}

/* ------------------------------------------------- 5. REFINE — decisão 1 */
{
  const s = pres.addSlide();
  titulo(s, "REFINE — a coluna que mentia");
  imagem(s, "uf-trocada.png", { x: L, y: 1.18, w: 8.6 });
  s.addText(
    "São Paulo estava gravado como “Maranhão”. E 12 UFs — RS, SC, BA entre elas — não " +
    "têm rótulo algum: 33% da base. Decisão: usar a UF derivada do código IBGE.",
    {
      x: L, y: 4.66, w: LARG, h: 0.6,
      fontFace: SANS, fontSize: 13.5, color: TINTA, isTextBox: true, margin: 0,
    }
  );
  s.addNotes(
    "Primeira decisão do REFINE. A UF do acidente tinha Maranhão em primeiro lugar e " +
    "São Paulo ausente. Cruzando com a UF derivada do código IBGE do município, vimos " +
    "que os rótulos estão trocados de forma sistemática, e que doze estados não têm " +
    "rótulo nenhum. A coluna é irrecuperável — descartamos e usamos a do empregador."
  );
}

/* ------------------------------------------------- 6. REFINE — decisão 2 */
{
  const s = pres.addSlide();
  titulo(s, "REFINE — os arquivos que se repetiam");
  imagem(s, "republicacao.png", { x: L, y: 1.25, w: 5.1 });

  [["11,7%", "das linhas já haviam sido publicadas"],
   ["8 arquivos", "sem um único registro novo"],
   ["458 mil", "de diferença na contagem"]].forEach(([valor, rotulo], i) => {
    const y = 1.42 + i * 1.06;
    s.addText(valor, {
      x: 6.0, y, w: 3.5, h: 0.45,
      fontFace: SERIF, fontSize: 24, bold: true, color: AMBAR,
      isTextBox: true, margin: 0,
    });
    s.addText(rotulo, {
      x: 6.0, y: y + 0.44, w: 3.5, h: 0.5,
      fontFace: SANS, fontSize: 12.5, color: MUDO, isTextBox: true, margin: 0,
    });
  });

  s.addText(
    "Marcamos em vez de apagar: a base guarda o problema e a decisão fica auditável.",
    {
      x: L, y: 4.72, w: LARG, h: 0.45,
      fontFace: SANS, fontSize: 13.5, italic: true, color: AMBAR,
      isTextBox: true, margin: 0,
    }
  );
  s.addNotes(
    "Segunda decisão. Os arquivos não são partições disjuntas: cada um cobre uma " +
    "janela de mês de emissão, e as janelas se sobrepõem. Oito arquivos são " +
    "republicação integral. Optamos por marcar a repetição numa coluna, em vez de " +
    "apagar a linha — assim quem revisa consegue conferir a decisão."
  );
}

/* --------------------------------------------------------- 7. PRODUCE */
{
  const s = pres.addSlide();
  titulo(s, "PRODUCE — o que foi produzido");

  const entregas = [
    ["Base única", "3,47 milhões de registros · 1,8 GB de CSV → 94 MB de Parquet"],
    ["Pipeline reproduzível", "quatro etapas retomáveis · reconstrói tudo em 2 minutos"],
    ["Relatório automatizado", "volume, cobertura, domínios e consistência, regerado por comando"],
    ["Notebook no Colab", "a consolidação explicada passo a passo, executável por qualquer um"],
  ];
  entregas.forEach(([forte, resto], i) => {
    const y = 1.3 + i * 0.82;
    selo(s, i + 1, { x: L, y: y + 0.02 });
    s.addText(forte, {
      x: L + 0.5, y, w: 2.9, h: 0.32,
      fontFace: SANS, fontSize: 14, bold: true, color: TINTA,
      isTextBox: true, margin: 0,
    });
    s.addText(resto, {
      x: L + 3.45, y: y + 0.02, w: 5.45, h: 0.6,
      fontFace: SANS, fontSize: 12.5, color: MUDO, isTextBox: true, margin: 0,
    });
  });

  s.addText("122 testes automatizados sustentam cada decisão de limpeza.", {
    x: L, y: 4.72, w: LARG, h: 0.45,
    fontFace: SANS, fontSize: 13.5, italic: true, color: AMBAR,
    isTextBox: true, margin: 0,
  });
  s.addNotes(
    "O PRODUCE entregou quatro coisas: a base consolidada, o pipeline que a " +
    "reconstrói, um relatório descritivo que se regenera sozinho e um notebook que " +
    "explica a consolidação. Tudo sustentado por 122 testes — cada decisão de limpeza " +
    "tem um teste que a documenta."
  );
}

/* ------------------------------------------------ 8. Ferramentas por etapa */
{
  const s = pres.addSlide();
  titulo(s, "Ferramentas em cada etapa");

  const colunas = [
    ["EXPLORE", AZUL, ["urllib + HTTP Range", "pandas", "PyArrow"],
     "ler cabeçalhos sem baixar tudo; perfilar domínios e nulos"],
    ["REFINE", AMBAR, ["pandas", "pytest", "ruff"],
     "normalizar os 4 formatos; cada decisão com teste que a fixa"],
    ["PRODUCE", "1BAF7A", ["Parquet + zstd", "matplotlib", "Colab · Git"],
     "base consolidada, figuras e notebook reproduzível"],
  ];
  colunas.forEach(([fase, cor, ferramentas, papel], i) => {
    const x = L + i * 3.05;
    s.addShape(pres.ShapeType.roundRect, {
      x, y: 1.28, w: 2.8, h: 3.05, rectRadius: 0.06,
      fill: { color: SUAVE }, line: { color: SUAVE },
    });
    s.addText(fase, {
      x: x + 0.2, y: 1.45, w: 2.4, h: 0.32,
      fontFace: SANS, fontSize: 13, bold: true, color: cor,
      isTextBox: true, margin: 0,
    });
    ferramentas.forEach((ferramenta, j) => {
      s.addText(ferramenta, {
        x: x + 0.2, y: 1.85 + j * 0.34, w: 2.4, h: 0.3,
        fontFace: SANS, fontSize: 12.5, color: TINTA, isTextBox: true, margin: 0,
      });
    });
    s.addText(papel, {
      x: x + 0.2, y: 3.0, w: 2.4, h: 1.15,
      fontFace: SANS, fontSize: 11.5, color: MUDO, isTextBox: true, margin: 0,
    });
  });

  s.addText(
    "Python em todas as etapas. O que mudou foi o papel: explorar com requisições " +
    "leves, refinar com testes, produzir com formato colunar.",
    {
      x: L, y: 4.55, w: LARG, h: 0.55,
      fontFace: SANS, fontSize: 13, color: TINTA, isTextBox: true, margin: 0,
    }
  );
  s.addNotes(
    "As ferramentas foram basicamente as mesmas — Python, pandas — mas o papel mudou " +
    "em cada fase. No EXPLORE, requisições HTTP leves para não baixar 1,8 GB só para " +
    "ver um cabeçalho. No REFINE, pytest: cada decisão de limpeza virou teste. No " +
    "PRODUCE, Parquet comprimido e Colab."
  );
}

/* ------------------------------------------------ 9. Principais resultados */
{
  const s = pres.addSlide();
  titulo(s, "Principais resultados: trajeto mata mais");
  imagem(s, "letalidade.png", { x: L, y: 1.2, w: 8.9 });
  s.addText(
    "O acidente de trajeto é 2,7× mais letal que o típico, apesar de 3,3× menos " +
    "frequente. E o transporte rodoviário lidera entre os setores, com 4× a média. " +
    "Duas análises independentes apontando para o mesmo mecanismo: o trânsito.",
    {
      x: L, y: 4.55, w: LARG, h: 0.85,
      fontFace: SANS, fontSize: 13.5, color: TINTA, isTextBox: true, margin: 0,
    }
  );
  s.addNotes(
    "O achado principal. O trajeto é minoria dos acidentes, mas o mais letal — 2,7 " +
    "vezes o típico. E o setor mais letal é o transporte rodoviário de carga, com " +
    "quatro vezes a média geral. Duas análises independentes apontando para o " +
    "trânsito. É a hipótese que vamos aprofundar."
  );
}

/* ------------------------------------------ 10. Como a EDA ajuda o artigo */
{
  const s = pres.addSlide();
  s.background = { color: CARVAO };
  titulo(s, "Como a EDA contribui para o artigo", { cor: BRANCO, y: 0.5 });

  const contribuicoes = [
    ["Delimitou o que é possível", "geografia só pelo empregador; série temporal só em períodos completos"],
    ["Deu a hipótese", "exposição ao trânsito, sustentada por duas análises independentes"],
    ["Expôs a limitação central", "sem denominador de exposição, medimos composição — não risco"],
    ["Definiu o próximo passo", "cruzar tipo × setor e buscar vínculos da RAIS por CNAE"],
  ];
  contribuicoes.forEach(([forte, resto], i) => {
    const y = 1.4 + i * 0.86;
    selo(s, i + 1, { x: L, y: y + 0.02 });
    s.addText(forte, {
      x: L + 0.5, y, w: 3.0, h: 0.34,
      fontFace: SANS, fontSize: 14, bold: true, color: AMBAR,
      isTextBox: true, margin: 0,
    });
    s.addText(resto, {
      x: L + 3.6, y: y + 0.02, w: 5.3, h: 0.66,
      fontFace: SANS, fontSize: 12.5, color: "C9C8C4", isTextBox: true, margin: 0,
    });
  });

  s.addText("github.com/mrcsvg/ufpr-ppgcd-acidentes-no-trabalho", {
    x: L, y: 4.95, w: LARG, h: 0.32,
    fontFace: SANS, fontSize: 11.5, color: MUDO, isTextBox: true, margin: 0,
  });
  s.addNotes(
    "A EDA fez quatro coisas pelo artigo. Delimitou o escopo: a geografia só pode ser " +
    "do empregador. Deu a hipótese do trânsito. Expôs a limitação central — sem " +
    "denominador de exposição, estamos medindo composição, não risco. E definiu o " +
    "próximo passo: cruzar tipo com setor e buscar vínculos da RAIS."
  );
}

pres.writeFile({ fileName: SAIDA }).then(() => console.log("gravado: " + SAIDA));
