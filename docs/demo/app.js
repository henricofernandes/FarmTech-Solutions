/*
 * Demonstração web da interface do FarmTech Solutions.
 *
 * Navegador não executa Python nem R, então as fórmulas do farmtech.py e a
 * saída do estatisticas.R foram reproduzidas aqui. Os números e o texto
 * seguem o mesmo formato do programa original para poderem ser comparados
 * lado a lado. O clima é consultado na mesma API Open-Meteo do clima.R.
 *
 * Os talhões são lidos do CSV real do repositório, para não existir uma
 * segunda cópia dos dados envelhecendo aqui dentro.
 */

"use strict";

const REPO = "https://raw.githubusercontent.com/henricofernandes/FarmTech-Solutions/main";

// Mesmo par cultura/manejo do ler_cultura() no farmtech.py.
const CULTURAS = [
  ["Soja", "Fosfato líquido"],
  ["Milho", "Adubo nitrogenado líquido"],
];

// O mesmo local padrão definido no clima.R.
const CIDADE_PADRAO = "Sorriso - MT";
const LOCAL_PADRAO = "Sorriso - MT (Brasil)";
const LATITUDE_PADRAO = -12.5453;
const LONGITUDE_PADRAO = -55.7113;
const FUSO = "America/Sao_Paulo";
const DIAS_PREVISAO = 2;
const CIDADE_DESCONHECIDA = "não informada";

// Vetores paralelos: a mesma posição em todos é o mesmo talhão.
let culturas = [];
let manejos = [];
let lados = [];
let ruas = [];
let doses = [];
let cidades = [];

let cidadeAtual = CIDADE_PADRAO;
let selecionada = null;

const el = (id) => document.getElementById(id);

// ---------------------------------------------------------------- cálculos

const calcularArea = (lado) => lado * lado;
const calcularInsumo = (lado, qtdRuas, dose) => (lado * qtdRuas * dose) / 1000;

const manejoDaCultura = (cultura) => {
  const par = CULTURAS.find(([nome]) => nome === cultura);
  return par ? par[1] : "";
};

const doisDecimais = (valor) => valor.toFixed(2);

// Equivalente ao %g do Python: 100 vira "100" e 100.5 continua "100.5".
const semZeroAToa = (valor) => String(Number(valor));

// ------------------------------------------------------------------ leitura

/* Divide uma linha de CSV respeitando campos entre aspas. */
function dividirLinha(linha) {
  const campos = [];
  let atual = "";
  let dentroDeAspas = false;

  for (let i = 0; i < linha.length; i += 1) {
    const c = linha[i];
    if (c === '"') {
      if (dentroDeAspas && linha[i + 1] === '"') {
        atual += '"';
        i += 1;
      } else {
        dentroDeAspas = !dentroDeAspas;
      }
    } else if (c === "," && !dentroDeAspas) {
      campos.push(atual);
      atual = "";
    } else {
      atual += c;
    }
  }
  campos.push(atual);
  return campos;
}

function lerCsv(texto) {
  const linhas = texto.replace(/\r/g, "").split("\n").filter((l) => l.trim() !== "");
  if (linhas.length === 0) return [];

  const cabecalho = dividirLinha(linhas[0]);
  return linhas.slice(1).map((linha) => {
    const campos = dividirLinha(linha);
    const registro = {};
    cabecalho.forEach((nome, i) => { registro[nome] = campos[i]; });
    return registro;
  });
}

async function carregarDoRepositorio() {
  const [respDados, respCidades] = await Promise.all([
    fetch(`${REPO}/dados/dados_agricultura.csv`, { cache: "no-store" }),
    fetch(`${REPO}/dados/cidades.csv`, { cache: "no-store" }),
  ]);

  if (!respDados.ok) throw new Error(`o CSV não pôde ser lido (HTTP ${respDados.status})`);

  const registros = lerCsv(await respDados.text());

  culturas = []; manejos = []; lados = []; ruas = []; doses = []; cidades = [];

  registros.forEach((linha) => {
    culturas.push(linha.cultura);
    manejos.push(linha.manejo);
    lados.push(parseFloat(linha.lado));
    ruas.push(parseInt(linha.ruas, 10));
    doses.push(parseFloat(linha.dose));
  });

  // Igual ao carregar_cidades(): fora de sincronia, não afirma a cidade de ninguém.
  let salvas = [];
  if (respCidades.ok) {
    salvas = lerCsv(await respCidades.text()).map((l) => l.cidade);
  }
  cidades = salvas.length === culturas.length
    ? salvas
    : new Array(culturas.length).fill(CIDADE_DESCONHECIDA);
}

