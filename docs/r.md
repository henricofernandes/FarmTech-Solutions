# Aplicações em R

Dois scripts independentes, ambos de terminal e sem interface gráfica.

---

# `r/estatisticas.R`

Lê `dados/dados_agricultura.csv` e calcula média e desvio padrão dos talhões
cadastrados. Usa apenas funções básicas do R (`read.csv`, `mean`, `sd`, `nrow`), sem
nenhum pacote externo.

## Execução e saída

```powershell
Rscript r/estatisticas.R
```

```
========================================
ESTATÍSTICAS FARMTECH

Quantidade de registros: 3

----------------------------------------

ÁREA DOS TALHÕES

Média: 15633.33 m²
Desvio padrão: 6340.61 m²
```

Os mesmos blocos se repetem para a dose dos insumos (mL/m) e para a quantidade total de
insumo (L). As colunas usadas nas contas são convertidas com `as.numeric()` antes do
cálculo.

## Validações

| Situação | Comportamento |
|---|---|
| CSV não existe | avisa que os dados ainda não foram gerados pelo Python |
| CSV só com cabeçalho | informa que não há registros suficientes |
| Valores não numéricos | pede para gerar o arquivo novamente pelo Python |
| Apenas 1 registro | mostra a média e explica que o desvio padrão precisa de 2 registros |

O último caso merece atenção: o `sd()` do R devolve `NA` com um único valor, o que
apareceria na tela como "Desvio padrão: NA" e pareceria um defeito. O script troca isso
por uma frase explicando o motivo.

---

# `r/clima.R`

Consulta a **Open-Meteo**, uma API meteorológica pública que não exige chave de acesso,
e mostra as condições da região do talhão. Requisito do "ir além": toda a comunicação
com a API é feita em R, sem participação do Python.

## Pacote necessário

Apenas `jsonlite`, para converter a resposta JSON em estrutura do R:

```r
install.packages("jsonlite")
```

A requisição HTTP usa o suporte a `libcurl` que já vem embutido no R. O script verifica
se o pacote está instalado e, se não estiver, mostra o comando acima em vez de falhar
com um erro técnico.

## Execução

```powershell
Rscript r/clima.R              # local padrão: Sorriso - MT
Rscript r/clima.R Rio Verde    # qualquer cidade brasileira
```

Sorriso - MT foi escolhida como padrão por ser um dos maiores polos de soja e milho do
país. A latitude e a longitude ficam em constantes no topo do arquivo.

Quando você informa uma cidade, o script primeiro busca as coordenadas dela na API de
geocodificação da própria Open-Meteo, também gratuita. Assim não é preciso procurar
latitude e longitude manualmente.

## O que é exibido

Condições atuais (temperatura, umidade relativa, precipitação e velocidade do vento) e,
a partir da série horária das próximas 48 horas, a média, a máxima e a mínima da
temperatura mais o total de chuva prevista — a informação mais útil para decidir uma
aplicação de insumo.

## Tratamento de erros

Se a API não responder, o script explica que não conseguiu obter os dados e sugere
verificar a conexão. Se a resposta vier em formato inesperado, avisa em vez de calcular
em cima de dados vazios. Se a cidade não for encontrada, pede para conferir a grafia.
Em todos os casos encerra com mensagem em português, sem despejar erro do R na tela.
