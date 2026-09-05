# FarmTech Solutions - Clima
# Consulta a API pública Open-Meteo (não exige chave) e mostra as condições
# meteorológicas da região do talhão diretamente no terminal.
#
# Uso:
#   Rscript r/clima.R              -> usa o local padrão do projeto
#   Rscript r/clima.R Rio Verde    -> busca as coordenadas da cidade informada
#
# Pacote necessário: jsonlite
# Instale com: install.packages("jsonlite")

# ---------------------------------------------------------------
# LOCALIZAÇÃO PADRÃO DO PROJETO
# Sorriso - MT, um dos maiores polos de soja e milho do Brasil.
# ---------------------------------------------------------------
LOCAL_PADRAO <- "Sorriso - MT (Brasil)"
LATITUDE_PADRAO <- -12.5453
LONGITUDE_PADRAO <- -55.7113
FUSO <- "America/Sao_Paulo"
DIAS_PREVISAO <- 2


if (!requireNamespace("jsonlite", quietly = TRUE)) {
  cat("\nO pacote 'jsonlite' não está instalado e é necessário para ler o JSON.\n")
  cat("Instale com o comando abaixo dentro do R e rode este script de novo:\n\n")
  cat('  install.packages("jsonlite")\n\n')
  quit(status = 1)
}

linha <- function(caractere = "-") {
  cat("\n", strrep(caractere, 40), "\n", sep = "")
}

# Busca latitude e longitude pelo nome da cidade na API de geocodificação
# da própria Open-Meteo, que também é gratuita e não exige chave.
buscar_cidade <- function(cidade) {
  url_busca <- paste0(
    "https://geocoding-api.open-meteo.com/v1/search",
    "?name=", URLencode(cidade, reserved = TRUE),
    "&count=1&language=pt&country=BR"
  )

  resposta <- tryCatch(
    suppressWarnings(jsonlite::fromJSON(url_busca)),
    error = function(e) NULL
  )

  if (is.null(resposta) || is.null(resposta$results) || nrow(resposta$results) == 0) {
    return(NULL)
  }

  encontrada <- resposta$results[1, ]
  estado <- if (is.null(encontrada$admin1)) "Brasil" else encontrada$admin1

  list(
    nome = paste0(encontrada$name, " - ", estado, " (Brasil)"),
    latitude = encontrada$latitude,
    longitude = encontrada$longitude
  )
}


# ---------------------------------------------------------------
# LOCAL A CONSULTAR: o informado na linha de comando ou o padrão
# ---------------------------------------------------------------
cidade_pedida <- paste(commandArgs(trailingOnly = TRUE), collapse = " ")

if (nzchar(cidade_pedida)) {
  cat("\nProcurando as coordenadas de \"", cidade_pedida, "\"...\n", sep = "")
  local <- buscar_cidade(cidade_pedida)

  if (is.null(local)) {
    cat("\nNão encontrei nenhuma cidade brasileira com esse nome.\n")
    cat("Confira a grafia e tente de novo (exemplo: Rio Verde).\n\n")
    quit(status = 1)
  }
} else {
  local <- list(
    nome = LOCAL_PADRAO,
    latitude = LATITUDE_PADRAO,
    longitude = LONGITUDE_PADRAO
  )
}

# Mostra o valor com a unidade, avisando quando a API não trouxe o dado.
medida <- function(rotulo, valor, unidade, casas = 1) {
  if (is.null(valor) || length(valor) == 0 || is.na(valor)) {
    cat(rotulo, ": não informado pela API\n", sep = "")
  } else {
    cat(rotulo, ": ", sprintf(paste0("%.", casas, "f"), valor), " ", unidade, "\n", sep = "")
  }
}


# ---------------------------------------------------------------
# 1) REQUISIÇÃO HTTP
# ---------------------------------------------------------------
url <- paste0(
  "https://api.open-meteo.com/v1/forecast",
  "?latitude=", local$latitude,
  "&longitude=", local$longitude,
  "&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
  "&hourly=temperature_2m,relative_humidity_2m,precipitation",
  "&forecast_days=", DIAS_PREVISAO,
  "&timezone=", FUSO
)

options(timeout = 20)

cat("\nConsultando a Open-Meteo...\n")

# 2) RESPOSTA EM JSON. Erro de rede ou JSON inválido cai no tryCatch.
resposta <- tryCatch(
  # O suppressWarnings evita o aviso técnico do R repetindo o erro na tela.
  suppressWarnings(jsonlite::fromJSON(url)),
  error = function(e) {
    cat("\nNão foi possível obter os dados meteorológicos.\n")
    cat("Motivo:", conditionMessage(e), "\n")
    cat("Verifique sua conexão com a internet e tente novamente.\n\n")
    quit(status = 1)
  }
)


# ---------------------------------------------------------------
# 3) PROCESSAMENTO DOS DADOS
# ---------------------------------------------------------------
atual <- resposta$current
previsao <- resposta$hourly

if (is.null(atual) || is.null(previsao$temperature_2m)) {
  cat("\nA resposta da API veio em um formato inesperado.\n")
  cat("Os dados de clima não puderam ser lidos.\n\n")
  quit(status = 1)
}

temperaturas <- as.numeric(previsao$temperature_2m)
chuva_prevista <- as.numeric(previsao$precipitation)

# 4) INFORMAÇÕES CALCULADAS E EXIBIDAS
linha("=")
cat("CLIMA - FARMTECH SOLUTIONS\n")
cat("\nLocal: ", local$nome, "\n", sep = "")
cat("Latitude: ", local$latitude, " | Longitude: ", local$longitude, "\n", sep = "")
# A API devolve a data no formato 2026-09-04T13:30; o "T" só atrapalha a leitura.
cat("Medição: ", sub("T", " às ", atual$time), " (", FUSO, ")\n", sep = "")

linha()
cat("\nCONDIÇÕES ATUAIS\n\n")
medida("Temperatura", atual$temperature_2m, "°C")
medida("Umidade relativa", atual$relative_humidity_2m, "%", casas = 0)
medida("Precipitação", atual$precipitation, "mm")
medida("Velocidade do vento", atual$wind_speed_10m, "km/h")

linha()
cat("\nTEMPERATURA PREVISTA PARA ", DIAS_PREVISAO * 24, " HORAS\n\n", sep = "")
medida("Média", mean(temperaturas, na.rm = TRUE), "°C")
medida("Máxima", max(temperaturas, na.rm = TRUE), "°C")
medida("Mínima", min(temperaturas, na.rm = TRUE), "°C")
cat("Horas coletadas: ", sum(!is.na(temperaturas)), "\n", sep = "")

linha()
cat("\nCHUVA PREVISTA NO PERÍODO\n\n")
medida("Total acumulado", sum(chuva_prevista, na.rm = TRUE), "mm")

linha("=")
cat("\n")