// ------------------------------------------------------------------ desenho

/* O quadrado do talhão e as ruas dentro dele, como no _desenhar_talhao(). */
function desenharTalhao(lado, qtdRuas) {
  const x0 = 45, y0 = 15, x1 = 165, y1 = 135;
  const partes = [
    `<rect x="${x0}" y="${y0}" width="${x1 - x0}" height="${y1 - y0}"`,
    ` fill="#f4f9f5" stroke="#1d6b38" stroke-width="1.5"/>`,
  ];

  // Acima de 60 ruas as linhas viram uma mancha; o traço fica só indicativo.
  if (qtdRuas > 0) {
    const linhas = Math.min(qtdRuas, 60);
    const passo = (x1 - x0) / (linhas + 1);
    for (let i = 1; i <= linhas; i += 1) {
      const x = x0 + passo * i;
      partes.push(`<line x1="${x}" y1="${y0 + 4}" x2="${x}" y2="${y1 - 4}" stroke="#7fbe90"/>`);
    }
  }

  const medida = lado > 0 ? `${doisDecimais(lado)} m` : "lado";
  partes.push(
    `<text x="${(x0 + x1) / 2}" y="${y1 + 16}" text-anchor="middle"`,
    ` fill="#5d6f62" font-size="9" font-family="Segoe UI, sans-serif">${medida}</text>`,
    `<text x="${x0 - 12}" y="${(y0 + y1) / 2}" text-anchor="middle" fill="#5d6f62"`,
    ` font-size="9" font-family="Segoe UI, sans-serif"`,
    ` transform="rotate(-90 ${x0 - 12} ${(y0 + y1) / 2})">lado</text>`,
  );

  el("desenho").innerHTML = partes.join("");
}

// ------------------------------------------------------------------ interface

function culturaEscolhida() {
  return document.querySelector('input[name="cultura"]:checked').value;
}

function valoresDoFormulario(silencioso) {
  const bruto = [
    ["Lado do talhão", el("lado").value],
    ["Quantidade de ruas", el("ruas").value],
    ["Dose do insumo", el("dose").value],
  ];

  if (bruto.some(([, v]) => v.trim() === "")) return null;

  const lado = parseFloat(bruto[0][1]);
  const qtdRuas = parseInt(bruto[1][1], 10);
  const dose = parseFloat(bruto[2][1]);

  for (const [rotulo, valor] of [["Lado do talhão", lado], ["Quantidade de ruas", qtdRuas], ["Dose do insumo", dose]]) {
    if (!Number.isFinite(valor) || valor <= 0) {
      if (!silencioso) atualizarStatus(`${rotulo} precisa ser um número maior que zero.`);
      return null;
    }
  }

  return { lado, qtdRuas, dose };
}

function atualizarPrevia() {
  const v = valoresDoFormulario(true);
  el("manejo").textContent = `Manejo: ${manejoDaCultura(culturaEscolhida())}`;

  if (!v) {
    el("previa-area").textContent = "—";
    el("previa-insumo").textContent = "—";
    desenharTalhao(0, 0);
    return;
  }

  el("previa-area").textContent = `${doisDecimais(calcularArea(v.lado))} m²`;
  el("previa-insumo").textContent = `${doisDecimais(calcularInsumo(v.lado, v.qtdRuas, v.dose))} L`;
  desenharTalhao(v.lado, v.qtdRuas);
}

function preencherTabela() {
  const corpo = document.querySelector("#tabela tbody");
  corpo.innerHTML = "";

  culturas.forEach((cultura, posicao) => {
    const lado = lados[posicao];
    const qtdRuas = ruas[posicao];
    const dose = doses[posicao];

    const tr = document.createElement("tr");
    if (posicao === selecionada) tr.className = "escolhida";
    tr.dataset.posicao = String(posicao);

    [
      [posicao, true],
      [cidades[posicao], false],
      [cultura, false],
      [manejos[posicao], false],
      [doisDecimais(lado), true],
      [qtdRuas, true],
      [doisDecimais(dose), true],
      [doisDecimais(calcularArea(lado)), true],
      [doisDecimais(calcularInsumo(lado, qtdRuas, dose)), true],
    ].forEach(([valor, numerico]) => {
      const td = document.createElement("td");
      td.textContent = valor;
      if (numerico) td.className = "num";
      tr.appendChild(td);
    });

    tr.addEventListener("click", () => {
      selecionada = posicao;
      preencherTabela();
    });
    corpo.appendChild(tr);
  });
}

