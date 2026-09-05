# FarmTech Solutions - Estatísticas
# Lê o CSV gerado pela aplicação Python e mostra média e desvio padrão no terminal.

# Descobre a pasta do projeto a partir do próprio script, para não depender
# de caminho absoluto nem da pasta em que o R foi executado.
argumentos <- commandArgs(trailingOnly = FALSE)
caminho_script <- sub("^--file=", "", argumentos[grep("^--file=", argumentos)])

if (length(caminho_script) > 0) {
  pasta_projeto <- dirname(dirname(normalizePath(caminho_script)))
} else {
  pasta_projeto <- getwd()
}

caminho_csv <- file.path(pasta_projeto, "dados", "dados_agricultura.csv")


# Mostra o valor com 2 casas decimais. O desvio padrão de um único registro
# é NA no R, então nesse caso explicamos o motivo em vez de imprimir "NA".
formatar <- function(valor, unidade) {
  if (is.na(valor)) {
    return("indisponível (é preciso pelo menos 2 registros)")
  }
  paste(sprintf("%.2f", valor), unidade)
}

mostrar_bloco <- function(titulo, valores, unidade) {
  cat("\n", strrep("-", 40), "\n\n", sep = "")
  cat(titulo, "\n\n", sep = "")
  cat("Média: ", formatar(mean(valores), unidade), "\n", sep = "")
  cat("Desvio padrão: ", formatar(sd(valores), unidade), "\n", sep = "")
}


if (!file.exists(caminho_csv)) {
  cat("\nArquivo não encontrado:", caminho_csv, "\n")
  cat("Os dados ainda não foram gerados. Execute antes o programa em Python\n")
  cat("(python/farmtech.py) e cadastre pelo menos um talhão.\n\n")
  quit(status = 0)
}

dados <- tryCatch(
  read.csv(caminho_csv, fileEncoding = "UTF-8"),
  error = function(e) {
    cat("\nNão foi possível ler o CSV:", conditionMessage(e), "\n\n")
    quit(status = 1)
  }
)

if (nrow(dados) == 0) {
  cat("\nO arquivo existe, mas não possui registros.\n")
  cat("Cadastre talhões no programa em Python para gerar os dados.\n\n")
  quit(status = 0)
}

# Garante que as colunas usadas nas contas sejam numéricas.
area <- as.numeric(dados$area)
dose <- as.numeric(dados$dose)
insumo <- as.numeric(dados$total_insumo_litros)

if (anyNA(area) || anyNA(dose) || anyNA(insumo)) {
  cat("\nO CSV possui valores não numéricos nas colunas de cálculo.\n")
  cat("Gere o arquivo novamente pelo programa em Python.\n\n")
  quit(status = 1)
}

cat("\n", strrep("=", 40), "\n", sep = "")
cat("ESTATÍSTICAS FARMTECH\n")
cat("\nQuantidade de registros: ", nrow(dados), "\n", sep = "")

mostrar_bloco("ÁREA DOS TALHÕES", area, "m²")
mostrar_bloco("DOSE DOS INSUMOS", dose, "mL/m")
mostrar_bloco("QUANTIDADE DE INSUMO", insumo, "L")

cat("\n", strrep("=", 40), "\n\n", sep = "")