function atualizarStatus(mensagem) {
  el("rotulo-cidade").textContent = `Cidade dos próximos cadastros: ${cidadeAtual}`;

  const total = culturas.length;
  let resumo;
  if (total > 0) {
    const area = lados.reduce((soma, lado) => soma + calcularArea(lado), 0);
    const insumo = lados.reduce(
      (soma, lado, i) => soma + calcularInsumo(lado, ruas[i], doses[i]), 0);
    resumo = `${total} registro(s)  |  área total ${doisDecimais(area)} m²  |  `
           + `insumo total ${doisDecimais(insumo)} L`;
  } else {
    resumo = "Nenhum registro cadastrado.";
  }

  el("status").textContent = mensagem ? `${resumo}  ${mensagem}` : resumo;
}

function escreverSaida(texto) {
  el("saida").textContent = texto.trim() || "(nenhuma saída)";
}

// ------------------------------------------------------------------ ações

function cadastrar() {
  const v = valoresDoFormulario(false);
  if (!v) {
    if (el("lado").value.trim() === "") atualizarStatus("Preencha os três campos para cadastrar.");
    return;
  }

  const cultura = culturaEscolhida();
  culturas.push(cultura);
  manejos.push(manejoDaCultura(cultura));
  lados.push(v.lado);
  ruas.push(v.qtdRuas);
  doses.push(v.dose);
  cidades.push(cidadeAtual);

  selecionada = culturas.length - 1;
  preencherTabela();
  atualizarStatus(`Talhão cadastrado na posição ${selecionada}.`);
  limpar(true);
  document.querySelector("tr.escolhida")?.scrollIntoView({ block: "nearest" });
}

function atualizar() {
  if (selecionada === null) {
    atualizarStatus("Escolha um registro na tabela para atualizar.");
    return;
  }
  const v = valoresDoFormulario(false);
  if (!v) return;

  const cultura = culturaEscolhida();
  culturas[selecionada] = cultura;
  manejos[selecionada] = manejoDaCultura(cultura);
  lados[selecionada] = v.lado;
  ruas[selecionada] = v.qtdRuas;
  doses[selecionada] = v.dose;

  preencherTabela();
  atualizarStatus(`Posição ${selecionada} atualizada.`);
}

function deletar() {
  if (selecionada === null) {
    atualizarStatus("Escolha um registro na tabela para deletar.");
    return;
  }

  const posicao = selecionada;
  const resumo = `${culturas[posicao]} de ${doisDecimais(lados[posicao])} m em ${cidades[posicao]}`;
  if (!window.confirm(`Excluir o registro da posição ${posicao}?\n\n${resumo}`)) {
    atualizarStatus("Exclusão cancelada.");
    return;
  }

  // Remove a mesma posição dos seis vetores para não perder a sincronia.
  [culturas, manejos, lados, ruas, doses, cidades].forEach((vetor) => vetor.splice(posicao, 1));
  selecionada = null;

  preencherTabela();
  atualizarStatus(`Registro da posição ${posicao} removido.`);
}

function carregarNoFormulario() {
  if (selecionada === null) {
    atualizarStatus("Escolha um registro na tabela para editar.");
    return;
  }
  document.querySelector(`input[name="cultura"][value="${culturas[selecionada]}"]`).checked = true;
  el("lado").value = semZeroAToa(lados[selecionada]);
  el("ruas").value = String(ruas[selecionada]);
  el("dose").value = semZeroAToa(doses[selecionada]);
  atualizarPrevia();
  atualizarStatus(`Posição ${selecionada} carregada. Edite e use "Atualizar selecionado".`);
}

function limpar(semMensagem) {
  el("lado").value = "";
  el("ruas").value = "";
  el("dose").value = "";
  atualizarPrevia();
  if (!semMensagem) atualizarStatus("Campos limpos.");
}

async function recarregar() {
  atualizarStatus("Lendo o CSV do repositório...");
  try {
    await carregarDoRepositorio();
    selecionada = null;
    preencherTabela();
    atualizarPrevia();
    atualizarStatus("Dados recarregados do CSV.");
  } catch (erro) {
    atualizarStatus(`Não foi possível ler o CSV: ${erro.message}`);
  }
}

// ------------------------------------------------- estatísticas (era o R)

const traco = (caractere) => "\n" + caractere.repeat(40) + "\n";

/* O sd() do R é o desvio padrão amostral, com divisão por n-1. */
function desvioPadraoAmostral(valores) {
  if (valores.length < 2) return NaN;
  const media = valores.reduce((a, b) => a + b, 0) / valores.length;
  const soma = valores.reduce((acc, v) => acc + (v - media) ** 2, 0);
  return Math.sqrt(soma / (valores.length - 1));
}

function formatar(valor, unidade) {
  if (!Number.isFinite(valor)) return "indisponível (é preciso pelo menos 2 registros)";
  return `${valor.toFixed(2)} ${unidade}`;
}

function bloco(titulo, valores, unidade) {
  const media = valores.reduce((a, b) => a + b, 0) / valores.length;
  return traco("-") + "\n" + titulo + "\n\n"
       + `Média: ${formatar(media, unidade)}\n`
       + `Desvio padrão: ${formatar(desvioPadraoAmostral(valores), unidade)}\n`;
}

function consultarEstatisticas() {
  if (culturas.length === 0) {
    escreverSaida("\nO arquivo existe, mas não possui registros.\n"
                + "Cadastre talhões no programa em Python para gerar os dados.\n");
    atualizarStatus("Nenhum registro para calcular.");
    return;
  }

  const areas = lados.map(calcularArea);
  const insumos = lados.map((lado, i) => calcularInsumo(lado, ruas[i], doses[i]));

  escreverSaida(
    traco("=")
    + "ESTATÍSTICAS FARMTECH\n"
    + `\nQuantidade de registros: ${culturas.length}\n`
    + bloco("ÁREA DOS TALHÕES", areas, "m²")
    + bloco("DOSE DOS INSUMOS", doses, "mL/m")
    + bloco("QUANTIDADE DE INSUMO", insumos, "L")
    + traco("=")
  );
  atualizarStatus("Estatísticas calculadas.");
}

// ------------------------------------------------------- clima (Open-Meteo)

function medida(rotulo, valor, unidade, casas = 1) {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) {
    return `${rotulo}: não informado pela API\n`;
  }
  return `${rotulo}: ${valor.toFixed(casas)} ${unidade}\n`;
}

async function buscarCidade(cidade) {
  const url = "https://geocoding-api.open-meteo.com/v1/search"
            + `?name=${encodeURIComponent(cidade)}&count=1&language=pt&country=BR`;
  const resposta = await fetch(url);
  if (!resposta.ok) return null;

  const dados = await resposta.json();
  if (!dados.results || dados.results.length === 0) return null;

  const achada = dados.results[0];
  return {
    nome: `${achada.name} - ${achada.admin1 || "Brasil"} (Brasil)`,
    latitude: achada.latitude,
    longitude: achada.longitude,
  };
}

async function consultarClima() {
  const escolhida = el("cidade").value.trim() || CIDADE_PADRAO;

  escreverSaida(`\nConsultando a Open-Meteo para ${escolhida}...\n`);
  atualizarStatus(`Consultando o clima de ${escolhida}...`);

  let local;
  if (escolhida === CIDADE_PADRAO) {
    // Mesmo atalho do clima.R: o local padrão já tem coordenadas fixas.
    local = { nome: LOCAL_PADRAO, latitude: LATITUDE_PADRAO, longitude: LONGITUDE_PADRAO };
  } else {
    local = await buscarCidade(escolhida);
    if (!local) {
      escreverSaida("\nNão encontrei nenhuma cidade brasileira com esse nome.\n"
                  + "Confira a grafia e tente de novo (exemplo: Rio Verde).\n");
      el("cidade").value = cidadeAtual;
      atualizarStatus(`A cidade continua sendo ${cidadeAtual}.`);
      return;
    }
  }

  const url = "https://api.open-meteo.com/v1/forecast"
            + `?latitude=${local.latitude}&longitude=${local.longitude}`
            + "&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
            + "&hourly=temperature_2m,relative_humidity_2m,precipitation"
            + `&forecast_days=${DIAS_PREVISAO}&timezone=${encodeURIComponent(FUSO)}`;

  let resposta;
  try {
    const bruta = await fetch(url);
    if (!bruta.ok) throw new Error(`HTTP ${bruta.status}`);
    resposta = await bruta.json();
  } catch (erro) {
    escreverSaida("\nNão foi possível obter os dados meteorológicos.\n"
                + `Motivo: ${erro.message}\n`
                + "Verifique sua conexão com a internet e tente novamente.\n");
    atualizarStatus("Falha ao consultar o clima.");
    return;
  }

  const atual = resposta.current;
  const previsao = resposta.hourly;
  if (!atual || !previsao || !previsao.temperature_2m) {
    escreverSaida("\nA resposta da API veio em um formato inesperado.\n"
                + "Os dados de clima não puderam ser lidos.\n");
    return;
  }

  const temperaturas = previsao.temperature_2m.filter((v) => v !== null);
  const chuva = previsao.precipitation.filter((v) => v !== null);

  escreverSaida(
    traco("=")
    + "CLIMA - FARMTECH SOLUTIONS\n"
    + `\nLocal: ${local.nome}\n`
    + `Latitude: ${local.latitude} | Longitude: ${local.longitude}\n`
    + `Medição: ${String(atual.time).replace("T", " às ")} (${FUSO})\n`
    + traco("-")
    + "\nCONDIÇÕES ATUAIS\n\n"
    + medida("Temperatura", atual.temperature_2m, "°C")
    + medida("Umidade relativa", atual.relative_humidity_2m, "%", 0)
    + medida("Precipitação", atual.precipitation, "mm")
    + medida("Velocidade do vento", atual.wind_speed_10m, "km/h")
    + traco("-")
    + `\nTEMPERATURA PREVISTA PARA ${DIAS_PREVISAO * 24} HORAS\n\n`
    + medida("Média", temperaturas.reduce((a, b) => a + b, 0) / temperaturas.length, "°C")
    + medida("Máxima", Math.max(...temperaturas), "°C")
    + medida("Mínima", Math.min(...temperaturas), "°C")
    + `Horas coletadas: ${temperaturas.length}\n`
    + traco("-")
    + "\nCHUVA PREVISTA NO PERÍODO\n\n"
    + medida("Total acumulado", chuva.reduce((a, b) => a + b, 0), "mm")
    + traco("=")
  );

  // Mesmo resumo que o interface.py mostra no cabeçalho.
  el("rotulo-clima").textContent = [
    local.nome,
    `${atual.temperature_2m.toFixed(1)} °C`,
    `umidade ${Math.round(atual.relative_humidity_2m)}%`,
  ].join("  ·  ");

  if (escolhida !== cidadeAtual) {
    cidadeAtual = escolhida;
    atualizarStatus(`Cidade alterada para ${escolhida}.`);
  } else {
    atualizarStatus("Clima consultado.");
  }
}

// ------------------------------------------------------------------ ligação

el("btn-cadastrar").addEventListener("click", cadastrar);
el("btn-atualizar").addEventListener("click", atualizar);
el("btn-limpar").addEventListener("click", () => limpar(false));
el("btn-editar").addEventListener("click", carregarNoFormulario);
el("btn-deletar").addEventListener("click", deletar);
el("btn-recarregar").addEventListener("click", recarregar);
el("btn-estatisticas").addEventListener("click", consultarEstatisticas);
el("btn-clima").addEventListener("click", consultarClima);

["lado", "ruas", "dose"].forEach((id) => el(id).addEventListener("input", atualizarPrevia));
document.querySelectorAll('input[name="cultura"]').forEach((radio) => {
  radio.addEventListener("change", atualizarPrevia);
});

(async function iniciar() {
  desenharTalhao(0, 0);
  atualizarPrevia();
  try {
    await carregarDoRepositorio();
    preencherTabela();
    atualizarStatus("Dados lidos de dados_agricultura.csv.");
  } catch (erro) {
    atualizarStatus(`Não foi possível ler o CSV: ${erro.message}`);
  }
})();
